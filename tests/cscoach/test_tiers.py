"""Tests for rank decoding and match tiers (M1.4). Synthetic frames: code behaviour only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.data.tiers import decode_players, match_tier, to_tier

CFG = {
    "tier_cutoffs": {
        # upper bounds (exclusive) per tier index 0..2; values >= last bound → index 3 (semipro)
        "premier": [10000, 15000, 20000],
        "competitive": [7, 13, 17],
        "faceit": [4, 7, 10],
    },
    "tiers": ["low", "mid", "high", "semipro"],
    "min_known_players": 6,
    "premier_min_rating": 19,
}


def pi(ranks, rank_type=None, rank_platform=None, rounds=1):
    rows = []
    for r in range(1, rounds + 1):
        for i, rank in enumerate(ranks):
            rows.append({
                "round": r, "player_id_fixed": i, "rank": rank,
                "rank_type": rank_type, "rank_platform": (rank_platform[i] if rank_platform else 0.0),
            })
    return pd.DataFrame(rows)


def test_to_tier_boundaries():
    assert to_tier(9999, "premier", CFG) == "low"
    assert to_tier(10000, "premier", CFG) == "mid"
    assert to_tier(20000, "premier", CFG) == "semipro"
    assert to_tier(6, "competitive", CFG) == "low" and to_tier(17, "competitive", CFG) == "semipro"
    assert to_tier(3, "faceit", CFG) == "low" and to_tier(10, "faceit", CFG) == "semipro"
    assert to_tier(np.nan, "faceit", CFG) is None


def test_premier_detected_without_rank_type():
    p = decode_players(pi([0, 1300, 5000, 12000, 9000, 8000, 7000, 0, 11000, 15000]), "steam", "5v5", CFG)
    assert set(p["scale"]) == {"premier"}
    assert p["value"].isna().sum() == 2  # rank 0 = unknown, never 0 rating


def test_competitive_when_all_ranks_small():
    p = decode_players(pi([3, 5, 8, 0, 12, 18, 9, 7, 6, 4]), "steam", "5v5", CFG)
    assert set(p["scale"]) == {"competitive"}


def test_rank_type_wins_when_present():
    p = decode_players(pi([3, 5, 8, 9, 12, 14, 9, 7, 6, 4], rank_type=11.0), "steam", "5v5", CFG)
    assert set(p["scale"]) == {"premier"}  # explicit type 11 = Premier even with small numbers


def test_wingman_is_out_of_scope():
    p = decode_players(pi([3, 5, 8, 9]), "steam", "wingman", CFG)
    assert set(p["scale"]) == {"wingman"}
    t = match_tier(p, CFG)
    assert t["tier"] is None and t["tier_reason"] == "wingman"


def test_faceit_level_from_rank_platform():
    p = decode_players(pi([0] * 10, rank_type=-1.0, rank_platform=[1, 2, 3, 4, 5, 6, 7, 8, 9, 0]), "faceit", "5v5", CFG)
    assert set(p["scale"]) == {"faceit"} and p["value"].isna().sum() == 1


def test_one_row_per_player_latest_round():
    frame = pi([100, 200], rounds=2)
    frame.loc[(frame["round"] == 2) & (frame["player_id_fixed"] == 0), "rank"] = 150
    p = decode_players(frame, "steam", "5v5", CFG)
    assert len(p) == 2 and p.set_index("player_id")["raw_rank"][0] == 150


def test_match_tier_median_and_spread():
    p = decode_players(pi([4000, 6000, 9000, 11000, 12000, 16000, 0, 0, 0, 0]), "steam", "5v5", CFG)
    t = match_tier(p, CFG)
    assert t["n_known"] == 6 and t["median_value"] == 10000.0 and t["tier"] == "mid"
    assert t["tier_spread"] == 2  # low … high
    assert t["tier_source"] == "premier"


def test_too_few_known_players_is_null_not_guessed():
    p = decode_players(pi([4000, 6000, 9000, 11000, 12000, 0, 0, 0, 0, 0]), "steam", "5v5", CFG)
    t = match_tier(p, CFG)
    assert t["tier"] is None and t["tier_reason"] == "too_few_known" and t["n_known"] == 5


def test_unknown_platform_is_null():
    p = decode_players(pi([0] * 10, rank_type=-1.0), "unknown", "5v5", CFG)
    t = match_tier(p, CFG)
    assert t["tier"] is None and t["tier_reason"] == "platform_unknown"
