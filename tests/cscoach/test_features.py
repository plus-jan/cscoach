"""Tests for state features v1 (M2.3). Synthetic frames: code behaviour only (A-33)."""
import re

import numpy as np
import pandas as pd
import pytest

from cscoach.data.features import DENYLIST, build_features, denylisted

CFG = {"round_time_s": 115.0, "bomb_timer_s": 40.0, "code_side": {2: "T", 3: "CT"}}
CTX = {"match_id": "m", "tick_rate": 64, "map_name": "de_mirage", "platform": "steam", "tier": "mid",
       "build_num": 10896, "channel_set": "v42"}


def snaps():
    rows = []
    for tick in (1000, 1640, 2280):
        for p in range(4):
            dead = p == 3 and tick >= 1640
            rows.append({
                "round": 1, "tick": tick, "source": "cadence", "player_id_fixed": float(p), "is_alive": not dead,
                "health": np.nan if dead else 100.0 - 10 * p, "armor": np.nan if dead else 100.0,
                "has_helmet": pd.NA if dead else (p % 2 == 0), "has_defuser": pd.NA if dead else (p == 0),
                "money": np.nan if dead else 1000.0, "current_equipment_cost": np.nan if dead else 3000.0,
                "inv_primary": np.nan if dead else (7.0 if p < 3 else 0.0), "inv_flashbang": np.nan if dead else 1.0,
                "inv_hegrenade": np.nan if dead else 0.0, "inv_smokegrenade": np.nan if dead else 1.0,
                "inv_molotov": np.nan if dead else 0.0, "inv_incgrenade": np.nan if dead else 1.0,
                "place_name": None if dead else ("BombsiteA" if p == 2 else "Middle"),
                "staleness_ticks": 0,
            })
    df = pd.DataFrame(rows)
    df["has_helmet"] = df["has_helmet"].astype("boolean")
    df["has_defuser"] = df["has_defuser"].astype("boolean")
    return df


def player_info():  # players 0,1 CT; 2,3 T
    return pd.DataFrame({"round": [1] * 4, "player_id_fixed": [0, 1, 2, 3], "team_code": [3, 3, 2, 2]})


def bomb():
    # player 2 (T) plants at 1640 while standing in BombsiteA; site_code is an unstable entity index (MV.1)
    return pd.DataFrame({"round": [1], "tick": [1640], "event_type": ["bomb_planted"], "player_id_fixed": [2.0],
                         "site_code": [168]})


def rounds():
    return pd.DataFrame({"round": [1], "freeze_end_tick": [1000]})


def test_side_aggregates_and_man_advantage():
    f = build_features(snaps(), player_info(), bomb(), rounds(), CTX, CFG).set_index("tick")
    r = f.loc[1000]
    assert (r["ct_alive"], r["t_alive"], r["man_advantage"]) == (2, 2, 0)
    assert r["ct_hp_sum"] == 190 and r["t_hp_sum"] == 150
    assert r["ct_kits"] == 1 and r["ct_helmets"] == 1 and r["t_helmets"] == 1
    assert r["ct_primaries"] == 2 and r["t_primaries"] == 1
    assert r["ct_equip_value"] == 6000 and r["t_money_sum"] == 2000
    assert r["t_flashes"] == 2 and r["t_molotovs"] == 2 and r["t_smokes"] == 2 and r["t_hes"] == 0
    later = f.loc[1640]
    assert (later["t_alive"], later["man_advantage"]) == (1, 1)  # dead player not counted
    assert later["t_hp_sum"] == 80


def test_time_remaining_before_and_after_plant():
    f = build_features(snaps(), player_info(), bomb(), rounds(), CTX, CFG).set_index("tick")
    assert f.loc[1000, "time_remaining_s"] == pytest.approx(115.0)
    assert not f.loc[1000, "bomb_planted"]
    assert f.loc[1640, "bomb_planted"] and f.loc[1640, "bomb_site"] == "A"  # from the planter's place_name
    assert f.loc[1000, "bomb_site"] is None and "bomb_site_code" not in f.columns
    assert f.loc[1640, "time_remaining_s"] == pytest.approx(40.0)  # plant at this tick (≤ t)
    assert f.loc[2280, "time_remaining_s"] == pytest.approx(30.0)
    assert f.loc[2280, "second_in_round"] == pytest.approx(20.0)


def test_context_and_keys():
    f = build_features(snaps(), player_info(), bomb(), rounds(), CTX, CFG)
    assert set(["match_id", "round", "tick", "round_uid", "map_name", "platform", "tier", "build_num"]) <= set(f.columns)
    assert f["round_uid"].iloc[0] == "m:1"
    assert len(f) == 3  # one row per snapshot


def test_players_without_side_are_counted_not_guessed():
    pi = player_info()[lambda d: d["player_id_fixed"] != 1]
    f = build_features(snaps(), pi, bomb(), rounds(), CTX, CFG).set_index("tick")
    assert f.loc[1000, "ct_alive"] == 1 and f.loc[1000, "n_players_no_side"] == 1


def test_no_denylisted_columns():
    f = build_features(snaps(), player_info(), bomb(), rounds(), CTX, CFG)
    assert not denylisted(f.columns)


@pytest.mark.parametrize("col", ["winner_side", "round_end_tick", "end_reason", "end_tick", "t_starters_score_final",
                                 "y_ct_win", "wp_after", "wpa", "rank_update_new"])
def test_denylist_catches_forbidden_names(col):
    assert denylisted([col]) == [col]


