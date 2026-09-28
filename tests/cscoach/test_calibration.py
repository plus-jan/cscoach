"""Tests for the WP calibration layer (M3.3, docs/specs/04 §7 "Per-tier calibration"). Synthetic: code only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.eval.metrics import ece
from cscoach.models.calibration import EPS, Calibrator, crossfit

CFG = {"method": "auto", "by": "tier", "isotonic_min_rows": 5000, "min_rows_per_group": 1000}


def miscalibrated(n=40000, seed=0, groups=("low", "high")):
    rng = np.random.default_rng(seed)
    p_true = rng.uniform(0.02, 0.98, n)
    y = (rng.uniform(size=n) < p_true).astype(int)
    g = np.array(groups)[rng.integers(0, len(groups), n)]
    logit = np.log(p_true / (1 - p_true))
    k = np.where(g == groups[0], 2.0, 0.6)  # over-confident in one group, under-confident in the other
    p_raw = 1 / (1 + np.exp(-k * logit))
    return pd.DataFrame({"p": p_raw, "y": y, "tier": g})


def test_recovers_calibration_per_group():
    d = miscalibrated()
    assert ece(d["p"], d["y"]) > 0.03
    cal = Calibrator(CFG).fit(d["p"], d["y"], d)
    q = cal.predict(d["p"], d)
    for _, g in d.assign(q=q).groupby("tier"):
        assert ece(g["q"], g["y"]) < 0.015


def test_monotone_and_clipped():
    d = miscalibrated()
    cal = Calibrator({**CFG, "by": None}).fit(d["p"], d["y"], d)
    grid = np.linspace(0, 1, 501)
    q = cal.predict(grid, None)
    assert np.all(np.diff(q) >= 0) and q.min() >= EPS and q.max() <= 1 - EPS


def test_auto_method_and_group_fallback():
    d = miscalibrated(n=6000)
    cal = Calibrator({**CFG, "min_rows_per_group": 4000}).fit(d["p"], d["y"], d)
    assert cal.global_.method == "isotonic"          # 6,000 rows ≥ 5,000
    assert cal.groups_ == {}                         # each tier has ~3,000 < 4,000 rows → global only
    small = Calibrator(CFG).fit(d["p"][:3000], d["y"][:3000], d.iloc[:3000])
    assert small.global_.method == "platt" and set(small.groups_) == {"low", "high"}
    assert all(c.method == "platt" for c in small.groups_.values())


def test_unseen_group_uses_global_and_none_is_identity():
    d = miscalibrated()
    cal = Calibrator(CFG).fit(d["p"], d["y"], d)
    new = pd.DataFrame({"tier": ["semipro", "low"]})
    q = cal.predict(np.array([0.7, 0.7]), new)
    assert q[0] == pytest.approx(cal.global_.predict(np.array([0.7]))[0])
    ident = Calibrator({**CFG, "method": "none"}).fit(d["p"], d["y"], d)
    np.testing.assert_allclose(ident.predict(d["p"], d), np.clip(d["p"], EPS, 1 - EPS))


def test_by_several_columns_and_missing_group_values():
    d = miscalibrated().assign(platform=lambda x: np.where(np.arange(len(x)) % 2, "steam", "faceit"))
    d.loc[:99, "tier"] = None
    cal = Calibrator({**CFG, "by": ["tier", "platform"]}).fit(d["p"], d["y"], d)
    assert "null|steam" not in cal.groups_ and "low|steam" in cal.groups_  # 50 rows < min_rows_per_group
    assert np.isfinite(cal.predict(d["p"], d)).all()


def test_roundtrip():
    d = miscalibrated()
    for method in ("isotonic", "platt"):
        cal = Calibrator({**CFG, "method": method}).fit(d["p"], d["y"], d)
        back = Calibrator.from_dict(cal.to_dict())
        np.testing.assert_allclose(back.predict(d["p"], d), cal.predict(d["p"], d))


def test_crossfit_never_uses_the_fold_it_predicts():
    d = miscalibrated(n=20000).assign(fold=lambda x: np.arange(len(x)) % 4)
    a = crossfit(d, CFG)
    flipped = d.copy()
    flipped.loc[flipped["fold"] == 0, "y"] = 1 - flipped.loc[flipped["fold"] == 0, "y"]
    b = crossfit(flipped, CFG)
    np.testing.assert_allclose(a[d["fold"] == 0], b[d["fold"] == 0])      # fold-0 labels don't touch fold 0
    assert not np.allclose(a[d["fold"] == 1], b[d["fold"] == 1])          # but they do feed the other folds


def test_calibrated_loop_task_rows_and_identity():
    from cscoach.loops.tasks import TASKS, synthetic_wp_frame
    from cscoach.models.wp_gbdt import gbdt_oof

    df = synthetic_wp_frame(n_matches=120, rounds=10, snaps=3, seed=0)
    df["fold"] = df["match_id"].map({m: i % 3 for i, m in enumerate(sorted(df["match_id"].unique()))})
    gbdt = {"features": ["x1", "x2"], "categorical": [], "label": "y", "stratum": "tier", "monotone": {"x1": 1},
            "num_boost_round": 40, "early_stopping_rounds": 10, "es_fraction": 0.15, "seed": 7,
            "params": {"learning_rate": 0.1, "num_leaves": 7, "min_child_samples": 20, "num_threads": 2}}
    base = gbdt_oof(df, gbdt)
    none = TASKS["gbdt_wp_calibrated"](df, {"label": "y", "stratum": "tier", "gbdt": gbdt,
                                            "calibration": {**CFG, "method": "none"}})
    assert none["match_id"].tolist() == base["match_id"].tolist()
    np.testing.assert_allclose(none["p"], np.clip(base["p"], EPS, 1 - EPS))
    iso = TASKS["gbdt_wp_calibrated"](df, {"label": "y", "stratum": "tier", "gbdt": gbdt, "calibration": CFG})
    assert list(iso.columns) == list(base.columns) and not np.allclose(iso["p"], base["p"])
