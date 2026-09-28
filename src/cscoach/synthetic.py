"""Synthetic CS-like round simulator for tests and pipeline development.

Rounds are sequences of kill events between CT and T. Each kill is won by CT with
probability ``sigmoid(skill_diff + a * (alive_ct - alive_t) * discipline + b * bomb_planted)``,
where ``discipline`` depends on the tier: low tiers convert man-advantage worse
(the "chaos factor" from research question A/C). A snapshot is emitted before each kill,
so snapshots are clustered within rounds exactly like real data.

The ground-truth WP of a state is *not* analytic, which is the point: models must learn
it, and calibration must hold on held-out matches.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TIER_DISCIPLINE = {"low": 0.25, "mid": 0.45, "high": 0.65, "semipro": 0.8, "pro": 1.0}
MAPS = ("de_mirage", "de_inferno", "de_nuke", "de_ancient", "de_anubis")
ROUND_TIME_S = 115.0
BOMB_TIME_S = 40.0


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def simulate_matches(
    n_matches: int = 200,
    rounds_per_match: int = 20,
    tiers: tuple[str, ...] = ("low", "mid", "high", "semipro"),
    seed: int = 0,
) -> pd.DataFrame:
    """Return a snapshot table with state features, ``y_ct_win`` and grouping columns."""
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for m in range(n_matches):
        match_id = f"m{m:05d}"
        tier = tiers[m % len(tiers)]
        map_name = MAPS[rng.integers(len(MAPS))]
        disc = TIER_DISCIPLINE[tier]
        team_skill = rng.normal(0, 0.3)
        for r in range(1, rounds_per_match + 1):
            rows.extend(_simulate_round(rng, match_id, r, tier, map_name, disc, team_skill))
    return pd.DataFrame(rows)


def _simulate_round(
    rng: np.random.Generator,
    match_id: str,
    round_num: int,
    tier: str,
    map_name: str,
    disc: float,
    team_skill: float,
) -> list[dict[str, object]]:
    alive = {"CT": 5, "T": 5}
    hp = {"CT": 500.0, "T": 500.0}
    equip_ct = float(rng.choice([1000, 3000, 4500, 5500]) * 5)
    equip_t = float(rng.choice([1000, 3000, 4000, 5000]) * 5)
    equip_edge = (equip_ct - equip_t) / 10000.0
    t, planted, plant_t = 0.0, False, 0.0
    snaps: list[dict[str, object]] = []
    tick = 0
    winner: str | None = None
    while winner is None:
        t += float(rng.exponential(8.0))
        tick = int(t * 64)
        if not planted and alive["T"] > 0 and t > 30 and rng.random() < 0.08 * alive["T"]:
            planted, plant_t = True, t
        remaining = (BOMB_TIME_S - (t - plant_t)) if planted else (ROUND_TIME_S - t)
        if remaining <= 0:
            winner = "T" if planted else "CT"
            break
        snaps.append(
            {
                "match_id": match_id,
                "round_num": round_num,
                "round_uid": f"{match_id}:{round_num}",
                "tick": tick,
                "tier": tier,
                "map_name": map_name,
                "alive_ct": alive["CT"],
                "alive_t": alive["T"],
                "hp_sum_ct": hp["CT"],
                "hp_sum_t": hp["T"],
                "armor_sum_ct": 100.0 * alive["CT"],
                "armor_sum_t": 100.0 * alive["T"],
                "equip_value_ct": equip_ct * alive["CT"] / 5,
                "equip_value_t": equip_t * alive["T"] / 5,
                "n_kits_ct": min(alive["CT"], 2),
                "bomb_planted": int(planted),
                "time_remaining_s": remaining,
                "man_advantage": alive["CT"] - alive["T"],
            }
        )
        logit = (
            team_skill
            + equip_edge
            + 0.6 * disc * (alive["CT"] - alive["T"])
            - (0.5 if planted else 0.0)
            + rng.normal(0, 1.0 - disc)  # chaos
        )
        loser = "T" if rng.random() < _sigmoid(logit) else "CT"
        alive[loser] -= 1
        hp[loser] = max(0.0, hp[loser] - 100.0)
        other = "CT" if loser == "T" else "T"
        hp[other] = max(1.0 * alive[other], hp[other] - float(rng.uniform(0, 60)))
        if alive["T"] == 0 and not planted:
            winner = "CT"
        elif alive["CT"] == 0:
            winner = "T"
        elif alive["T"] == 0 and planted:
            # CT must defuse: succeeds if enough time
            winner = "CT" if rng.random() < min(1.0, remaining / 10.0) else "T"
    y = 1 if winner == "CT" else 0
    for s in snaps:
        s["y_ct_win"] = y
    return snaps
