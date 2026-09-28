"""Tests for the snapshot sampler and as-of join (M2.2). Synthetic frames: code behaviour only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.data.snapshots import asof_join, sample_ticks, snapshots, truncate

TICK_RATE = 64


def rounds():
    return pd.DataFrame({
        "round": [1, 2],
        "freeze_end_tick": [1000, 5000],
        "end_tick": [3000, 7000],
    })


def events():
    return {
        "player_death": pd.DataFrame({"round": [1, 1, 2], "tick": [1500, 3000, 6500]}),  # 3000 = end tick
        "bomb_state": pd.DataFrame({"round": [2], "tick": [5100]}),
        "player_hurt": pd.DataFrame({"round": [1], "tick": [999]}),  # before freeze end → outside window
    }


def status():
    rows = []
    for p in range(4):
        for t in range(900, 7001, 32):  # player_status every 32 ticks
            rnd = 1 if t < 4000 else 2
            rows.append({"round": rnd, "tick": t, "player_id_fixed": p, "health": 100 - (t // 1000) - p,
                         "money": 800 + t})
    return pd.DataFrame(rows)


def test_sample_ticks_window_cadence_and_events():
    s = sample_ticks(rounds(), events(), tick_rate=TICK_RATE, cadence_s=1.0)
    r1 = s[s["round"] == 1]
    assert r1["tick"].min() == 1000  # freeze end included
    assert r1["tick"].max() < 3000  # end tick excluded
    assert 1500 in set(r1["tick"]) and 999 not in set(r1["tick"])
    cad = r1.loc[r1["source"].str.contains("cadence"), "tick"]
    assert list(cad[:3]) == [1000, 1064, 1128]
    assert s.loc[(s["round"] == 2) & (s["tick"] == 5100), "source"].item() == "bomb_state"
    assert s[["round", "tick"]].duplicated().sum() == 0


def test_event_on_cadence_tick_keeps_both_sources():
    ev = {"player_death": pd.DataFrame({"round": [1], "tick": [1064]})}
    s = sample_ticks(rounds(), ev, tick_rate=TICK_RATE, cadence_s=1.0)
    assert s.loc[s["tick"] == 1064, "source"].item() == "cadence|player_death"


def test_asof_join_takes_latest_row_not_after_tick():
    s = sample_ticks(rounds(), events(), tick_rate=TICK_RATE, cadence_s=1.0)
    j = asof_join(s, status(), ["health", "money"])
    assert (j["status_tick"] <= j["tick"]).all()
    row = j[(j["tick"] == 1500) & (j["player_id_fixed"] == 0)].iloc[0]
    assert row["status_tick"] == 1476 and row["money"] == 800 + 1476  # 900 + 18 * 32
    assert (j["staleness_ticks"] >= 0).all() and j["staleness_ticks"].max() < 32
    assert len(j) == len(s) * 4


def test_asof_join_flags_status_from_another_round():
    st = status()
    st = st[~((st["player_id_fixed"] == 3) & (st["round"] == 2))]  # player 3 has no rows in round 2
    s = sample_ticks(rounds(), events(), tick_rate=TICK_RATE, cadence_s=1.0)
    j = asof_join(s, st, ["health"])
    p3 = j[(j["player_id_fixed"] == 3) & (j["round"] == 2)]
    assert p3["status_other_round"].all() and p3["health"].isna().all()  # never carried across rounds


@pytest.mark.parametrize("cut", [999, 1000, 1499, 1500, 2100, 4000, 5100, 6499, 6999])
def test_leakage_removing_future_rows_changes_nothing(cut):
    full = snapshots(rounds(), events(), status(), ["health", "money"], tick_rate=TICK_RATE, cadence_s=1.0)
    rs, ev, st = truncate(rounds(), events(), status(), cut)
    part = snapshots(rs, ev, st, ["health", "money"], tick_rate=TICK_RATE, cadence_s=1.0)
    a = full[full["tick"] <= cut].reset_index(drop=True)
    b = part[part["tick"] <= cut].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
