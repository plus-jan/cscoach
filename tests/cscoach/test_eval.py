"""Tests for metrics and grouped splits (docs/specs/04 §7). Synthetic data: code behaviour only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.eval.metrics import brier, ece, logloss, reliability
from cscoach.eval.splits import grouped_split, kfold_groups


def test_brier_and_logloss():
    y = np.array([0, 1])
    assert brier(np.array([0.0, 1.0]), y) == 0.0
    assert brier(np.array([0.5, 0.5]), y) == pytest.approx(0.25)
    assert logloss(np.array([0.5, 0.5]), y) == pytest.approx(np.log(2))
    assert np.isfinite(logloss(np.array([0.0, 1.0]), np.array([1, 0])))  # clipped


def test_ece_small_when_calibrated_and_large_when_shifted():
    rng = np.random.default_rng(0)
    p = rng.uniform(0, 1, 50_000)
    y = rng.uniform(0, 1, 50_000) < p
    assert ece(p, y, n_bins=15) < 0.01
    assert ece(np.clip(p + 0.15, 0, 1), y, n_bins=15) > 0.1


def test_reliability_quantile_bins():
    rng = np.random.default_rng(1)
    p = rng.uniform(0, 1, 3000)
    y = rng.uniform(0, 1, 3000) < p
    rel = reliability(p, y, n_bins=15)
    assert rel["count"].sum() == 3000 and len(rel) == 15
    assert rel["count"].min() >= 190  # quantile bins are (nearly) equal-sized
    assert (rel["mean_p"].diff().dropna() > 0).all()


def test_reliability_degenerate_predictions_collapse_to_one_bin():
    # spec: unique quantile edges, first/last set to 0 and 1 → two distinct values give one bin
    rel = reliability(np.array([0.1] * 50 + [0.9] * 50), np.array([0, 1] * 50), n_bins=15)
    assert len(rel) == 1 and rel["count"].item() == 100


def test_grouped_split_disjoint_complete_and_every_stratum_in_test():
    groups = pd.DataFrame({"match_id": [f"m{i}" for i in range(300)],
                           "stratum": ["a"] * 200 + ["b"] * 90 + ["c"] * 10})
    s = grouped_split(groups, fractions={"train": 0.7, "calibration": 0.1, "test": 0.2}, seed=7)
    assert set(s) == set(groups["match_id"])  # complete
    assert set(s.values()) == {"train", "calibration", "test"}
    for st, g in groups.groupby("stratum"):
        assert "test" in {s[m] for m in g["match_id"]}
    assert s == grouped_split(groups, fractions={"train": 0.7, "calibration": 0.1, "test": 0.2}, seed=7)
    counts = pd.Series(s).value_counts()
    assert 200 <= counts["train"] <= 215 and 55 <= counts["test"] <= 65


def test_kfold_groups_partition_training_matches():
    ids = [f"m{i}" for i in range(50)]
    f = kfold_groups(ids, k=5, seed=3)
    assert sorted(f) == sorted(ids) and set(f.values()) == {0, 1, 2, 3, 4}
    assert f == kfold_groups(ids, k=5, seed=3)
