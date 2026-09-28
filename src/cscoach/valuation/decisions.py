"""xK × WPA decision-quality matrix (M5.4). Research question E."""

from __future__ import annotations

import pandas as pd


def flag_risky_duels(
    duels: pd.DataFrame,
    xk_col: str = "xk",
    wp_if_avoid_col: str = "wp_if_avoid",
    max_xk: float = 0.30,
    min_safe_wp: float = 0.85,
) -> pd.DataFrame:
    """Flag duels taken with low win chance when avoiding them kept the round safe.

    Requires ``wp_if_avoid`` = team WP had the player not engaged (counterfactual state
    without the duel, M9.2). Returns ``duels`` with boolean column ``risky_duel`` and
    ``decision_cost`` = wp_if_avoid - E[WP | duel taken].
    """
    raise NotImplementedError("M5.4: needs xK model (M4.3) and counterfactual WP (M9.2)")
