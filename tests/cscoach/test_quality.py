"""Tests for header dedup and quality flags (M1.3). Synthetic frames: code behaviour only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.data.quality import channel_flags, final_state, header_flags

CFG = {
    "wingman_max_unique_steamids": 5,
    "wins_needed": {"5v5": 13, "wingman": 9},
    "overtime_half_rounds": 3,
    "max_tick_gap_s": 1.0,
}


def header(**over):
    base = dict(
        match_id="m", map_name="de_mirage", server_name="srv", number_of_points=100,
        t_starters_score_final=13, ct_starters_score_final=7, is_wingman=None, unique_steamids=10,
        platform="steam", providence="auto", ppp_version="8.5.0", match_date="2026-08-10T20:00:00Z",
        tick_rate=64, t_starters_avg_rank=10.0,
    )
    base.update(over)
    return base


@pytest.mark.parametrize(
    "fmt,a,b,state",
    [
        ("5v5", 13, 7, "regulation"), ("5v5", 12, 12, "draw"), ("5v5", 16, 14, "overtime"),
        ("5v5", 15, 15, "draw"), ("5v5", 19, 17, "overtime"), ("5v5", 18, 18, "draw"),
        ("5v5", 16, 12, "overtime"), ("5v5", 16, 11, "incomplete"), ("5v5", 17, 15, "incomplete"),
        ("5v5", 3, 0, "incomplete"), ("5v5", 9, 4, "incomplete"), ("5v5", 15, 13, "incomplete"),
        ("wingman", 9, 5, "regulation"), ("wingman", 8, 8, "draw"), ("wingman", 13, 2, "incomplete"),
    ],
)
def test_final_state(fmt, a, b, state):
    assert final_state(a, b, fmt, CFG) == state


def test_duplicates_share_key_and_one_canonical_copy():
    h = pd.DataFrame([
        header(match_id="a", ppp_version="6.11.0"),
        header(match_id="b", ppp_version="8.5.0", match_date="2026-08-11T09:00:00Z", providence="user"),
        header(match_id="c", number_of_points=101),
    ])
    complete = {"a": True, "b": False, "c": False}
    f = header_flags(h, complete, CFG).set_index("match_id")
    assert f.loc["a", "dedup_key"] == f.loc["b", "dedup_key"] != f.loc["c", "dedup_key"]
    assert f.loc["a", "dup_n"] == 2 and f.loc["c", "dup_n"] == 1
    assert f.loc["a", "is_canonical"] and not f.loc["b", "is_canonical"]  # full channels win
    assert f.loc["c", "is_canonical"]


def test_canonical_tiebreak_newest_parser_then_id():
    h = pd.DataFrame([header(match_id="z", ppp_version="6.11.9"), header(match_id="y", ppp_version="6.11.10")])
    f = header_flags(h, {"z": False, "y": False}, CFG).set_index("match_id")
    assert f.loc["y", "is_canonical"] and not f.loc["z", "is_canonical"]  # 6.11.10 > 6.11.9 (numeric)


def test_wingman_from_flag_or_player_count():
    h = pd.DataFrame([
        header(match_id="w1", is_wingman=True),
        header(match_id="w2", unique_steamids=4, t_starters_score_final=9, ct_starters_score_final=3),
        header(match_id="n", is_wingman=False, unique_steamids=4),
    ])
    f = header_flags(h, {}, CFG).set_index("match_id")
    assert f.loc["w1", "format"] == "wingman" and f.loc["w2", "format"] == "wingman"
    assert f.loc["n", "format"] == "5v5"  # explicit flag wins over the proxy
    assert f.loc["w2", "final_state"] == "regulation"


def test_header_quality_flags():
    h = pd.DataFrame([
        header(match_id="ok"),
        header(match_id="u", platform="unknown", providence="user", unique_steamids=9, t_starters_avg_rank=0.0),
    ])
    f = header_flags(h, {}, CFG).set_index("match_id")
    assert not f.loc["ok", ["q_platform_unknown", "q_upload_date", "q_player_count"]].any()
    assert f.loc["u", ["q_platform_unknown", "q_upload_date", "q_player_count"]].all()
    assert f.loc["ok", "rank_known"] and not f.loc["u", "rank_known"]
    assert f.loc["ok", "month"] == "2026-08"


def frames(n_rounds=3, disconnects=(), spawns=(), ticks=None, warmup_ticks=()):
    re_ = pd.DataFrame({"round": range(1, n_rounds + 1), "tick": [1000 * r for r in range(1, n_rounds + 1)]})
    rs = pd.DataFrame({"tick": [10, *warmup_ticks], "is_warmup": [True] + [True] * len(warmup_ticks)})
    tk = pd.DataFrame({"tick": ticks if ticks is not None else np.arange(0, 1000 * n_rounds + 1)})
    dc = pd.DataFrame(disconnects, columns=["tick", "player_id_fixed", "is_bot"])
    sp = pd.DataFrame(spawns, columns=["tick", "player_id_fixed"])
    return {"round_end": re_, "round_state": rs, "tick": tk, "player_disconnect": dc, "player_spawn": sp}


def test_channel_flags_clean():
    f = channel_flags(frames(), final_score_sum=3, tick_rate=64, cfg=CFG)
    assert f == {
        "n_round_end": 3, "q_no_round_end": False, "q_rounds_vs_score": False, "q_warmup_after_start": False,
        "max_tick_gap_s": pytest.approx(1 / 64), "q_tick_gap": False, "q_abandonment": False,
    }


def test_channel_flags_defects():
    ticks = np.r_[np.arange(0, 1000), np.arange(1200, 3001)]  # 999 → 1200: 201-tick hole ≈ 3.1 s
    fr = frames(disconnects=[(1500, 4, False), (2990, 5, False), (1500, 9, True)], spawns=[(1400, 4)],
                ticks=ticks, warmup_ticks=(1500,))
    f = channel_flags(fr, final_score_sum=2, tick_rate=64, cfg=CFG)
    assert f["q_rounds_vs_score"] and f["q_warmup_after_start"] and f["q_tick_gap"]
    assert f["max_tick_gap_s"] == pytest.approx(201 / 64)
    assert f["q_abandonment"]  # player 4 left at 1500 < last round end 3000, never respawned


def test_reconnect_is_not_abandonment():
    fr = frames(disconnects=[(1500, 4, False)], spawns=[(2100, 4)])
    assert not channel_flags(fr, final_score_sum=3, tick_rate=64, cfg=CFG)["q_abandonment"]


def test_missing_round_end():
    fr = frames(n_rounds=0, ticks=np.arange(0, 100))
    f = channel_flags(fr, final_score_sum=0, tick_rate=64, cfg=CFG)
    assert f["q_no_round_end"] and f["n_round_end"] == 0 and not f["q_abandonment"]
