# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Compare live inputs and scores with what the model was trained on.

For each column it reports the population stability index (PSI) against the
reference, the change in missing rate, the share of live values outside the
reference range and the share of categories the reference never had. With
--by, it does the same for each segment (platform, app version, country), which
is where pipeline and client bugs show; with --time, for each period, which
dates the change.

    uv run drift.py training_sample.csv live.csv --by platform app_version --time ts --freq D

The largest shifts come first. A shift is a question (a release, a unit change,
a holiday, a new campaign), not a verdict that the model needs retraining.
"""

# %%
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Conventional PSI bands from credit scoring: under 0.1 stable, 0.1 to 0.25
# worth a look, above 0.25 a shift that changes what the model sees.
PSI_WATCH = 0.10
PSI_SHIFT = 0.25
# Bins are reference deciles, so each holds a tenth of the reference rows.
BINS = 10
# Shares of the reference distribution outside which a value counts as out of range.
RANGE_Q = (0.005, 0.995)
# Changes in missing rate, out-of-range share and unseen-category share above
# these are reported as shifts even when PSI stays low.
MISSING_JUMP = 0.05
OUT_OF_RANGE = 0.05
UNSEEN = 0.02
# Segments or periods smaller than this give PSI values too noisy to read.
MIN_ROWS = 200
EPS = 1e-4


# %%
def read_table(path: str) -> pd.DataFrame:
    p = Path(path)
    return pd.read_parquet(p) if p.suffix in {".parquet", ".pq"} else pd.read_csv(p)


def psi(ref_share: np.ndarray, cur_share: np.ndarray) -> float:
    r = np.clip(ref_share, EPS, None)
    c = np.clip(cur_share, EPS, None)
    return float(((c - r) * np.log(c / r)).sum())


def numeric_profile(ref: pd.Series, cur: pd.Series) -> dict:
    r, c = ref.dropna().astype(float), cur.dropna().astype(float)
    edges = np.unique(np.quantile(r, np.linspace(0, 1, BINS + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    rs = np.histogram(r, edges)[0] / max(len(r), 1)
    cs = np.histogram(c, edges)[0] / max(len(c), 1)
    lo, hi = np.quantile(r, RANGE_Q)
    return dict(psi=psi(rs, cs), missing_ref=ref.isna().mean(), missing_cur=cur.isna().mean(),
                out_of_range=float(((c < lo) | (c > hi)).mean()) if len(c) else float("nan"), unseen=0.0,
                ref_median=float(r.median()) if len(r) else float("nan"),
                cur_median=float(c.median()) if len(c) else float("nan"))


def category_profile(ref: pd.Series, cur: pd.Series) -> dict:
    r, c = ref.astype("string").fillna("<missing>"), cur.astype("string").fillna("<missing>")
    cats = sorted(set(r.unique()) | set(c.unique()))
    rs = r.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    cs = c.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    unseen = float((~c.isin(set(r.unique()))).mean())
    top_cur = c.value_counts(normalize=True).head(1)
    return dict(psi=psi(rs, cs), missing_ref=ref.isna().mean(), missing_cur=cur.isna().mean(), out_of_range=0.0,
                unseen=unseen, ref_median=float("nan"), cur_median=float("nan"),
                top=f"{top_cur.index[0]} ({top_cur.iloc[0]:.0%})" if len(top_cur) else "")


def profile(ref: pd.DataFrame, cur: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for col in cols:
        numeric = pd.api.types.is_numeric_dtype(ref[col]) and ref[col].nunique() > 12
        p = numeric_profile(ref[col], cur[col]) if numeric else category_profile(ref[col], cur[col])
        rows.append(dict(column=col, **p))
    return pd.DataFrame(rows)


def judge(row) -> str:
    notes = []
    if row["psi"] >= PSI_SHIFT:
        notes.append("shift")
    elif row["psi"] >= PSI_WATCH:
        notes.append("watch")
    if abs(row["missing_cur"] - row["missing_ref"]) >= MISSING_JUMP:
        notes.append("missing rate moved")
    if row["out_of_range"] >= OUT_OF_RANGE:
        notes.append("out of range")
    if row["unseen"] >= UNSEEN:
        notes.append("unseen categories")
    return ", ".join(notes)


# %%
def fmt_table(df: pd.DataFrame) -> str:
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return "" if v != v else f"{v:,.3g}"
        return str(v)
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns)
    return head + "\n" + "\n".join("| " + " | ".join(cell(v) for v in r) + " |" for r in df.itertuples(index=False))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference", help="what the model was trained or validated on")
    ap.add_argument("current", help="live rows to compare")
    ap.add_argument("--columns", nargs="+", help="columns to compare; default: every column in both files")
    ap.add_argument("--by", nargs="+", default=[], help="segment columns, such as platform or app_version")
    ap.add_argument("--time", help="time column in the live file")
    ap.add_argument("--freq", default="D", help="period for --time: D, W or M")
    ap.add_argument("--top", type=int, default=15, help="rows to show in the segment and period tables")
    args = ap.parse_args(argv)

    ref, cur = read_table(args.reference), read_table(args.current)
    skip = set(args.by) | {args.time}
    cols = args.columns or [c for c in ref.columns if c in cur.columns and c not in skip]
    out = [f"# Drift\n\nReference: {len(ref)} rows. Live: {len(cur)} rows. "
           f"PSI under {PSI_WATCH} is stable, {PSI_WATCH} to {PSI_SHIFT} worth a look, above {PSI_SHIFT} a shift.\n"]

    overall = profile(ref, cur, cols)
    overall["finding"] = overall.apply(judge, axis=1)
    overall = overall.sort_values("psi", ascending=False)
    shown = overall.drop(columns=[c for c in ["top"] if c in overall.columns and overall[c].isna().all()])
    out.append("## All live rows against the reference\n\n" + fmt_table(shown))

    if args.by:
        rows = []
        seg_cols = [c for c in cols if c not in args.by]  # a segment column always shifts within its own segments
        for col in args.by:
            for v, part in cur.groupby(col, dropna=False):
                if len(part) < MIN_ROWS:
                    continue
                p = profile(ref, part, seg_cols)
                p.insert(0, "segment", f"{col}={v}")
                p.insert(1, "rows", len(part))
                rows.append(p)
        if rows:
            seg = pd.concat(rows)
            seg["finding"] = seg.apply(judge, axis=1)
            seg = seg[seg["finding"] != ""].sort_values("psi", ascending=False).head(args.top)
            keep = ["segment", "rows", "column", "psi", "missing_ref", "missing_cur", "out_of_range", "unseen",
                    "ref_median", "cur_median", "finding"]
            out.append("\n## Segments with a shift, largest first\n\n" + (fmt_table(seg[keep]) if len(seg) else "None."))

    if args.time:
        t = pd.to_datetime(cur[args.time], errors="coerce")
        period = t.dt.to_period(args.freq).astype(str)
        rows = []
        for v, part in cur.groupby(period):
            if len(part) < MIN_ROWS:
                continue
            p = profile(ref, part, cols)
            rows.append(p.assign(period=v)[["period", "column", "psi"]])
        if rows:
            per = pd.concat(rows).pivot(index="period", columns="column", values="psi")
            moved = [c for c in per.columns if per[c].max() >= PSI_WATCH]
            out.append("\n## PSI by period, columns that moved\n")
            if moved:
                out.append(fmt_table(per[moved].reset_index()))
                first = {c: per.index[per[c] >= PSI_WATCH][0] for c in moved}
                out.append("\nFirst period at or above " + str(PSI_WATCH) + ": "
                           + "; ".join(f"`{c}` {p}" for c, p in sorted(first.items(), key=lambda kv: kv[1])) + ".")
            else:
                out.append("No column reaches " + str(PSI_WATCH) + " in any period.")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
