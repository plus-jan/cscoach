"""Probabilistic scoring and calibration metrics.

All functions take binary labels ``y`` in {0, 1} and predicted probabilities ``p``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.metrics import roc_auc_score

EPS = 1e-12


def _arr(y: ArrayLike, p: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    y_arr = np.asarray(y, dtype=float).ravel()
    p_arr = np.asarray(p, dtype=float).ravel()
    if y_arr.shape != p_arr.shape:
        raise ValueError(f"shape mismatch {y_arr.shape} vs {p_arr.shape}")
    if len(y_arr) == 0:
        raise ValueError("empty input")
    if np.any((p_arr < 0) | (p_arr > 1)):
        raise ValueError("probabilities must be in [0, 1]")
    return y_arr, p_arr


def brier_score(y: ArrayLike, p: ArrayLike) -> float:
    y_arr, p_arr = _arr(y, p)
    return float(np.mean((p_arr - y_arr) ** 2))


def log_loss(y: ArrayLike, p: ArrayLike) -> float:
    y_arr, p_arr = _arr(y, p)
    p_arr = np.clip(p_arr, EPS, 1 - EPS)
    return float(-np.mean(y_arr * np.log(p_arr) + (1 - y_arr) * np.log(1 - p_arr)))


def brier_skill_score(y: ArrayLike, p: ArrayLike, p_ref: ArrayLike) -> float:
    """1 - Brier(p) / Brier(p_ref). > 0 means ``p`` beats the reference."""
    ref = brier_score(y, p_ref)
    return float(1.0 - brier_score(y, p) / ref) if ref > 0 else 0.0


def auc(y: ArrayLike, p: ArrayLike) -> float:
    y_arr, p_arr = _arr(y, p)
    if len(np.unique(y_arr)) < 2:
        return float("nan")
    return float(roc_auc_score(y_arr, p_arr))


@dataclass(frozen=True)
class ReliabilityCurve:
    bin_lower: NDArray[np.float64]
    bin_upper: NDArray[np.float64]
    mean_pred: NDArray[np.float64]
    frac_pos: NDArray[np.float64]
    count: NDArray[np.int64]


def _bin_edges(p: NDArray[np.float64], n_bins: int, strategy: str) -> NDArray[np.float64]:
    if strategy == "uniform":
        return np.linspace(0.0, 1.0, n_bins + 1)
    if strategy == "quantile":
        edges = np.unique(np.quantile(p, np.linspace(0, 1, n_bins + 1)))
        edges[0], edges[-1] = 0.0, 1.0
        return edges
    raise ValueError(f"unknown strategy {strategy!r}")


def reliability_curve(
    y: ArrayLike, p: ArrayLike, n_bins: int = 15, strategy: str = "quantile"
) -> ReliabilityCurve:
    """Binned mean prediction vs observed frequency (empty bins dropped)."""
    y_arr, p_arr = _arr(y, p)
    edges = _bin_edges(p_arr, n_bins, strategy)
    idx = np.clip(np.searchsorted(edges, p_arr, side="right") - 1, 0, len(edges) - 2)
    counts = np.bincount(idx, minlength=len(edges) - 1)
    sum_p = np.bincount(idx, weights=p_arr, minlength=len(edges) - 1)
    sum_y = np.bincount(idx, weights=y_arr, minlength=len(edges) - 1)
    keep = counts > 0
    return ReliabilityCurve(
        bin_lower=edges[:-1][keep],
        bin_upper=edges[1:][keep],
        mean_pred=sum_p[keep] / counts[keep],
        frac_pos=sum_y[keep] / counts[keep],
        count=counts[keep].astype(np.int64),
    )


def expected_calibration_error(
    y: ArrayLike, p: ArrayLike, n_bins: int = 15, strategy: str = "quantile"
) -> float:
    """Count-weighted mean |observed - predicted| over bins."""
    rc = reliability_curve(y, p, n_bins, strategy)
    w = rc.count / rc.count.sum()
    return float(np.sum(w * np.abs(rc.frac_pos - rc.mean_pred)))


def max_calibration_error(
    y: ArrayLike, p: ArrayLike, n_bins: int = 15, strategy: str = "quantile"
) -> float:
    rc = reliability_curve(y, p, n_bins, strategy)
    return float(np.max(np.abs(rc.frac_pos - rc.mean_pred)))


def score_all(y: ArrayLike, p: ArrayLike, n_bins: int = 15) -> dict[str, float]:
    """Standard metric bundle used in reports."""
    return {
        "n": float(len(np.asarray(y))),
        "brier": brier_score(y, p),
        "log_loss": log_loss(y, p),
        "ece": expected_calibration_error(y, p, n_bins),
        "mce": max_calibration_error(y, p, n_bins),
        "auc": auc(y, p),
        "base_rate": float(np.mean(np.asarray(y, dtype=float))),
    }
