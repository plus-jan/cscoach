"""Snapshot sampling: event-anchored + fixed cadence (M2.2)."""

from __future__ import annotations

import pandas as pd


def sample_snapshot_ticks(
    rounds: pd.DataFrame, events: dict[str, pd.DataFrame], tick_rate: float, cadence_s: float = 1.0
) -> pd.DataFrame:
    """Return (match_id, round_num, tick) rows between freeze_end_tick and end_tick
    (exclusive of end_tick) at every event tick and every ``cadence_s`` seconds."""
    raise NotImplementedError("M2.2: snapshot sampler")
