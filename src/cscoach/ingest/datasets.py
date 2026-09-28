"""Loaders for external datasets (M1.2). Each returns contract-conformant tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_pureskill(root: Path) -> dict[str, pd.DataFrame]:
    """Load the PureSkill.gg CS2 dataset from ``data/external/pureskill``.

    Must return at least: ``manifest`` (with tier via ingest.tiers), ``rounds``,
    ``player_ticks`` or equivalent, ``kills``, ``damages``. Inspect the dataset's actual
    file layout first and document it in data/README.md.
    """
    raise NotImplementedError("M1.2: PureSkill dataset loader")
