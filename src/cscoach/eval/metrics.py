"""Probabilistic metrics exactly as specified in docs/specs/04 §7."""
from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-12


def brier(p, y) -> float:
    p, y = np.asarray(p, float), np.asarray(y, float)
    return float(np.mean((p - y) ** 2))


def logloss(p, y) -> float:
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def logloss_rows(p, y) -> np.ndarray:
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def reliability(p, y, n_bins: int = 15) -> pd.DataFrame:
    """Quantile bins; edges made unique with the first/last edge set to 0 and 1; empty bins dropped."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    edges = np.unique(np.quantile(p, np.linspace(0, 1, n_bins + 1)))
    edges[0], edges[-1] = 0.0, 1.0
    if len(edges) < 2:
        edges = np.array([0.0, 1.0])
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, len(edges) - 2)
    df = pd.DataFrame({"bin": idx, "p": p, "y": y})
    out = df.groupby("bin").agg(mean_p=("p", "mean"), mean_y=("y", "mean"), count=("p", "size")).reset_index()
    return out[out["count"] > 0].reset_index(drop=True)


def ece(p, y, n_bins: int = 15) -> float:
    rel = reliability(p, y, n_bins)
    return float((rel["count"] / rel["count"].sum() * (rel["mean_y"] - rel["mean_p"]).abs()).sum())
