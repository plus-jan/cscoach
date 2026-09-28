import numpy as np

from cscoach.validation.bootstrap import cluster_bootstrap
from cscoach.validation.ess import design_effect, effective_sample_size, icc_oneway


def test_icc_extremes():
    clusters = np.repeat(np.arange(100), 10)
    identical_within = np.repeat(np.random.default_rng(0).normal(size=100), 10)
    assert icc_oneway(identical_within, clusters) > 0.99
    noise = np.random.default_rng(1).normal(size=1000)
    assert icc_oneway(noise, clusters) < 0.05


def test_ess_equals_clusters_when_perfectly_correlated():
    clusters = np.repeat(np.arange(50), 20)
    v = np.repeat(np.random.default_rng(2).normal(size=50), 20)
    assert abs(effective_sample_size(v, clusters) - 50) < 2
    assert design_effect(clusters, 0.0) == 1.0


def test_cluster_bootstrap_wider_than_naive():
    rng = np.random.default_rng(3)
    clusters = np.repeat(np.arange(40), 25)
    v = np.repeat(rng.normal(size=40), 25) + rng.normal(scale=0.1, size=1000)
    ci = cluster_bootstrap(np.mean, (v,), clusters, n_resamples=300, seed=0)
    naive_half = 1.96 * v.std() / np.sqrt(len(v))
    assert (ci.high - ci.low) / 2 > 2 * naive_half
    assert ci.low <= ci.estimate <= ci.high
