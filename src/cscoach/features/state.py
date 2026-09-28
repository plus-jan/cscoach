"""State features for the WP model (M2.3). Spec: docs/specs/03_models.md.

Input: player-level snapshot rows (one row per match_id, round_num, tick, steamid) with
columns side, is_alive, health, armor, has_helmet, has_defuser, equipment_value.
Only data at or before ``tick`` may be used.
"""

from __future__ import annotations

import pandas as pd

KEYS = ["match_id", "round_num", "tick"]


def aggregate_team_state(players: pd.DataFrame) -> pd.DataFrame:
    """Aggregate player rows into per-snapshot team features (CT/T suffixes)."""
    p = players.copy()
    alive = p["is_alive"].astype(bool)
    p["alive"] = alive.astype(int)
    p["hp"] = p["health"].where(alive, 0).astype(float)
    p["armor_v"] = p["armor"].where(alive, 0).astype(float)
    p["helmet"] = (p["has_helmet"].astype(bool) & alive).astype(int)
    p["kit"] = (p["has_defuser"].astype(bool) & alive).astype(int)
    p["equip"] = p["equipment_value"].where(alive, 0).astype(float)
    agg = p.groupby([*KEYS, "side"]).agg(
        alive=("alive", "sum"),
        hp_sum=("hp", "sum"),
        armor_sum=("armor_v", "sum"),
        helmets=("helmet", "sum"),
        kits=("kit", "sum"),
        equip_value=("equip", "sum"),
    )
    wide: pd.DataFrame = agg.unstack("side", fill_value=0)  # type: ignore[assignment]
    wide.columns = [f"{c[0]}_{str(c[1]).lower()}" for c in wide.columns]
    for col in ["alive_ct", "alive_t", "hp_sum_ct", "hp_sum_t", "kits_ct"]:
        if col not in wide:
            wide[col] = 0
    wide = wide.rename(columns={"kits_ct": "n_kits_ct"}).drop(columns=["kits_t"], errors="ignore")
    wide["man_advantage"] = wide["alive_ct"] - wide["alive_t"]
    return wide.reset_index()


def time_remaining(
    round_time_s: pd.Series,
    bomb_planted: pd.Series,
    plant_time_s: pd.Series,
    round_length_s: float = 115.0,
    bomb_timer_s: float = 40.0,
) -> pd.Series:
    """Seconds until the round ends by timer: round clock pre-plant, bomb clock post-plant.

    Round/bomb lengths must come from game settings (verify in M2.3; CS2 defaults 1:55 / 40 s).
    """
    pre = round_length_s - round_time_s
    post = bomb_timer_s - (round_time_s - plant_time_s)
    return pre.where(~bomb_planted.astype(bool), post).clip(lower=0.0)
