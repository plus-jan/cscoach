"""Buy classification and team economic synchronisation (M6.2, M6.3)."""

from __future__ import annotations

import pandas as pd

BUY_CLASSES = ("eco", "force", "half", "full")


def classify_buy(equip_value: float, thresholds: tuple[int, int, int] = (1500, 3000, 4000)) -> str:
    """Per-player buy class from freeze-end equipment value. Thresholds to be tuned (M6.2)."""
    eco, force, full = thresholds
    if equip_value < eco:
        return "eco"
    if equip_value < force:
        return "force"
    if equip_value < full:
        return "half"
    return "full"


def team_sync(buys: pd.DataFrame) -> pd.DataFrame:
    """Per team-round: modal buy class, number of players deviating, money spread."""
    raise NotImplementedError("M6.3: team economic synchronisation metric")


def counterfactual_buy_value(state: pd.DataFrame, alternative_equipment: pd.Series) -> float:
    """Two-round expected WP under an alternative buy (see docs/specs/03_models.md#economy)."""
    raise NotImplementedError("M6.3: counterfactual buy evaluation via WP + rules engine")
