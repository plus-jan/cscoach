"""Expected-kills (duel) model. Spec: docs/specs/03_models.md#xk. Tasks M4.x."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from cscoach.models.base import ProbabilisticModel


class ExpectedKillsModel(ProbabilisticModel):
    """P(p1 wins the duel | pre-duel state). Implement like GBDTWinProbability
    (LightGBM + calibration by tier), config in configs/model_xk.yaml."""

    name = "xk_gbdt"

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg

    def fit(self, df: pd.DataFrame, y: pd.Series, **kwargs: Any) -> ExpectedKillsModel:
        raise NotImplementedError("M4.3: train xK model with grouped early stopping + calibration")

    def predict_proba(self, df: pd.DataFrame) -> NDArray[np.float64]:
        raise NotImplementedError("M4.3: predict duel win probability for p1")
