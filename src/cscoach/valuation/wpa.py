"""Win Probability Added per event. Spec: docs/specs/03_models.md#wpa."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cscoach.config import load_config


def event_wpa(
    events: pd.DataFrame,
    wp_before_col: str = "wp_ct_before",
    wp_after_col: str = "wp_ct_after",
    side_col: str = "team_side",
) -> pd.DataFrame:
    """Add ``wp_before``, ``wp_after`` and ``wpa`` from the acting team's perspective.

    ``events`` holds CT-perspective WP evaluated just before/after each event (M5.1 wires
    this to the WP model via snapshots at ``tick - pre_ticks`` / ``tick + post_ticks``).
    """
    is_ct = events[side_col].eq("CT").to_numpy()
    before = np.where(is_ct, events[wp_before_col], 1 - events[wp_before_col])
    after = np.where(is_ct, events[wp_after_col], 1 - events[wp_after_col])
    return events.assign(wp_before=before, wp_after=after, wpa=after - before)


def attribute_kill_credit(
    wpa: float,
    killer: str,
    assister: str | None = None,
    flash_assister: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Split a kill's team WPA across roles per configs/valuation.yaml (M5.2 refines).

    Shares of absent roles go to ``redistribute_missing_to``. Credits sum to ``wpa``.
    """
    vcfg = cfg or load_config("valuation")
    shares: dict[str, float] = dict(vcfg["attribution"]["kill"])
    fallback = vcfg["attribution"].get("redistribute_missing_to", "killer")
    who = {"killer": killer, "assister": assister, "flash_assister": flash_assister}
    credit: dict[str, float] = {}
    for role, share in shares.items():
        player = who.get(role) or who[fallback]
        assert player is not None
        credit[player] = credit.get(player, 0.0) + share * wpa
    return credit
