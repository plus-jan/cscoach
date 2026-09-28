"""Round segmentation from parsed events (M2.1)."""

from __future__ import annotations

import pandas as pd

from cscoach.ingest.demo_parser import ParsedDemo


def segment_rounds(demo: ParsedDemo) -> pd.DataFrame:
    """Return the ``rounds`` table (schemas.tables.ROUNDS).

    Must handle: warmup, knife rounds, restarts (mp_restartgame), overtime, side swaps,
    technical pauses. Verify winners against final score on real demos.
    """
    raise NotImplementedError("M2.1: round segmentation")
