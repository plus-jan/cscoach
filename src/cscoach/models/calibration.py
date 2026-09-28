"""WP calibration layer (M3.3; docs/specs/03 WP model 3, docs/specs/04 §7 "Per-tier calibration", A-28).

A global calibrator plus one per group (``by``: a column or a list of columns; missing values form the group
"null") with ≥ ``min_rows_per_group`` rows; other groups use the global one. Each calibrator is isotonic regression
if its rows ≥ ``isotonic_min_rows``, else Platt (logistic regression on logit p) — ``method: auto``; ``isotonic``,
``platt`` and ``none`` (identity) force a method. Outputs are clipped to [EPS, 1 − EPS]. The deployed calibrator is
fitted on the calibration fold only; ``crossfit`` gives out-of-fold calibrated predictions on the training folds for
the loop (docs/specs/07 §2). Data provided by PureSkill.gg.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

EPS = 1e-6


def _logit(p):
    p = np.clip(np.asarray(p, dtype="float64"), EPS, 1 - EPS)
    return np.log(p / (1 - p))


class _One:
    def __init__(self, method: str, params: dict | None = None):
        self.method, self.params = method, params or {}

    @classmethod
    def fit(cls, p, y, method: str) -> "_One":
        p, y = np.asarray(p, dtype="float64"), np.asarray(y, dtype="float64")
        if method == "none":
            return cls("none")
        if method == "isotonic":
            iso = IsotonicRegression(y_min=EPS, y_max=1 - EPS, out_of_bounds="clip").fit(p, y)
            return cls("isotonic", {"x": iso.X_thresholds_.tolist(), "y": iso.y_thresholds_.tolist()})
        if method == "platt":
            lr = LogisticRegression(C=1e6, max_iter=1000).fit(_logit(p).reshape(-1, 1), y)
            return cls("platt", {"a": float(lr.coef_[0, 0]), "b": float(lr.intercept_[0])})
        raise ValueError(f"unknown calibration method {method!r}")

    def predict(self, p) -> np.ndarray:
        p = np.asarray(p, dtype="float64")
        if self.method == "isotonic":
            q = np.interp(p, self.params["x"], self.params["y"])
        elif self.method == "platt":
            q = 1 / (1 + np.exp(-(self.params["a"] * _logit(p) + self.params["b"])))
        else:
            q = p
        return np.clip(q, EPS, 1 - EPS)


class Calibrator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.global_: _One | None = None
        self.groups_: dict[str, _One] = {}

    def _by(self) -> list[str]:
        by = self.cfg.get("by")
        return [] if not by else [by] if isinstance(by, str) else list(by)

    def keys(self, frame: pd.DataFrame | None) -> np.ndarray | None:
        by = self._by()
        if not by or frame is None:
            return None
        parts = [frame[c].astype("string").fillna("null").to_numpy(dtype=object) for c in by]
        return parts[0] if len(parts) == 1 else np.array(["|".join(v) for v in zip(*parts)], dtype=object)

    def _method(self, n: int) -> str:
        m = self.cfg.get("method", "auto")
        if m != "auto":
            return m
        return "isotonic" if n >= self.cfg["isotonic_min_rows"] else "platt"

    def fit(self, p, y, frame: pd.DataFrame | None = None) -> "Calibrator":
        p, y = np.asarray(p, dtype="float64"), np.asarray(y, dtype="float64")
        self.global_ = _One.fit(p, y, self._method(len(p)))
        self.groups_ = {}
        keys = self.keys(frame)
        if keys is not None and self.cfg.get("method", "auto") != "none":
            for k in pd.unique(keys):
                idx = keys == k
                if idx.sum() >= self.cfg["min_rows_per_group"]:
                    self.groups_[str(k)] = _One.fit(p[idx], y[idx], self._method(int(idx.sum())))
        return self

    def predict(self, p, frame: pd.DataFrame | None = None) -> np.ndarray:
        p = np.asarray(p, dtype="float64")
        q = self.global_.predict(p)
        keys = self.keys(frame)
        if keys is not None:
            for k, c in self.groups_.items():
                idx = keys == k
                if idx.any():
                    q[idx] = c.predict(p[idx])
        return q

    def to_dict(self) -> dict:
        one = lambda c: {"method": c.method, "params": c.params}  # noqa: E731
        return {"cfg": self.cfg, "global": one(self.global_), "groups": {k: one(c) for k, c in self.groups_.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> "Calibrator":
        cal = cls(d["cfg"])
        cal.global_ = _One(d["global"]["method"], d["global"]["params"])
        cal.groups_ = {k: _One(v["method"], v["params"]) for k, v in d["groups"].items()}
        return cal


def crossfit(frame: pd.DataFrame, cfg: dict) -> np.ndarray:
    """Out-of-fold calibrated predictions: fold k is calibrated by a calibrator fitted on the other folds."""
    q = np.empty(len(frame), dtype="float64")
    folds = frame["fold"].to_numpy()
    for k in sorted(pd.unique(folds)):
        fit, pred = folds != k, folds == k
        cal = Calibrator(cfg).fit(frame["p"].to_numpy()[fit], frame["y"].to_numpy()[fit], frame[fit])
        q[pred] = cal.predict(frame["p"].to_numpy()[pred], frame[pred])
    return q
