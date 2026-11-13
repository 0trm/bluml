# %%
"""Tests for the skills' scripts, on synthetic data where the right answer is known.

    uv run --with numpy,pandas,pytest pytest tests
"""

import importlib.util
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SKILLS = Path(__file__).resolve().parent.parent / "skills"


def load(rel: str):
    spec = importlib.util.spec_from_file_location(Path(rel).stem, SKILLS / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


leak = load("building-datasets/scripts/leakage_screen.py")
thr = load("evaluating-models/scripts/threshold.py")
sl = load("evaluating-models/scripts/slices.py")
dr = load("monitoring-models/scripts/drift.py")


# %% leakage_screen
def churn_like(n=20000, seed=0):
    rng = np.random.default_rng(seed)
    month = rng.integers(0, 12, n)
    risk = rng.normal(0, 1, n)
    y = (rng.random(n) < 1 / (1 + np.exp(-(-3.5 + 1.0 * risk)))).astype(int)
    honest = -risk + rng.normal(0, 1, n)
    backfilled = np.where(month < 8, -3 * y + rng.normal(0, 0.3, n), -0.3 * risk + rng.normal(0, 1, n))
    return pd.DataFrame(dict(month=month, honest=honest, backfilled=backfilled, noise=rng.normal(0, 1, n), y=y))


def test_auc_matches_known_values():
    y = pd.Series([0, 0, 1, 1])
    assert leak.auc(pd.Series([0.1, 0.2, 0.8, 0.9]), y) == 1.0
    assert leak.auc(pd.Series([0.9, 0.8, 0.2, 0.1]), y) == 1.0  # folded: direction does not matter
    assert leak.auc(pd.Series([0.5, 0.5, 0.5, 0.5]), y) == 0.5


def test_screen_flags_the_backfilled_feature_and_not_the_honest_one():
    result = leak.screen(churn_like(), "y", time="month")
    flagged = " ".join(result["flags"])
    assert "`backfilled`" in flagged
    assert "`honest`" not in flagged and "`noise`" not in flagged


def test_screen_flags_missingness_that_depends_on_the_label():
    rng = np.random.default_rng(1)
    n = 5000
    y = (rng.random(n) < 0.2).astype(int)
    filled_after = np.where(y == 1, np.nan, rng.normal(0, 1, n))
    df = pd.DataFrame(dict(filled_after=filled_after, other=rng.normal(0, 1, n), y=y))
    assert any("`filled_after` is missing" in f for f in leak.screen(df, "y")["flags"])


def test_screen_reports_entities_and_time_overlap_across_splits():
    df = pd.DataFrame(dict(t=[1, 2, 3, 4, 5, 6], uid=["a", "b", "a", "c", "d", "e"], x=[1, 2, 3, 4, 5, 6],
                           y=[0, 1, 0, 1, 0, 1], split=["train", "train", "test", "train", "test", "test"]))
    flags = " ".join(leak.screen(df, "y", time="t", id_col="uid", split="split")["flags"])
    assert "overlap in time" in flags
    assert "appear in more than one split" in flags


def test_screen_reports_empty_values_with_splits_instead_of_crashing(tmp_path, capsys):
    path = tmp_path / "na.csv"
    pd.DataFrame(dict(t=[1, 1, 2, 2], id=["a", "b", "a", "b"], x=[1.0, None, 2.0, 3.0],
                      y=[0, 1, 0, 1], split=["train", "train", "valid", "valid"])).to_csv(path, index=False)
    code = leak.main([str(path), "--label", "y", "--time", "t", "--id", "id", "--split", "split"])
    assert code in (0, 1)
    x_line = next(line for line in capsys.readouterr().out.splitlines() if line.startswith("| x |"))
    assert "| 25.0% |" in x_line


def test_rows_empty_in_the_same_column_count_as_duplicates_across_splits():
    df = pd.DataFrame(dict(x=[1.0, np.nan, np.nan, 2.0], c=["a", None, None, "b"],
                           y=[0, 1, 1, 0], split=["train", "train", "test", "test"]))
    flags = " ".join(leak.screen(df, "y", split="split")["flags"])
    assert "1 distinct feature rows appear in more than one split" in flags


def test_screen_flags_a_feature_that_changes_strength_over_time_for_a_count_label():
    rng = np.random.default_rng(8)
    n = 20000
    month = rng.integers(0, 12, n)
    risk = rng.normal(0, 1, n)
    y = rng.poisson(np.exp(0.5 * risk))
    backfilled = np.where(month < 8, y + rng.normal(0, 0.1, n), rng.normal(0, 1, n))
    df = pd.DataFrame(dict(month=month, honest=risk + rng.normal(0, 1, n), backfilled=backfilled,
                           noise=rng.normal(0, 1, n), y=y))
    result = leak.screen(df, "y", time="month")
    flagged = " ".join(result["flags"])
    assert "`backfilled` scores" in flagged and "produced differently over time" in flagged
    assert "`honest`" not in flagged and "`noise`" not in flagged
    assert len(result["stretches"]) == leak.TIME_CHUNKS
    assert result["stretches"][0].startswith("0 to") and result["stretches"][-1].endswith("to 11")  # oldest first
    # Every row of the features table has as many cells as its header, |rho| included.
    table = [line for line in leak.report(result).splitlines() if line.startswith("| ")]
    cells = {len(re.split(r"(?<!\\)\|", line)) for line in table}
    assert len(cells) == 1


def test_screen_leaves_out_rows_without_a_label():
    rng = np.random.default_rng(9)
    n = 2000
    y = (rng.random(n) < 0.3).astype(float)
    y[:300] = np.nan
    df = pd.DataFrame(dict(x=rng.normal(0, 1, n), y=y))
    result = leak.screen(df, "y")
    assert result["n"] == 1700 and result["positives"] == int(np.nansum(y))
    assert "300 rows without a label" in leak.report(result)


def test_screen_survives_rows_without_a_time():
    rng = np.random.default_rng(10)
    n = 2000
    t = pd.Series(pd.date_range("2024-01-01", periods=n, freq="h").astype(str))
    t[5] = None
    df = pd.DataFrame(dict(t=t, x=rng.normal(0, 1, n), y=(rng.random(n) < 0.3).astype(int)))
    result = leak.screen(df, "y", time="t")
    assert len(result["stretches"]) >= 2
    assert any("1 rows have no readable `t`" in note for note in result["notes"])


def test_rows_that_share_a_time_stay_in_one_stretch():
    rng = np.random.default_rng(11)
    month = np.repeat(["2024-01", "2024-02", "2024-03"], [700, 700, 600])
    df = pd.DataFrame(dict(m=month, x=rng.normal(0, 1, 2000), y=(rng.random(2000) < 0.3).astype(int)))
    assert leak.screen(df, "y", time="m")["stretches"] == [
        "2024-01 to 2024-01", "2024-02 to 2024-02", "2024-03 to 2024-03"]


def test_screen_flags_time_overlap_between_splits_that_are_not_neighbours():
    t = list(range(1, 13)) + [2, 3, 4, 5]
    split = ["train"] * 12 + ["valid", "valid", "test", "test"]
    df = pd.DataFrame(dict(t=t, x=range(16), y=[0, 1] * 8, split=split))
    flags = " ".join(leak.screen(df, "y", time="t", split="split")["flags"])
    assert "Splits `train` and `valid` overlap" in flags
    assert "Splits `train` and `test` overlap in time (4 to 5)" in flags


def test_screen_says_when_id_is_given_without_a_split():
    df = pd.DataFrame(dict(uid=["a", "b"] * 50, x=range(100), y=[0, 1] * 50))
    assert any("`--split`" in note for note in leak.screen(df, "y", id_col="uid")["notes"])


# %% threshold
def run_main(main, path, args, capsys):
    code = main([str(path), *args])
    return code, capsys.readouterr().out


def test_cost_threshold_finds_the_known_optimum():
    # Calibrated scores with equal costs: the best threshold is 0.5.
    rng = np.random.default_rng(2)
    p = rng.uniform(0, 1, 50000)
    y = (rng.random(50000) < p).astype(int)
    curve = thr.cost_curve(p, y, 0.0, 1.0, np.full(len(y), 1.0))
    t, lo, hi = thr.best_threshold(curve)
    assert abs(t - 0.5) < 0.05
    assert lo <= t <= hi


def test_asymmetric_costs_move_the_threshold_down():
    rng = np.random.default_rng(3)
    p = rng.uniform(0, 1, 50000)
    y = (rng.random(50000) < p).astype(int)
    curve = thr.cost_curve(p, y, 0.0, 1.0, np.full(len(y), 9.0))  # a miss costs 9 times a false alarm
    t, _, _ = thr.best_threshold(curve)
    assert abs(t - 0.1) < 0.05


def test_expected_cost_policy_acts_on_large_amounts_at_low_scores():
    act = thr.expected_cost_policy(np.array([0.01, 0.01, 0.5]), 8.0, 0.0, np.array([100.0, 2000.0, 10.0]))
    assert act.tolist() == [False, True, False]


def test_capacity_table_counts_hits_in_the_top_k():
    df = pd.DataFrame(dict(g=["a"] * 4 + ["b"] * 4, s=[4, 3, 2, 1] * 2, y=[1, 0, 0, 1, 0, 0, 1, 1]))
    t = thr.capacity_table(df, "s", "y", 2, "g").set_index("group")
    assert t.loc["a", "hits"] == 1 and t.loc["b", "hits"] == 0


def test_flat_range_stays_around_the_lowest_cost():
    # Two low points with costly thresholds between them: the range must not span the gap.
    curve = pd.DataFrame(dict(threshold=[0.10, 0.12, 0.20, 0.35, 0.50, 0.60, 0.70],
                              cost=[105.0, 100.0, 100.5, 200.0, 150.0, 100.5, 130.0]))
    assert thr.best_threshold(curve) == (0.12, 0.12, 0.20)


def scored_claims(n=2000, seed=12):
    rng = np.random.default_rng(seed)
    p = rng.random(n)
    return pd.DataFrame(dict(p=p, y=(rng.random(n) < p).astype(int), amt=rng.random(n) * 100 + 1))


def test_threshold_leaves_out_rows_with_an_empty_cost(tmp_path, capsys):
    df = scored_claims()
    df.loc[3, "amt"] = np.nan
    df.to_csv(tmp_path / "c.csv", index=False)
    code, out = run_main(thr.main, tmp_path / "c.csv", ["--score", "p", "--label", "y", "--cost-act", "1", "--cost-fn-col", "amt"], capsys)
    assert code == 0
    assert "1999 rows" in out and "Left out 1 rows with an empty value (`amt` 1)" in out


def test_threshold_does_not_count_an_empty_rule_value_as_acting(tmp_path, capsys):
    df = scored_claims()
    df["rule"] = np.where(np.arange(len(df)) % 2 == 0, np.nan, 0.0)  # the rule never acts
    df.to_csv(tmp_path / "r.csv", index=False)
    _, out = run_main(thr.main, tmp_path / "r.csv", ["--score", "p", "--label", "y", "--cost-act", "1", "--cost-fn", "5", "--rule", "rule"], capsys)
    rule_row = next(line for line in out.splitlines() if line.startswith("| current rule |"))
    assert rule_row.split("|")[3].strip() == "0"  # flagged
    assert "Left out 1000 rows" in out


# %% slices
def test_slices_leave_out_rows_without_a_label(tmp_path, capsys):
    rng = np.random.default_rng(13)
    n = 4000
    y = (rng.random(n) < 0.3).astype(float)
    y[:500] = np.nan  # outcomes not in yet
    df = pd.DataFrame(dict(y=y, g=rng.choice(["a", "b"], n), m=rng.integers(0, 2, n), b=rng.integers(0, 2, n)))
    df.to_csv(tmp_path / "s.csv", index=False)
    code, out = run_main(sl.main, tmp_path / "s.csv", ["--label", "y", "--decision", "m", "--baseline", "b", "--by", "g",
                                                         "--metric", "recall", "--boot", "50"], capsys)
    assert code == 0 and "Left out 500 rows with an empty value (`y` 500)" in out
    all_row = next(line for line in out.splitlines() if line.startswith("| all |"))
    assert all_row.split("|")[3].strip() == "3500"  # rows


def test_batched_bootstrap_matches_one_resample_at_a_time():
    rng = np.random.default_rng(14)
    n = 300
    y = (rng.random(n) < 0.3).astype(float)
    a = rng.integers(0, 2, n)
    idx = rng.integers(0, n, (5, n))
    for name in ["cost", "precision", "recall", "fpr", "accuracy", "flag_rate", "mae", "rmse", "pinball:0.8"]:
        f = sl.metric_fn(name, y, 2.0, 1.0, np.full(n, 10.0))
        assert np.allclose(f(a, idx), [f(a, row) for row in idx], equal_nan=True), name


def test_slices_find_the_segment_where_the_model_loses():
    rng = np.random.default_rng(4)
    n = 20000
    seg = rng.choice(["old", "new"], n, p=[0.8, 0.2])
    y = (rng.random(n) < 0.2).astype(int)
    model = np.where(seg == "old", np.where(rng.random(n) < 0.9, y, 1 - y), np.where(rng.random(n) < 0.6, y, 1 - y))
    base = np.where(rng.random(n) < 0.75, y, 1 - y)
    df = pd.DataFrame(dict(seg=seg, y=y))
    t = sl.slice_table(df, "y", model, base, ["seg"], "accuracy", boot=200).set_index("value")
    assert t.loc["old", "verdict"] == "model better"
    assert t.loc["new", "verdict"] == "model worse"


def test_slices_mark_small_slices():
    rng = np.random.default_rng(5)
    n = 3000
    df = pd.DataFrame(dict(c=np.where(np.arange(n) < 100, "tiny", "big"), y=(rng.random(n) < 0.1).astype(int)))
    a = rng.integers(0, 2, n)
    t = sl.slice_table(df, "y", a, a, ["c"], "recall", boot=50).set_index("value")
    assert t.loc["tiny", "verdict"] == "too small to judge"


def test_pinball_loss_prefers_the_right_quantile():
    rng = np.random.default_rng(6)
    y = rng.exponential(30, 20000)
    df = pd.DataFrame(dict(y=y, k="all"))
    p80 = np.full(len(y), np.quantile(y, 0.8))
    p50 = np.full(len(y), np.quantile(y, 0.5))
    t = sl.slice_table(df, "y", p80, p50, ["k"], "pinball:0.8", regression=True, boot=100)
    assert t.iloc[0]["difference"] < 0


# %% drift
def test_psi_is_zero_for_identical_and_large_for_a_unit_change():
    rng = np.random.default_rng(7)
    ref = pd.Series(np.exp(rng.normal(4.6, 0.5, 10000)))
    assert dr.numeric_profile(ref, ref.sample(frac=1, random_state=0))["psi"] < 0.01
    shifted = dr.numeric_profile(ref, ref * 100)
    assert shifted["psi"] > dr.PSI_SHIFT and shifted["out_of_range"] > 0.9


def test_whole_numbers_read_as_float_and_as_int_are_one_category():
    ref = pd.Series([1.0, 2.0, 3.0] * 100 + [np.nan])  # one empty value makes pandas read floats
    cur = pd.Series([1, 2, 3] * 100)
    p = dr.category_profile(ref, cur)
    assert p["unseen"] == 0 and p["psi"] < dr.PSI_WATCH


def test_category_profile_reports_unseen_categories():
    ref = pd.Series(["ios", "android", "web"] * 100)
    cur = pd.Series(["ios", "android", "web", "tv"] * 100)
    assert dr.category_profile(ref, cur)["unseen"] == pytest.approx(0.25)
