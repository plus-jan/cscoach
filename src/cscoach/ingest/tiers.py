"""Map source-specific rank labels to canonical tiers (configs/tiers.yaml). M1.3."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np

from cscoach.config import load_config


class TierMapper:
    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        self.cfg = cfg or load_config("tiers")
        self.order = {t["id"]: t["order"] for t in self.cfg["tiers"]}

    def from_faceit_level(self, level: int | None) -> str | None:
        if level is None:
            return None
        return self.cfg["mappings"]["faceit_level"].get(int(level))

    def _from_ranges(self, key: str, value: float | None) -> str | None:
        if value is None:
            return None
        for lo, hi, tier in self.cfg["mappings"][key]:
            if lo <= value < hi:
                return str(tier)
        return None

    def from_premier_rating(self, rating: float | None) -> str | None:
        return self._from_ranges("premier_rating", rating)

    def from_mm_skill_group(self, group: int | None) -> str | None:
        return self._from_ranges("mm_skill_group", group)

    def match_tier(self, player_tiers: Iterable[str | None]) -> str | None:
        """Aggregate player tiers into one match tier per ``match_tier_rule``; else None."""
        known = [self.order[t] for t in player_tiers if t is not None]
        if len(known) < self.cfg.get("min_known_players", 6):
            return None
        rule = self.cfg.get("match_tier_rule", "median_of_players")
        if rule == "min":
            val = min(known)
        elif rule == "mean_order":
            val = int(round(float(np.mean(known))))
        else:
            val = int(np.floor(np.median(known)))
        inv = {v: k for k, v in self.order.items()}
        return inv[val]
