# %%
"""Tests for the skills' scripts, on synthetic data where the right answer is known.

    uv run --with numpy,pandas,pytest pytest tests
"""

import importlib.util
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


# %% threshold
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


# %% slices
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


def test_category_profile_reports_unseen_categories():
    ref = pd.Series(["ios", "android", "web"] * 100)
    cur = pd.Series(["ios", "android", "web", "tv"] * 100)
    assert dr.category_profile(ref, cur)["unseen"] == pytest.approx(0.25)
