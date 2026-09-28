"""Mistake detectors (M9.1). Each returns candidate feedback rows with evidence.

Output columns: match_id, steamid, round_num, tick, category, evidence (dict).
Categories: risky_duel, untraded_death, desync_buy, utility_waste, late_rotation.
"""

from __future__ import annotations

import pandas as pd


def detect_all(match_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    raise NotImplementedError("M9.1: run all detectors and concatenate candidates")
