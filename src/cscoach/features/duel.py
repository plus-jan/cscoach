"""Duel extraction and pre-duel features for xK (M4.1, M4.2)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray


def view_offset_deg(
    shooter_xyz: ArrayLike, yaw_deg: ArrayLike, pitch_deg: ArrayLike, target_xyz: ArrayLike
) -> NDArray[np.float64]:
    """Angle (degrees) between the shooter's view direction and the direction to target.

    Proxy for crosshair placement. Source engine: yaw around z, pitch positive = down.
    """
    s = np.atleast_2d(np.asarray(shooter_xyz, float))
    t = np.atleast_2d(np.asarray(target_xyz, float))
    yaw = np.radians(np.asarray(yaw_deg, float))
    pitch = np.radians(np.asarray(pitch_deg, float))
    view = np.stack(
        [np.cos(pitch) * np.cos(yaw), np.cos(pitch) * np.sin(yaw), -np.sin(pitch)], axis=-1
    )
    d = t - s
    d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    cos = np.clip(np.sum(np.atleast_2d(view) * d, axis=-1), -1.0, 1.0)
    return np.asarray(np.degrees(np.arccos(cos)), dtype=float)


def extract_duels(
    kills: pd.DataFrame, damages: pd.DataFrame, ticks: pd.DataFrame, window_s: float
) -> pd.DataFrame:
    """Build the ``duels`` table (schemas.tables.DUELS) with pre-duel features."""
    raise NotImplementedError("M4.1/M4.2: duel extraction + pre-duel features")
