# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Screen a training table for features that leak the label.

For each feature it reports how well the feature alone separates the label,
overall and per period, and whether it goes missing for one class more than
the other. It also checks splits for overlapping time ranges, entities on both
sides and duplicated rows. Every flag is a question to answer from the
feature's source and timestamp, not proof of a leak.

    uv run leakage_screen.py data.csv --label churned --time snapshot_month
    uv run leakage_screen.py data.parquet --label clicked --split split --id user_id

Prints a Markdown report. Exits 0 when nothing is flagged and 1 otherwise.
"""

# %%
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# One behavioural feature rarely separates the classes this well on its own;
# most leaks (backfills, post-outcome fields, the label in a window) land above it.
TOO_STRONG_AUC = 0.90
# The same bar for a numeric label, as an absolute rank correlation.
TOO_STRONG_RHO = 0.80
# A single-feature AUC that moves this much between stretches of time, and by more
# than three standard errors, means the feature was produced differently in some
# stretches (a backfill, a redefinition).
PERIOD_SPREAD = 0.15
PERIOD_Z = 3.0
# Time is cut into this many consecutive stretches of equal row count, fewer when
# positives are scarce, so that each stretch's AUC is stable enough to compare.
TIME_CHUNKS = 4
MIN_POSITIVES_PER_CHUNK = 100
# A feature missing far more often for one class was often filled in after the outcome.
MISSING_GAP = 0.30
# Columns with nearly one value per row behave like identifiers.
ID_UNIQUE_RATIO = 0.90
# Fewer positives or negatives than this in a period gives an AUC too noisy to compare.
MIN_CLASS = 30


# %%
def read_table(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix in {".parquet", ".pq"}:
        return pd.read_parquet(p)
    return pd.read_csv(p, keep_default_na=True, na_values=[""])


def auc(score: pd.Series, y: pd.Series) -> float:
    """Rank AUC of a score against a 0/1 label, folded so 0.5 means no signal."""
    mask = score.notna()
    s, t = score[mask], y[mask]
    pos, neg = int(t.sum()), int((1 - t).sum())
    if pos == 0 or neg == 0:
        return float("nan")
    ranks = s.rank(method="average")
    a = (ranks[t == 1].sum() - pos * (pos + 1) / 2) / (pos * neg)
    return float(max(a, 1 - a))


def auc_se(a: float, pos: int, neg: int) -> float:
    """Hanley and McNeil (1982) standard error of an AUC."""
    q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
    return float(np.sqrt((a * (1 - a) + (pos - 1) * (q1 - a * a) + (neg - 1) * (q2 - a * a)) / (pos * neg)))


def spearman(x: pd.Series, y: pd.Series) -> float:
    mask = x.notna() & y.notna()
    if mask.sum() < 3:
        return float("nan")
    return float(abs(x[mask].rank().corr(y[mask].rank())))


def encode(col: pd.Series, y: pd.Series, folds: np.ndarray) -> pd.Series:
    """Numeric columns pass through; others get out-of-fold label means, so a
    category cannot score well by memorizing its own rows."""
    if pd.api.types.is_bool_dtype(col):
        return col.astype(float)
    if pd.api.types.is_numeric_dtype(col):
        return col.astype(float)
    col = col.astype("string").fillna("<missing>")
    out = pd.Series(np.nan, index=col.index)
    prior = float(y.mean())
    for f in np.unique(folds):
        train, test = folds != f, folds == f
        means = y[train].groupby(col[train]).mean()
        out[test] = col[test].map(means).astype(float).fillna(prior).to_numpy()
    return out


def strength(x: pd.Series, y: pd.Series, binary: bool) -> float:
    return auc(x, y) if binary else spearman(x, y)


# %%
def screen(df: pd.DataFrame, label: str, time: str | None = None, id_col: str | None = None,
           split: str | None = None, drop: list[str] | None = None) -> dict:
    drop = set(drop or [])
    y_raw = df[label]
    values = y_raw.dropna().unique()
    binary = len(values) == 2
    if binary:
        positive = 1 if set(values) <= {0, 1} else sorted(values)[-1]
        y = (y_raw == positive).astype(int)
    elif pd.api.types.is_numeric_dtype(y_raw):
        y = y_raw.astype(float)
    else:
        raise SystemExit(f"--label {label} has {len(values)} values and is not numeric; screen one class at a time.")

    rng = np.random.default_rng(0)
    if time:
        order = pd.to_datetime(df[time], errors="coerce") if not pd.api.types.is_numeric_dtype(df[time]) else df[time]
        folds = (order.rank(method="first") > len(df) / 2).to_numpy().astype(int)
    else:
        folds = rng.integers(0, 2, len(df))

    chunks = None
    if time and binary:
        order = df[time] if pd.api.types.is_numeric_dtype(df[time]) else pd.to_datetime(df[time], errors="coerce")
        k = int(min(TIME_CHUNKS, max(2, y.sum() // MIN_POSITIVES_PER_CHUNK)))
        idx = pd.Series(np.minimum((order.rank(method="first") - 1) * k // len(df), k - 1).astype(int), index=df.index)
        names = {i: f"{df.loc[idx == i, time].min()} to {df.loc[idx == i, time].max()}" for i in range(k)}
        chunks = idx.map(names)

    skip = {label, time, id_col, split} | drop
    rows, flags = [], []
    for c in [c for c in df.columns if c not in skip]:
        col = df[c]
        unique_ratio = col.nunique(dropna=True) / max(col.notna().sum(), 1)
        x = encode(col, y, folds)
        s = strength(x, y, binary)
        miss_gap = float("nan")
        if binary:
            miss_gap = abs(col[y == 1].isna().mean() - col[y == 0].isna().mean())
        by_period, se = {}, {}
        if chunks is not None:
            for p, rows_in in chunks.groupby(chunks, sort=False).groups.items():
                yy, xx = y.loc[rows_in], x.loc[rows_in]
                pos, neg = int(yy[xx.notna()].sum()), int((1 - yy[xx.notna()]).sum())
                if pos >= MIN_CLASS and neg >= MIN_CLASS:
                    by_period[p] = auc(xx, yy)
                    se[p] = auc_se(by_period[p], pos, neg)
        spread, z = float("nan"), 0.0
        if len(by_period) >= 2:
            lo, hi = min(by_period, key=by_period.get), max(by_period, key=by_period.get)
            spread = by_period[hi] - by_period[lo]
            z = spread / np.sqrt(se[hi] ** 2 + se[lo] ** 2)
        row = dict(feature=c, kind="numeric" if pd.api.types.is_numeric_dtype(col) else "category",
                   strength=s, missing=col.isna().mean(), missing_gap=miss_gap, period_spread=spread,
                   by_period=by_period, unique_ratio=unique_ratio)
        rows.append(row)
        bar = TOO_STRONG_AUC if binary else TOO_STRONG_RHO
        if s == s and s >= bar:
            flags.append(f"`{c}` alone scores {s:.3f} ({'AUC' if binary else '|rho|'}); find when its value is written relative to the prediction time.")
        if spread == spread and spread >= PERIOD_SPREAD and z >= PERIOD_Z:
            flags.append(f"`{c}` scores {by_period[hi]:.3f} from {hi} but {by_period[lo]:.3f} from {lo}; it was produced differently over time (backfill, redefinition) or leaks only in part of the data.")
        if miss_gap == miss_gap and miss_gap >= MISSING_GAP:
            flags.append(f"`{c}` is missing for {col[y == 1].isna().mean():.0%} of positives and {col[y == 0].isna().mean():.0%} of negatives; check whether it is filled in after the outcome.")
        if unique_ratio >= ID_UNIQUE_RATIO and s == s and s >= 0.7 and not pd.api.types.is_float_dtype(col):
            flags.append(f"`{c}` looks like an identifier and still scores {s:.3f}; identifiers that predict usually encode time or the outcome.")

    split_notes = []
    if split:
        groups = df.groupby(split)
        if time:
            t = pd.to_datetime(df[time], errors="coerce") if not pd.api.types.is_numeric_dtype(df[time]) else df[time]
            ranges = t.groupby(df[split]).agg(["min", "max"])
            split_notes.append("| Split | Rows | From | To |\n|---|---|---|---|\n" + "\n".join(
                f"| {k} | {len(groups.get_group(k))} | {r['min']} | {r['max']} |" for k, r in ranges.iterrows()))
            ordered = ranges.sort_values("min")
            for (a, ra), (b, rb) in zip(ordered.iterrows(), list(ordered.iterrows())[1:]):
                if rb["min"] <= ra["max"]:
                    flags.append(f"Splits `{a}` and `{b}` overlap in time ({rb['min']} to {ra['max']}); a model can learn from the period it is tested on.")
        if id_col:
            seen = df.groupby(id_col)[split].nunique()
            shared = int((seen > 1).sum())
            if shared:
                flags.append(f"{shared} of {len(seen)} `{id_col}` values appear in more than one split. Fine for a time split when the product scores known entities again; a leak when it mostly scores new ones.")
        feats = [c for c in df.columns if c not in skip]
        dup = df[feats].astype("string").agg("|".join, axis=1)
        across = dup.groupby(dup).apply(lambda s: df.loc[s.index, split].nunique() > 1)
        n_dup = int(across.sum())
        if n_dup:
            flags.append(f"{n_dup} distinct feature rows appear in more than one split; duplicates let a model be tested on rows it trained on.")

    stretches = list(dict.fromkeys(chunks.sort_index().tolist())) if chunks is not None else []
    return dict(rows=rows, flags=flags, split_notes=split_notes, binary=binary, n=len(df), stretches=stretches,
                positives=int(y.sum()) if binary else None)


# %%
def report(result: dict) -> str:
    binary = result["binary"]
    head = f"# Leak screen\n\n{result['n']} rows"
    if binary:
        head += f", {result['positives']} positives ({result['positives'] / result['n']:.1%})"
    lines = [head + ".\n", "## Flags\n"]
    lines += [f"- {f}" for f in result["flags"]] or ["- None."]
    lines.append("\n## Features, strongest first\n")
    metric = "AUC alone" if binary else "|rho| alone"
    lines.append(f"| Feature | Kind | {metric} | Missing | Missing gap by class | {metric}, by stretch of time |")
    lines.append("|---|---|---|---|---|---|")
    for r in sorted(result["rows"], key=lambda r: -(r["strength"] if r["strength"] == r["strength"] else 0)):
        fmt = lambda v, p=3: "" if v != v else f"{v:.{p}f}"
        stretches = " / ".join(f"{v:.2f}" for v in r["by_period"].values())
        lines.append(f"| {r['feature']} | {r['kind']} | {fmt(r['strength'])} | {r['missing']:.1%} | {fmt(r['missing_gap'], 2)} | {stretches} |")
    if result["stretches"]:
        lines.append("\nStretches of time, in order: " + "; ".join(result["stretches"]) + ".")
    if result["split_notes"]:
        lines.append("\n## Splits\n")
        lines += result["split_notes"]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", help="CSV or Parquet file, one row per prediction")
    ap.add_argument("--label", required=True, help="the target column")
    ap.add_argument("--time", help="prediction-time column, for strength over time and split ranges")
    ap.add_argument("--id", dest="id_col", help="entity column, for overlap between splits")
    ap.add_argument("--split", help="column naming each row's split (train, valid, test)")
    ap.add_argument("--drop", nargs="*", default=[], help="columns to leave out of the screen")
    args = ap.parse_args(argv)
    df = read_table(args.data)
    for c in [args.label, args.time, args.id_col, args.split, *args.drop]:
        if c and c not in df.columns:
            raise SystemExit(f"Column {c!r} not in {args.data}. Columns: {', '.join(df.columns)}")
    result = screen(df, args.label, args.time, args.id_col, args.split, args.drop)
    print(report(result))
    return 1 if result["flags"] else 0


if __name__ == "__main__":
    sys.exit(main())
