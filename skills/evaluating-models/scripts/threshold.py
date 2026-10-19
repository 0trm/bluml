# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Set a model's operating point from what each error costs, or from capacity.

Cost mode: every row the product acts on costs --cost-act (a review, a call),
acting on a negative costs --cost-fp more, and leaving a positive alone costs
--cost-fn, or the value in --cost-fn-col when it varies by row (the amount of a
missed fraud). The script finds the threshold with the lowest total cost, the
range of thresholds within 1% of it, and the policy that acts row by row when
the expected cost of acting is lower, which is right only if scores are
calibrated (the calibration table shows whether they are).

Capacity mode: the product can act on --capacity rows per --per group (40
demos a week); the script reports precision, recall and lift of the top rows.

With --rule-expr or --rule, the current rule is scored on the same rows. With
--time, the threshold is chosen on the earlier half and costed on the later half.

    uv run threshold.py claims.csv --score p --label fraudulent --cost-act 40 --cost-fn-col claim_amount
    uv run threshold.py leads.csv --score p --label won --capacity 40 --per week
"""

# %%
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Thresholds whose cost is within this share of the minimum are treated as equally
# good; choosing inside that range by other criteria (review load) costs little.
FLAT_TOLERANCE = 0.01
# Number of candidate thresholds, taken at score quantiles so every one changes the decision.
GRID = 400


# %%
def read_table(path: str) -> pd.DataFrame:
    p = Path(path)
    return pd.read_parquet(p) if p.suffix in {".parquet", ".pq"} else pd.read_csv(p)


def costs_of(act: np.ndarray, y: np.ndarray, cost_act: float, cost_fp: float, cost_fn: np.ndarray) -> np.ndarray:
    """Cost of each row under a decision."""
    return act * cost_act + act * (1 - y) * cost_fp + (1 - act) * y * cost_fn


def confusion(act: np.ndarray, y: np.ndarray) -> dict:
    tp = int((act & (y == 1)).sum())
    flagged = int(act.sum())
    pos = int(y.sum())
    return dict(flagged=flagged, flag_rate=flagged / len(y), precision=tp / flagged if flagged else float("nan"),
                recall=tp / pos if pos else float("nan"))


def cost_curve(score: np.ndarray, y: np.ndarray, cost_act: float, cost_fp: float, cost_fn: np.ndarray) -> pd.DataFrame:
    grid = np.unique(np.quantile(score, np.linspace(0, 1, GRID)))
    grid = np.append(grid, np.inf)  # acting on nothing
    rows = []
    for t in grid:
        act = score >= t
        rows.append(dict(threshold=t, cost=costs_of(act, y, cost_act, cost_fp, cost_fn).sum(), **confusion(act, y)))
    return pd.DataFrame(rows)


def best_threshold(curve: pd.DataFrame) -> tuple[float, float, float]:
    i = int(curve["cost"].idxmin())
    best = curve.loc[i, "cost"]
    flat = curve[curve["cost"] <= best * (1 + FLAT_TOLERANCE)]["threshold"]
    return float(curve.loc[i, "threshold"]), float(flat.min()), float(flat.max())


def expected_cost_policy(score: np.ndarray, cost_act: float, cost_fp: float, cost_fn: np.ndarray) -> np.ndarray:
    """Act when p * cost_fn > cost_act + (1 - p) * cost_fp, with p the score read as a probability."""
    return score * (cost_fn + cost_fp) > cost_act + cost_fp


def calibration(score: np.ndarray, y: np.ndarray, bins: int = 10) -> pd.DataFrame:
    q = pd.qcut(score, bins, duplicates="drop")
    t = pd.DataFrame(dict(score=score, y=y, bin=q)).groupby("bin", observed=True)
    return t.agg(rows=("y", "size"), mean_score=("score", "mean"), observed_rate=("y", "mean")).reset_index(drop=True)


def capacity_table(df: pd.DataFrame, score: str, label: str, k: int, per: str | None) -> pd.DataFrame:
    groups = df.groupby(per) if per else [("all", df)]
    rows = []
    for g, d in groups:
        top = d.nlargest(k, score)
        rows.append(dict(group=g, rows=len(d), positives=int(d[label].sum()), acted=len(top),
                         hits=int(top[label].sum()), precision=top[label].mean(),
                         recall=top[label].sum() / max(d[label].sum(), 1), base_rate=d[label].mean()))
    out = pd.DataFrame(rows)
    out["lift"] = out["precision"] / out["base_rate"]
    return out


# %%
def fmt_table(df: pd.DataFrame) -> str:
    def cell(v):
        if isinstance(v, (float, np.floating)):
            if v != v:
                return ""
            if v == np.inf:
                return "act on none"
            return f"{v:,.4g}" if abs(v) < 1000 else f"{v:,.0f}"
        return str(v)
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns)
    return head + "\n" + "\n".join("| " + " | ".join(cell(v) for v in r) + " |" for r in df.itertuples(index=False))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("--score", required=True, help="model score column, higher means more likely positive")
    ap.add_argument("--label", required=True, help="0/1 outcome column")
    ap.add_argument("--cost-act", type=float, default=0.0, help="cost of acting on any row")
    ap.add_argument("--cost-fp", type=float, default=0.0, help="extra cost of acting on a negative")
    ap.add_argument("--cost-fn", type=float, help="cost of leaving a positive alone")
    ap.add_argument("--cost-fn-col", help="column holding each row's cost of leaving it alone if positive")
    ap.add_argument("--capacity", type=int, help="rows the product can act on per group")
    ap.add_argument("--per", help="group column for --capacity (a month, a day)")
    ap.add_argument("--rule", help="0/1 column with the current rule's decisions")
    ap.add_argument("--rule-expr", help="pandas expression for the current rule, such as 'claim_amount > 5000 and policy_age_days < 30'")
    ap.add_argument("--time", help="time column: choose on the earlier half, cost on the later half")
    args = ap.parse_args(argv)

    df = read_table(args.data)
    missing = [c for c in [args.score, args.label, args.cost_fn_col, args.per, args.rule, args.time] if c and c not in df.columns]
    if missing:
        raise SystemExit(f"Columns not found: {missing}. Columns: {', '.join(df.columns)}")
    df = df.dropna(subset=[args.score, args.label]).reset_index(drop=True)
    y = df[args.label].astype(int).to_numpy()
    s = df[args.score].astype(float).to_numpy()
    out = [f"# Operating point\n\n{len(df)} rows, {y.sum()} positives ({y.mean():.2%}).\n"]

    rule = None
    if args.rule:
        rule = df[args.rule].astype(bool).to_numpy()
    elif args.rule_expr:
        rule = df.eval(args.rule_expr).astype(bool).to_numpy()

    if args.capacity:
        cap = capacity_table(df, args.score, args.label, args.capacity, args.per)
        out.append(f"## Top {args.capacity} per {args.per or 'table'}\n\n" + fmt_table(cap))
        out.append(f"\nOverall: {cap['hits'].sum()} hits in {cap['acted'].sum()} actions, "
                   f"precision {cap['hits'].sum() / cap['acted'].sum():.1%}, base rate {y.mean():.1%}.")
        print("\n".join(out))
        return 0

    if args.cost_fn is None and not args.cost_fn_col:
        raise SystemExit("Give --cost-fn or --cost-fn-col (with --cost-act and --cost-fp as needed), or --capacity.")
    fn = df[args.cost_fn_col].astype(float).to_numpy() if args.cost_fn_col else np.full(len(df), args.cost_fn)

    curve = cost_curve(s, y, args.cost_act, args.cost_fp, fn)
    t, lo, hi = best_threshold(curve)
    none_cost = costs_of(np.zeros(len(df), bool), y, args.cost_act, args.cost_fp, fn).sum()
    half = costs_of(s >= 0.5, y, args.cost_act, args.cost_fp, fn).sum()
    best = curve["cost"].min()
    out.append("## Cost of each policy\n")
    policies = [("act on none", np.zeros(len(df), bool)), (f"score >= {t:.4g} (lowest cost)", s >= t),
                ("score >= 0.5", s >= 0.5)]
    exp = expected_cost_policy(s, args.cost_act, args.cost_fp, fn)
    policies.append(("expected cost, row by row (needs calibrated scores)", exp))
    if rule is not None:
        policies.append(("current rule", rule))
    table = pd.DataFrame([dict(policy=name, cost=costs_of(a, y, args.cost_act, args.cost_fp, fn).sum(), **confusion(a, y))
                          for name, a in policies])
    out.append(fmt_table(table))
    out.append(f"\nThresholds from {lo:.4g} to {hi:.4g} cost within {FLAT_TOLERANCE:.0%} of the lowest; "
               f"pick inside that range by workload. A threshold of 0.5 costs {half / best:.2f} times the lowest; "
               f"acting on nothing costs {none_cost / best:.2f} times.")

    i = int(curve["cost"].idxmin())
    around = curve.iloc[max(0, i - 6): i + 7]
    out.append("\n## Cost curve near the lowest cost\n\n" + fmt_table(around))
    out.append("\n## Calibration (score deciles)\n\n" + fmt_table(calibration(s, y)))
    out.append("\nThe row-by-row policy is only as good as this table: where observed rates and mean scores differ, recalibrate first.")

    if args.time:
        order = df[args.time]
        order = order if pd.api.types.is_numeric_dtype(order) else pd.to_datetime(order, errors="coerce")
        early = (order.rank(method="first") <= len(df) / 2).to_numpy()
        c_early = cost_curve(s[early], y[early], args.cost_act, args.cost_fp, fn[early])
        t_early, _, _ = best_threshold(c_early)
        late = ~early
        late_cost = costs_of(s[late] >= t_early, y[late], args.cost_act, args.cost_fp, fn[late]).sum()
        late_best = cost_curve(s[late], y[late], args.cost_act, args.cost_fp, fn[late])["cost"].min()
        msg = (f"\n## Chosen on the earlier half, costed on the later half\n\nThreshold {t_early:.4g} chosen on the earlier half "
               f"costs {late_cost:,.0f} on the later half, against {late_best:,.0f} for the best threshold in hindsight")
        if rule is not None:
            msg += f" and {costs_of(rule[late], y[late], args.cost_act, args.cost_fp, fn[late]).sum():,.0f} for the rule"
        out.append(msg + ".")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
