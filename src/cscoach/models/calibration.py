"""Post-hoc probability calibration, optionally per skill tier (ADR-0002)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

_EPS = 1e-6


class _Platt:
    def __init__(self) -> None:
        self.lr = LogisticRegression(C=1e6, max_iter=1000)

    def fit(self, p: NDArray[np.float64], y: NDArray[np.float64]) -> _Platt:
        self.lr.fit(_logit(p)[:, None], y.astype(int))
        return self

    def predict(self, p: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.asarray(self.lr.predict_proba(_logit(p)[:, None])[:, 1], dtype=float)


class _Isotonic:
    def __init__(self) -> None:
        self.iso = IsotonicRegression(y_min=_EPS, y_max=1 - _EPS, out_of_bounds="clip")

    def fit(self, p: NDArray[np.float64], y: NDArray[np.float64]) -> _Isotonic:
        self.iso.fit(p, y)
        return self

    def predict(self, p: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.asarray(self.iso.predict(p), dtype=float)


def _logit(p: NDArray[np.float64]) -> NDArray[np.float64]:
    p = np.clip(p, _EPS, 1 - _EPS)
    return np.asarray(np.log(p / (1 - p)), dtype=float)


def _make(method: str, n: int, isotonic_min_rows: int) -> _Platt | _Isotonic:
    if method == "isotonic" or (method == "auto" and n >= isotonic_min_rows):
        return _Isotonic()
    if method in ("platt", "auto"):
        return _Platt()
    raise ValueError(f"unknown calibration method {method!r}")


class TierCalibrator:
    """Global calibrator plus one per tier (tiers with too few rows use the global one).

    Must be fitted on a *calibration fold* of matches disjoint from training and test.
    """

    def __init__(
        self, method: str = "auto", isotonic_min_rows: int = 5000, min_rows_per_tier: int = 1000
    ) -> None:
        self.method = method
        self.isotonic_min_rows = isotonic_min_rows
        self.min_rows_per_tier = min_rows_per_tier
        self.global_: _Platt | _Isotonic | None = None
        self.per_tier: dict[str, _Platt | _Isotonic] = {}

    def fit(self, p: ArrayLike, y: ArrayLike, tiers: ArrayLike | None = None) -> TierCalibrator:
        p_arr, y_arr = np.asarray(p, float), np.asarray(y, float)
        self.global_ = _make(self.method, len(p_arr), self.isotonic_min_rows).fit(p_arr, y_arr)
        self.per_tier = {}
        if tiers is not None:
            t = pd.Series(np.asarray(tiers, dtype=object)).fillna("__na__").to_numpy()
            for tier in np.unique(t):
                m = t == tier
                if m.sum() >= self.min_rows_per_tier and len(np.unique(y_arr[m])) == 2:
                    cal = _make(self.method, int(m.sum()), self.isotonic_min_rows)
                    self.per_tier[str(tier)] = cal.fit(p_arr[m], y_arr[m])
        return self

    def transform(self, p: ArrayLike, tiers: ArrayLike | None = None) -> NDArray[np.float64]:
        if self.global_ is None:
            raise RuntimeError("calibrator not fitted")
        p_arr = np.asarray(p, float)
        out = self.global_.predict(p_arr)
        if tiers is not None and self.per_tier:
            t = pd.Series(np.asarray(tiers, dtype=object)).fillna("__na__").to_numpy()
            for tier, cal in self.per_tier.items():
                m = t == tier
                if m.any():
                    out[m] = cal.predict(p_arr[m])
        return out

    def summary(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "global": type(self.global_).__name__,
            "per_tier": {k: type(v).__name__ for k, v in self.per_tier.items()},
        }
