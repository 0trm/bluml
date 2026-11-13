# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Compare a model with a baseline on every slice, with paired intervals.

Each row needs the model's decision and the baseline's decision (0/1 columns,
or a score with a threshold), or for a regression the two predictions. For the
whole table and each slice, the script reports the metric for both, the
difference, and a 95% bootstrap interval of the difference that resamples the
same rows for both, so slices where the model loses, and slices too small to
judge, stand out.

    uv run slices.py scored.csv --label fraudulent --decision model_flag --baseline rule_flag \\
        --by channel region --metric cost --cost-act 40 --cost-fn-col claim_amount
    uv run slices.py scored.csv --label clicked --score p --threshold 0.2 --baseline rule_flag --by platform --metric recall
    uv run slices.py eta.csv --label minutes --pred model_eta --baseline-pred rule_eta --by city --metric pinball:0.8

Metrics: cost (lower is better; set the costs as in threshold.py), precision,
recall, fpr (false positive rate), accuracy and flag_rate for decisions; mae, rmse and pinball:<q> for
predictions (lower is better). Rows with an empty label, decision, prediction or
cost are left out, and counted.
"""

# %%
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Below this many positives (or rows, for regression) a slice's metric swings by
# chance more than most real differences; the slice is reported but not judged.
MIN_POSITIVES = 30
MIN_ROWS = 100
BOOTSTRAP = 1000
# Resamples are drawn as one matrix of row indices, in batches of at most this many cells.
BATCH_CELLS = 2_000_000
LOWER_IS_BETTER = {"cost", "mae", "rmse", "pinball", "flag_rate", "fpr"}


# %%
def read_table(path: str) -> pd.DataFrame:
    p = Path(path)
    return pd.read_parquet(p) if p.suffix in {".parquet", ".pq"} else pd.read_csv(p)


def ratio(num, den):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, num / den, np.nan)


def metric_fn(name: str, y, cost_act=0.0, cost_fp=0.0, fn=None):
    """Return f(pred, idx) -> metric on the rows idx. idx is one set of rows, giving a
    number, or a matrix with one bootstrap resample per row, giving one number per resample."""
    def on_rows(g):
        def f(p, idx):
            out = g(p[idx], y[idx], idx)
            return float(out) if np.ndim(out) == 0 else out
        return f
    if name == "cost":
        return on_rows(lambda a, t, idx: (a * cost_act + a * (1 - t) * cost_fp + (1 - a) * t * fn[idx]).mean(-1) * 1000)
    if name == "precision":
        return on_rows(lambda a, t, _: ratio((a * t).sum(-1), a.sum(-1)))
    if name == "recall":
        return on_rows(lambda a, t, _: ratio((a * t).sum(-1), t.sum(-1)))
    if name == "fpr":
        return on_rows(lambda a, t, _: ratio((a * (1 - t)).sum(-1), (1 - t).sum(-1)))
    if name == "accuracy":
        return on_rows(lambda a, t, _: (a == t).mean(-1))
    if name == "flag_rate":
        return on_rows(lambda a, t, _: a.mean(-1))
    if name == "mae":
        return on_rows(lambda p, t, _: np.abs(t - p).mean(-1))
    if name == "rmse":
        return on_rows(lambda p, t, _: np.sqrt(((t - p) ** 2).mean(-1)))
    if name.startswith("pinball"):
        q = float(name.split(":")[1]) if ":" in name else 0.5
        return on_rows(lambda p, t, _: np.maximum(q * (t - p), (q - 1) * (t - p)).mean(-1))
    raise SystemExit(f"Unknown metric {name}")


def compare(model, base, idx, f, rng, b=BOOTSTRAP):
    m, k = f(model, idx), f(base, idx)
    n = len(idx)
    step = max(1, BATCH_CELLS // n)
    diffs = []
    for start in range(0, b, step):
        s = idx[rng.integers(0, n, (min(step, b - start), n))]
        diffs.append(f(model, s) - f(base, s))
    lo, hi = np.nanpercentile(np.concatenate(diffs), [2.5, 97.5])
    return m, k, m - k, lo, hi


def slice_table(df: pd.DataFrame, label: str, model: np.ndarray, base: np.ndarray, by: list[str], metric: str,
                cost_act=0.0, cost_fp=0.0, fn=None, regression=False, boot=BOOTSTRAP, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    y = df[label].to_numpy(dtype=float)
    if np.isnan(y).any():
        raise ValueError(f"{int(np.isnan(y).sum())} rows have no {label}; leave them out first, as main() does.")
    f = metric_fn(metric, y, cost_act, cost_fp, fn)
    lower = metric.split(":")[0] in LOWER_IS_BETTER
    groups = [("all", "all", np.arange(len(df)))]
    for col in by:
        for v, rows in df.groupby(col, dropna=False).indices.items():
            groups.append((col, v, np.asarray(rows)))
    out = []
    for col, v, idx in groups:
        m, k, d, lo, hi = compare(model, base, idx, f, rng, boot)
        small = len(idx) < MIN_ROWS if regression else y[idx].sum() < MIN_POSITIVES
        worse = (lo > 0) if lower else (hi < 0)
        better = (hi < 0) if lower else (lo > 0)
        verdict = "too small to judge" if small else "model worse" if worse else "model better" if better else "no clear difference"
        out.append(dict(slice=col, value=v, rows=len(idx), positives=None if regression else int(y[idx].sum()),
                        model=m, baseline=k, difference=d, ci_low=lo, ci_high=hi, verdict=verdict))
    t = pd.DataFrame(out)
    return t.drop(columns="positives") if regression else t


def drop_empty(df: pd.DataFrame, cols: list) -> tuple[pd.DataFrame, str]:
    """Leave out rows with an empty value in any column the run uses, and say how many."""
    cols = list(dict.fromkeys(c for c in cols if c))
    empty = df[cols].isna()
    keep = ~empty.any(axis=1)
    if keep.all():
        return df.reset_index(drop=True), ""
    per_col = ", ".join(f"`{c}` {int(n)}" for c, n in empty.sum().items() if n)
    return df[keep].reset_index(drop=True), f"Left out {int((~keep).sum())} rows with an empty value ({per_col})."


def fmt_table(df: pd.DataFrame) -> str:
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return "" if v != v else f"{v:,.4g}"
        return str(v)
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns)
    return head + "\n" + "\n".join("| " + " | ".join(cell(v) for v in r) + " |" for r in df.itertuples(index=False))


# %%
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("--label", required=True)
    ap.add_argument("--by", nargs="+", required=True, help="slice columns")
    ap.add_argument("--metric", default="cost")
    ap.add_argument("--decision", help="0/1 column: the model's decision")
    ap.add_argument("--score", help="model score column, with --threshold")
    ap.add_argument("--threshold", type=float)
    ap.add_argument("--baseline", help="0/1 column: the baseline's decision")
    ap.add_argument("--baseline-expr", help="pandas expression for the baseline's decision")
    ap.add_argument("--pred", help="model prediction column (regression)")
    ap.add_argument("--baseline-pred", help="baseline prediction column (regression)")
    ap.add_argument("--cost-act", type=float, default=0.0)
    ap.add_argument("--cost-fp", type=float, default=0.0)
    ap.add_argument("--cost-fn", type=float)
    ap.add_argument("--cost-fn-col")
    ap.add_argument("--boot", type=int, default=BOOTSTRAP)
    args = ap.parse_args(argv)

    df = read_table(args.data)
    used = [args.label, args.decision, args.score, args.baseline, args.pred, args.baseline_pred,
            args.cost_fn_col if args.metric == "cost" else None]
    missing = [c for c in [*used, *args.by] if c and c not in df.columns]
    if missing:
        raise SystemExit(f"Columns not found: {missing}. Columns: {', '.join(df.columns)}")
    df, left_out = drop_empty(df, used)
    regression = args.pred is not None
    if regression:
        model, base = df[args.pred].to_numpy(float), df[args.baseline_pred].to_numpy(float)
    else:
        if args.decision:
            model = df[args.decision].astype(int).to_numpy()
        elif args.score and args.threshold is not None:
            model = (df[args.score] >= args.threshold).astype(int).to_numpy()
        else:
            raise SystemExit("Give --decision, or --score with --threshold.")
        if args.baseline:
            base = df[args.baseline].astype(int).to_numpy()
        elif args.baseline_expr:
            base = df.eval(args.baseline_expr).astype(int).to_numpy()
        else:
            raise SystemExit("Give --baseline or --baseline-expr.")
    fn = None
    if args.metric == "cost":
        if args.cost_fn is None and not args.cost_fn_col:
            raise SystemExit("--metric cost needs --cost-fn or --cost-fn-col.")
        fn = df[args.cost_fn_col].to_numpy(float) if args.cost_fn_col else np.full(len(df), args.cost_fn)
    t = slice_table(df, args.label, model, base, args.by, args.metric, args.cost_act, args.cost_fp, fn, regression, args.boot)
    unit = " per 1,000 rows" if args.metric == "cost" else ""
    direction = "lower" if args.metric.split(":")[0] in LOWER_IS_BETTER else "higher"
    print(f"# Model against baseline by slice\n\nMetric: {args.metric}{unit}, {direction} is better. "
          f"Difference is model minus baseline, with a paired 95% bootstrap interval ({args.boot} resamples).\n")
    if left_out:
        print(left_out + "\n")
    print(fmt_table(t))
    worse = t[t["verdict"] == "model worse"]
    small = t[t["verdict"] == "too small to judge"]
    if len(worse):
        print("\nThe model loses on: " + "; ".join(f"{r.slice}={r.value}" for r in worse.itertuples()) + ".")
    if len(small):
        print("Too small to judge: " + "; ".join(f"{r.slice}={r.value}" for r in small.itertuples()) + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
