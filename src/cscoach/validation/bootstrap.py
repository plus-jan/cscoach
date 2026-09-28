"""Cluster (block) bootstrap confidence intervals. Clusters are usually matches."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

MetricFn = Callable[..., float]


@dataclass(frozen=True)
class BootstrapCI:
    estimate: float
    low: float
    high: float
    n_resamples: int
    n_clusters: int

    def excludes(self, value: float = 0.0) -> bool:
        return not (self.low <= value <= self.high)

    def as_dict(self) -> dict[str, float]:
        return {"estimate": self.estimate, "low": self.low, "high": self.high}


def cluster_bootstrap(
    metric: MetricFn,
    arrays: tuple[ArrayLike, ...],
    clusters: ArrayLike,
    n_resamples: int = 500,
    alpha: float = 0.05,
    seed: int = 0,
) -> BootstrapCI:
    """Percentile CI of ``metric(*arrays)`` resampling whole clusters with replacement.

    Example: ``cluster_bootstrap(brier_score, (y, p), match_ids)`` or, for a model
    difference, ``metric=lambda y, a, b: log_loss(y, a) - log_loss(y, b)``.
    """
    arrs = [np.asarray(a) for a in arrays]
    cl = np.asarray(clusters)
    uniq, inv = np.unique(cl, return_inverse=True)
    members: list[NDArray[np.intp]] = [np.flatnonzero(inv == i) for i in range(len(uniq))]
    rng = np.random.default_rng(seed)
    estimate = float(metric(*arrs))
    stats = np.empty(n_resamples)
    for b in range(n_resamples):
        pick = rng.integers(0, len(uniq), len(uniq))
        idx = np.concatenate([members[i] for i in pick])
        stats[b] = metric(*[a[idx] for a in arrs])
    low, high = np.nanquantile(stats, [alpha / 2, 1 - alpha / 2])
    return BootstrapCI(estimate, float(low), float(high), n_resamples, len(uniq))
