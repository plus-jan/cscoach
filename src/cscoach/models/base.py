"""Common interface for all probabilistic models (WP, xK, ...)."""

from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray


class ProbabilisticModel(ABC):
    """Binary probabilistic model. ``predict_proba`` returns P(y=1) as a 1-D array."""

    name: str = "model"

    @abstractmethod
    def fit(self, df: pd.DataFrame, y: pd.Series, **kwargs: Any) -> ProbabilisticModel: ...

    @abstractmethod
    def predict_proba(self, df: pd.DataFrame) -> NDArray[np.float64]: ...

    def card(self) -> dict[str, Any]:
        """Model card: config, training data summary, metrics. Extend in subclasses."""
        return {"name": self.name, "class": type(self).__name__}

    def save(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / "model.pkl").open("wb") as f:
            pickle.dump(self, f)
        (out_dir / "card.json").write_text(json.dumps(self.card(), indent=2, default=str))

    @staticmethod
    def load(model_dir: Path) -> ProbabilisticModel:
        with (model_dir / "model.pkl").open("rb") as f:
            model = pickle.load(f)  # noqa: S301 — only load artefacts you produced
        if not isinstance(model, ProbabilisticModel):
            raise TypeError(f"{model_dir} does not contain a ProbabilisticModel")
        return model
