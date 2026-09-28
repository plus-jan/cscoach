"""GBDT round win-probability model (LightGBM) with monotone constraints and
per-tier calibration. Config: configs/model_wp.yaml. Spec: docs/specs/03_models.md.
"""

from __future__ import annotations

from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
from numpy.typing import NDArray

from cscoach.models.base import ProbabilisticModel
from cscoach.models.calibration import TierCalibrator
from cscoach.schemas.tables import LEAKY_COLUMNS


class GBDTWinProbability(ProbabilisticModel):
    name = "wp_gbdt"

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        feats = cfg["features"]
        self.numeric: list[str] = list(feats["numeric"])
        self.categorical: list[str] = list(feats.get("categorical", []))
        leaky = LEAKY_COLUMNS.intersection(self.features)
        if leaky:
            raise ValueError(f"leaky feature(s) in config: {sorted(leaky)}")
        self.booster: lgb.LGBMClassifier | None = None
        self.calibrator: TierCalibrator | None = None
        self.categories_: dict[str, list[str]] = {}
        self.best_iteration_: int | None = None

    @property
    def features(self) -> list[str]:
        return self.numeric + self.categorical

    def _X(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        X = df[self.features].copy()
        for c in self.numeric:
            X[c] = X[c].astype(float)
        for c in self.categorical:
            if fit:
                self.categories_[c] = sorted(map(str, X[c].dropna().unique()))
            X[c] = pd.Categorical(X[c].astype("string"), categories=self.categories_[c])
        return X

    def fit(
        self,
        df: pd.DataFrame,
        y: pd.Series,
        *,
        valid: tuple[pd.DataFrame, pd.Series] | None = None,
        calibration: tuple[pd.DataFrame, pd.Series] | None = None,
        **kwargs: Any,
    ) -> GBDTWinProbability:
        """Fit on ``df``; ``valid`` (grouped!) enables early stopping; ``calibration``
        (a disjoint match fold) fits the per-tier calibrator."""
        params = dict(self.cfg.get("lightgbm", {}))
        es_rounds = params.pop("early_stopping_rounds", None)
        mono = self.cfg.get("monotone", {})
        params["monotone_constraints"] = [int(mono.get(f, 0)) for f in self.features]
        params.setdefault("verbose", -1)
        self.booster = lgb.LGBMClassifier(objective="binary", **params)
        X = self._X(df, fit=True)
        fit_kwargs: dict[str, Any] = {"categorical_feature": self.categorical or "auto"}
        if valid is not None:
            fit_kwargs["eval_set"] = [(self._X(valid[0]), valid[1].astype(int))]
            if es_rounds:
                fit_kwargs["callbacks"] = [lgb.early_stopping(es_rounds, verbose=False)]
        self.booster.fit(X, y.astype(int), **fit_kwargs)
        self.best_iteration_ = getattr(self.booster, "best_iteration_", None)
        if calibration is not None:
            ccfg = self.cfg.get("calibration", {})
            tier_col = self.cfg.get("tier_col", "tier")
            cdf, cy = calibration
            self.calibrator = TierCalibrator(
                method=ccfg.get("method", "auto"),
                isotonic_min_rows=ccfg.get("isotonic_min_rows", 5000),
            ).fit(
                self.predict_raw(cdf),
                cy,
                cdf[tier_col] if ccfg.get("per_tier", True) and tier_col in cdf else None,
            )
        return self

    def predict_raw(self, df: pd.DataFrame) -> NDArray[np.float64]:
        if self.booster is None:
            raise RuntimeError("model not fitted")
        proba = np.asarray(self.booster.predict_proba(self._X(df)), dtype=float)
        return proba[:, 1]

    def predict_proba(self, df: pd.DataFrame) -> NDArray[np.float64]:
        p = self.predict_raw(df)
        if self.calibrator is None:
            return p
        tier_col = self.cfg.get("tier_col", "tier")
        return self.calibrator.transform(p, df.get(tier_col))

    def card(self) -> dict[str, Any]:
        return {
            **super().card(),
            "config": self.cfg,
            "best_iteration": self.best_iteration_,
            "calibration": self.calibrator.summary() if self.calibrator else None,
        }
