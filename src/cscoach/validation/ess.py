"""Intraclass correlation, design effect and effective sample size for clustered data.

Snapshots within a round share the outcome, so n_rows overstates the information content.
We use the one-way ANOVA ICC estimator and Kish's design effect for unequal cluster sizes:

    DEFF = 1 + ((CV^2 + 1) * m_bar - 1) * ICC,   ESS = n / DEFF

where m_bar is the mean cluster size and CV its coefficient of variation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike


def icc_oneway(values: ArrayLike, clusters: ArrayLike) -> float:
    """ICC(1) via one-way random-effects ANOVA; clipped to [0, 1]."""
    df = pd.DataFrame({"v": np.asarray(values, dtype=float), "c": np.asarray(clusters)})
    g = df.groupby("c")["v"]
    sizes = g.size().to_numpy(dtype=float)
    k = len(sizes)
    n = sizes.sum()
    if k < 2 or n <= k:
        return 0.0
    grand = df["v"].mean()
    means = g.mean().to_numpy()
    ssb = float(np.sum(sizes * (means - grand) ** 2))
    ssw = float(((df["v"] - g.transform("mean")) ** 2).sum())
    msb = ssb / (k - 1)
    msw = ssw / (n - k)
    n0 = (n - np.sum(sizes**2) / n) / (k - 1)
    denom = msb + (n0 - 1) * msw
    if denom <= 0:
        return 0.0
    return float(np.clip((msb - msw) / denom, 0.0, 1.0))


def design_effect(clusters: ArrayLike, icc: float) -> float:
    sizes = pd.Series(np.asarray(clusters)).value_counts().to_numpy(dtype=float)
    m_bar = sizes.mean()
    cv2 = sizes.var(ddof=0) / m_bar**2 if m_bar > 0 else 0.0
    return float(1.0 + ((cv2 + 1.0) * m_bar - 1.0) * icc)


def effective_sample_size(values: ArrayLike, clusters: ArrayLike) -> float:
    """ESS of ``values`` (e.g. labels or calibration residuals) clustered by ``clusters``."""
    values = np.asarray(values, dtype=float)
    icc = icc_oneway(values, clusters)
    return float(len(values) / design_effect(clusters, icc))
