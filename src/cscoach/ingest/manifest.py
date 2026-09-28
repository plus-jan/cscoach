"""Data manifest: one row per match, idempotent ingestion (M1.4)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def update_manifest(manifest_path: Path, rows: pd.DataFrame) -> pd.DataFrame:
    """Upsert rows by ``match_id``; validate with schemas.tables.MANIFEST."""
    raise NotImplementedError("M1.4: manifest upsert + dedup")
