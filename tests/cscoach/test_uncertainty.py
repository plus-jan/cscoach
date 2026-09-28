"""Tests for ICC / design effect / ESS and cluster-bootstrap CIs (docs/specs/04 §7). Synthetic: code only (A-33)."""
import numpy as np
import pytest

from cscoach.eval.uncertainty import cluster_bootstrap_ci, design_effect, ess, icc1


def test_icc_zero_and_one():
    rng = np.random.default_rng(0)
    g = np.repeat(np.arange(300), 10)
    assert icc1(rng.normal(size=g.size), g) < 0.05
    const = np.repeat(rng.normal(size=300), 10)
    assert icc1(const, g) == pytest.approx(1.0)


def test_deff_one_without_clustering_and_ess_equals_clusters_when_constant():
    rng = np.random.default_rng(1)
    g = np.repeat(np.arange(200), 12)
    assert design_effect(np.zeros(1) + 0.0, g, icc=0.0) == pytest.approx(1.0)
    const = np.repeat(rng.normal(size=200), 12)
    assert ess(const, g) == pytest.approx(200, rel=0.02)


def test_cluster_ci_wider_than_iid_when_icc_high():
    rng = np.random.default_rng(2)
    g = np.repeat(np.arange(200), 20)
    x = np.repeat(rng.normal(size=200), 20) + rng.normal(0, 0.1, g.size)
    lo, hi = cluster_bootstrap_ci(x, g, np.mean, n_resamples=500, seed=3)
    iid = 1.96 * x.std() / np.sqrt(x.size)
    assert (hi - lo) / 2 > 3 * iid
