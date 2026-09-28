"""Reference WP model: logistic regression on the classic state variables.

Every WP challenger must beat this on held-out matches (docs/specs/04 §3).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from cscoach.models.base import ProbabilisticModel

BASE_COLS = ["alive_ct", "alive_t", "hp_sum_ct", "hp_sum_t", "bomb_planted", "time_remaining_s"]


def _design(df: pd.DataFrame) -> pd.DataFrame:
    X = df[BASE_COLS].astype(float).copy()
    X["alive_diff_x_planted"] = (df["alive_ct"] - df["alive_t"]) * df["bomb_planted"]
    X["time_x_planted"] = df["time_remaining_s"] * df["bomb_planted"]
    return X


class BaselineWinProbability(ProbabilisticModel):
    name = "wp_baseline_logit"

    def __init__(self, C: float = 1.0) -> None:
        self.C = C
        self.pipeline: Pipeline | None = None

    def fit(self, df: pd.DataFrame, y: pd.Series, **kwargs: Any) -> BaselineWinProbability:
        self.pipeline = make_pipeline(StandardScaler(), LogisticRegression(C=self.C, max_iter=1000))
        self.pipeline.fit(_design(df), y.astype(int))
        return self

    def predict_proba(self, df: pd.DataFrame) -> NDArray[np.float64]:
        if self.pipeline is None:
            raise RuntimeError("model not fitted")
        return np.asarray(self.pipeline.predict_proba(_design(df))[:, 1], dtype=float)
