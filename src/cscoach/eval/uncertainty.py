"""ICC(1), Kish design effect, ESS and cluster-bootstrap CIs exactly as in docs/specs/04 §7."""
from __future__ import annotations

import numpy as np
import pandas as pd


def icc1(values, groups) -> float:
    """One-way ANOVA ICC(1), clipped to [0, 1]."""
    df = pd.DataFrame({"y": np.asarray(values, float), "g": np.asarray(groups)})
    stats = df.groupby("g")["y"].agg(["mean", "size"])
    k, n_i = len(stats), stats["size"].to_numpy()
    N = n_i.sum()
    if k < 2 or N <= k:
        return 0.0
    grand = df["y"].mean()
    msb = (n_i * (stats["mean"].to_numpy() - grand) ** 2).sum() / (k - 1)
    within = df["y"] - df["g"].map(stats["mean"])
    msw = (within ** 2).sum() / (N - k)
    n0 = (N - (n_i ** 2).sum() / N) / (k - 1)
    denom = msb + (n0 - 1) * msw
    return float(np.clip((msb - msw) / denom, 0, 1)) if denom > 0 else 1.0


def design_effect(values, groups, icc: float | None = None) -> float:
    """Kish, unequal clusters: 1 + ((CV² + 1)·m̄ − 1)·ICC."""
    sizes = pd.Series(np.asarray(groups)).value_counts().to_numpy().astype(float)
    m = sizes.mean()
    cv2 = (sizes.std(ddof=0) / m) ** 2 if m > 0 else 0.0
    r = icc1(values, groups) if icc is None else icc
    return float(1 + ((cv2 + 1) * m - 1) * r)


def ess(values, groups) -> float:
    return float(len(np.asarray(values)) / design_effect(values, groups))


def cluster_bootstrap_ci(values, groups, stat, *, n_resamples: int, seed: int, alpha: float = 0.05):
    """Percentile CI of ``stat`` over whole-cluster resamples (``stat`` gets the resampled value array)."""
    v = np.asarray(values)
    codes, _ = pd.factorize(np.asarray(groups))
    order = np.argsort(codes, kind="stable")
    bounds = np.r_[0, np.cumsum(np.bincount(codes))]
    rng = np.random.default_rng(seed)
    k = len(bounds) - 1
    out = []
    for _ in range(n_resamples):
        pick = rng.integers(0, k, k)
        idx = np.concatenate([order[bounds[c]:bounds[c + 1]] for c in pick])
        out.append(stat(v[idx]))
    return float(np.quantile(out, alpha / 2)), float(np.quantile(out, 1 - alpha / 2))
