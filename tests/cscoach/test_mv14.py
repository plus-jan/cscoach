"""Tests for the MV.14 loop simulator. Synthetic data: method properties only (A-33)."""
import numpy as np
import pytest

from cscoach.verify.mv14 import calibrate_sigma, lower_bounds, simulate_loop, simulate_truth, variant_losses


def test_truth_is_calibrated():
    rng = np.random.default_rng(0)
    t = simulate_truth(rng, n_matches=3000, rounds=10, snaps=6)
    p, y = t["p"], t["y"]
    for lo, hi in ((0.1, 0.2), (0.45, 0.55), (0.8, 0.9)):
        m = (p > lo) & (p < hi)
        assert abs(y[m].mean() - p[m].mean()) < 0.02
    # snapshots of a round share one outcome
    assert (t["y"].reshape(-1, 6).std(axis=1) == 0).all()


def test_equal_error_variants_have_zero_expected_difference():
    rng = np.random.default_rng(1)
    t = simulate_truth(rng, n_matches=2000, rounds=10, snaps=6)
    a = variant_losses(rng, t, sigma_row=0.5, sigma_match=0.2)
    b = variant_losses(rng, t, sigma_row=0.5, sigma_match=0.2)
    d = (a.sum() - b.sum()) / a.size
    assert abs(d) < 0.003


def test_calibrated_sigma_gives_the_target_improvement():
    rng = np.random.default_rng(2)
    t = simulate_truth(rng, n_matches=4000, rounds=10, snaps=6)
    s = calibrate_sigma(t, sigma_row=0.5, sigma_match=0.2, target=0.002, seed=3)
    assert 0 < s < 0.5
    a = variant_losses(np.random.default_rng(4), t, sigma_row=0.5, sigma_match=0.2)
    b = variant_losses(np.random.default_rng(5), t, sigma_row=s, sigma_match=0.2)
    assert (a.mean() - b.mean()) == pytest.approx(0.002, abs=0.0015)


def test_lower_bounds_shape_and_order():
    rng = np.random.default_rng(6)
    d = rng.normal(0.01, 0.05, size=(3, 500))  # 3 variants × 500 matches (per-match mean deltas)
    n = np.full(500, 10)
    lb = lower_bounds(d * n, n, levels=(0.05, 0.05 / 15), n_resamples=500, seed=1)
    assert lb.shape == (3, 2) and (lb[:, 1] <= lb[:, 0]).all()  # stricter level → lower bound


def test_null_loop_rarely_keeps_with_correction():
    res = [simulate_loop(seed=s, n_matches=400, rounds=10, snaps=4, budget=15, planted=None, n_resamples=400)
           for s in range(12)]
    corrected = np.mean([r["any_keep_corrected"] for r in res])
    uncorrected = np.mean([r["any_keep_uncorrected"] for r in res])
    assert corrected <= uncorrected