@pytest.mark.parametrize("cut", [1000, 1639, 1640, 2280])
def test_features_unchanged_when_future_rows_removed(cut):
    full = build_features(snaps(), player_info(), bomb(), rounds(), CTX, CFG)
    s = snaps()[lambda d: d["tick"] <= cut]
    b = bomb()[lambda d: d["tick"] <= cut]
    part = build_features(s, player_info(), b, rounds(), CTX, CFG)
    pd.testing.assert_frame_equal(full[full["tick"] <= cut].reset_index(drop=True), part.reset_index(drop=True))


def test_nullable_integer_inputs_from_csds():
    b = bomb().astype({"round": "Int64", "tick": "Int64", "site_code": "Int64", "player_id_fixed": "Int64"})
    r = rounds().astype({"round": "Int64", "freeze_end_tick": "Int64"})
    f = build_features(snaps(), player_info(), b, r, CTX, CFG).set_index("tick")
    assert f.loc[1000, "time_remaining_s"] == pytest.approx(115.0) and f.loc[2280, "time_remaining_s"] == pytest.approx(30.0)


def test_spawn_fills_missing_player_info_but_never_overrides():
    pi = player_info()[lambda d: d["player_id_fixed"] != 1]
    spawn = pd.DataFrame({"round": [1, 1], "tick": [990, 990], "player_id_fixed": [1, 0], "player_team_code": [3, 2]})
    f = build_features(snaps(), pi, bomb(), rounds(), CTX, CFG, spawn=spawn).set_index("tick")
    assert f.loc[1000, "ct_alive"] == 2 and f.loc[1000, "n_players_no_side"] == 0  # player 1 from spawn
    assert f.loc[1000, "t_alive"] == 2  # player 0 stays CT (player_info wins), so T = players 2, 3


# ---------------------------------------------------------------- rank prior (M3.2, A-48)
CUTS = {"premier": [10000, 15000, 20000], "competitive": [7, 13, 17], "faceit": [4, 7, 10]}
RCFG = {**CFG, "tier_cutoffs": CUTS, "rank_min_known_share": 0.5}


def test_rank_units_piecewise_linear_over_tier_cutoffs():
    from cscoach.data.features import rank_units

    u = rank_units(np.array([5000, 10000, 12500, 20000, 25000, 40000, np.nan]), "premier", CUTS)
    np.testing.assert_allclose(u, [0.0, 1.0, 1.5, 3.0, 4.0, 4.0, np.nan])
    np.testing.assert_allclose(rank_units(np.array([1, 4, 10]), "faceit", CUTS), [0.0, 1.0, 3.0])
    np.testing.assert_allclose(rank_units(np.array([18]), "competitive", CUTS), [3.25])
    assert np.isnan(rank_units(np.array([12.0]), "unknown", CUTS)).all()


def ranked_info(extra_round2=False):
    pi = player_info().assign(rank=[12000, 14000, 16000, 0], rank_platform=0)
    if extra_round2:  # later rounds must not change earlier snapshots
        pi = pd.concat([pi, pi.assign(round=2, rank=[25000, 25000, 5000, 5000])], ignore_index=True)
    return pi


def test_rank_prior_of_alive_players_per_side():
    f = build_features(snaps(), ranked_info(), bomb(), rounds(), {**CTX, "rank_scale": "premier"}, RCFG).set_index("tick")
    r = f.loc[1000]
    assert r["ct_rank_alive"] == pytest.approx(1.6)   # (1.4 + 1.8) / 2
    assert r["t_rank_alive"] == pytest.approx(2.2)    # player 3 unranked (0) is ignored
    assert r["rank_diff_alive"] == pytest.approx(-0.6)
    assert f.loc[1640, "t_rank_alive"] == pytest.approx(2.2)  # player 3 dead


def test_rank_prior_uses_only_the_snapshot_round():
    ctx = {**CTX, "rank_scale": "premier"}
    a = build_features(snaps(), ranked_info(), bomb(), rounds(), ctx, RCFG)
    b = build_features(snaps(), ranked_info(extra_round2=True), bomb(), rounds(), ctx, RCFG)
    pd.testing.assert_frame_equal(a, b)


def test_rank_prior_missing_without_ranks_or_scale():
    f = build_features(snaps(), player_info(), bomb(), rounds(), CTX, RCFG)
    assert f[["ct_rank_alive", "t_rank_alive", "rank_diff_alive"]].isna().all().all()
    g = build_features(snaps(), ranked_info(), bomb(), rounds(), {**CTX, "rank_scale": "unknown"}, RCFG)
    assert g["rank_diff_alive"].isna().all()


def test_feature_rank_cutoffs_match_tier_config():
    import yaml

    feats = yaml.safe_load(open("configs/features.yaml"))["tier_cutoffs"]
    assert feats == yaml.safe_load(open("configs/tiers.yaml"))["tier_cutoffs"]  # one A-11 scale


def test_rank_prior_needs_half_of_the_alive_side_known():
    # one known rank among the side's alive players is not the side's rank (A-48)
    pi = player_info().assign(rank=[12000, 0, 16000, 0], rank_platform=0)
    f = build_features(snaps(), pi, bomb(), rounds(), {**CTX, "rank_scale": "premier"}, RCFG).set_index("tick")
    assert f.loc[1000, "ct_rank_alive"] == pytest.approx(1.4)   # 1 of 2 known: share 0.5
    three = snaps()
    three = pd.concat([three, three[three["player_id_fixed"] == 1].assign(player_id_fixed=4.0)], ignore_index=True)
    pi3 = pd.concat([pi, pd.DataFrame({"round": [1], "player_id_fixed": [4], "team_code": [3], "rank": [0],
                                       "rank_platform": [0]})], ignore_index=True)
    g = build_features(three, pi3, bomb(), rounds(), {**CTX, "rank_scale": "premier"}, RCFG).set_index("tick")
    assert np.isnan(g.loc[1000, "ct_rank_alive"]) and np.isnan(g.loc[1000, "rank_diff_alive"])  # 1 of 3 known
