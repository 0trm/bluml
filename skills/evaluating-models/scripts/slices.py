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
predictions (lower is better).
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
LOWER_IS_BETTER = {"cost", "mae", "rmse", "pinball", "flag_rate", "fpr"}


# %%
def read_table(path: str) -> pd.DataFrame:
    p = Path(path)
    return pd.read_parquet(p) if p.suffix in {".parquet", ".pq"} else pd.read_csv(p)


def metric_fn(name: str, y, cost_act=0.0, cost_fp=0.0, fn=None):
    """Return f(pred, idx) -> metric on the rows idx."""
    if name == "cost":
        def f(a, idx):
            a, t, c = a[idx], y[idx], fn[idx]
            return float((a * cost_act + a * (1 - t) * cost_fp + (1 - a) * t * c).sum() / len(idx) * 1000)
        return f
    if name == "precision":
        return lambda a, idx: float(y[idx][a[idx] == 1].mean()) if a[idx].sum() else float("nan")
    if name == "recall":
        return lambda a, idx: float(a[idx][y[idx] == 1].mean()) if y[idx].sum() else float("nan")
    if name == "fpr":
        return lambda a, idx: float(a[idx][y[idx] == 0].mean()) if (y[idx] == 0).any() else float("nan")
    if name == "accuracy":
        return lambda a, idx: float((a[idx] == y[idx]).mean())
    if name == "flag_rate":
        return lambda a, idx: float(a[idx].mean())
    if name == "mae":
        return lambda p, idx: float(np.abs(y[idx] - p[idx]).mean())
    if name == "rmse":
        return lambda p, idx: float(np.sqrt(((y[idx] - p[idx]) ** 2).mean()))
    if name.startswith("pinball"):
        q = float(name.split(":")[1]) if ":" in name else 0.5
        def f(p, idx):
            d = y[idx] - p[idx]
            return float(np.maximum(q * d, (q - 1) * d).mean())
        return f
    raise SystemExit(f"Unknown metric {name}")


def compare(model, base, idx, f, rng, b=BOOTSTRAP):
    m, k = f(model, idx), f(base, idx)
    diffs = np.empty(b)
    for i in range(b):
        s = idx[rng.integers(0, len(idx), len(idx))]
        diffs[i] = f(model, s) - f(base, s)
    lo, hi = np.nanpercentile(diffs, [2.5, 97.5])
    return m, k, m - k, lo, hi


def slice_table(df: pd.DataFrame, label: str, model: np.ndarray, base: np.ndarray, by: list[str], metric: str,
                cost_act=0.0, cost_fp=0.0, fn=None, regression=False, boot=BOOTSTRAP, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    y = df[label].to_numpy(dtype=float)
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

    df = read_table(args.data).reset_index(drop=True)
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
