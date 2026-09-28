"""Tests for round reconstruction (M2.1). Synthetic frames: code behaviour only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.data.rounds import build_rounds, check_rounds, sides_by_round

CFG = {"regulation_rounds": 24, "overtime_half_rounds": 3, "flip_winner_after_swap": ["v30"], "v30_end_offset_ticks_64": 429,
       "code_side": {2: "T", 3: "CT"}}


def player_info(n_rounds):
    """Players 0-4 start CT (3), 5-9 start T (2). CS2 schedule (observed in CSDS): swap at 13; overtime
    blocks of 6 from round 25 keep the sides for 3 rounds, then swap (28, 34, 40, …)."""
    rows = []
    for r in range(1, n_rounds + 1):
        swaps = 1 if r >= 13 else 0
        swaps += sum(1 for s in range(28, r + 1, 6))  # overtime swaps at 28, 34, 40 (observed in CSDS)
        flipped = swaps % 2 == 1
        for p in range(10):
            start_ct = p < 5
            is_ct = start_ct != flipped
            rows.append({"round": r, "player_id_fixed": p, "team_code": 3 if is_ct else 2})
    return pd.DataFrame(rows)


def match(true_winner_team, channel_set="v42", n_regulation=24):
    """Build channels from a list of true winners per round ('A' = team starting CT, 'B' = starting T)."""
    n = len(true_winner_team)
    pi = player_info(n)
    side = sides_by_round(pi)  # side of team A per round
    code_side = {"T": 2, "CT": 3}
    codes = []
    for i, w in enumerate(true_winner_team, start=1):
        a_side = side.loc[i]
        win_side = a_side if w == "A" else ("T" if a_side == "CT" else "CT")
        codes.append(code_side[win_side])
    re_ = pd.DataFrame({"round": range(1, n + 1), "tick": [1000 * r for r in range(1, n + 1)],
                        "winner_team_code": codes, "win_reason_code": [8] * n})
    if channel_set == "v30":  # simulate the old parser: stale side in the first round of every half
        swaps = [r for r in range(2, n + 1) if side.loc[r] != side.loc[r - 1]]
        for r in sorted(set(swaps) | set(range(25, n + 1, 6))):
            re_.loc[re_["round"] == r, "winner_team_code"] = 5 - re_.loc[re_["round"] == r, "winner_team_code"]
    rs_rows = []
    for r in range(1, n + 1):
        rs_rows += [
            {"round": r, "tick": 1000 * r - 900, "event_type": "round_freeze_end", "is_warmup": False},
            {"round": r, "tick": 1000 * r + 5, "event_type": "round_officially_ended", "is_warmup": False},
        ]
    rs = pd.DataFrame(rs_rows)
    start = pd.DataFrame({"round": range(2, n + 1), "tick": [1000 * (r - 1) + 10 for r in range(2, n + 1)]})
    a = true_winner_team.count("A")
    b = n - a
    return re_, rs, pi, start, (max(a, b), min(a, b))


def test_sides_by_round_detects_swap():
    s = sides_by_round(player_info(24))
    assert s.loc[1] == "CT" and s.loc[12] == "CT" and s.loc[13] == "T" and s.loc[24] == "T"


@pytest.mark.parametrize("channel_set", ["v42", "v30"])
def test_build_rounds_recovers_true_winners(channel_set):
    truth = list("AABABBBAAAAB" + "BBABAAAAA")  # 21 rounds, A wins 13
    re_, rs, pi, st, final = match(truth, channel_set)
    r = build_rounds(re_, rs, pi, st, channel_set=channel_set, cfg=CFG)
    got = ["A" if w == "start_ct" else "B" for w in r["winner_team"]]
    assert got == truth
    chk = check_rounds(r, final_hi=final[0], final_lo=final[1], header_winner=13)
    assert chk["ok"] and chk["team_scores"] == (13, 8)


def test_v30_without_flip_would_fail():
    truth = list("AABABBBAAAAB" + "BBABAAAAA")
    re_, rs, pi, st, final = match(truth, "v30")
    r = build_rounds(re_, rs, pi, st, channel_set="v30", cfg={**CFG, "flip_winner_after_swap": []})
    assert not check_rounds(r, final_hi=final[0], final_lo=final[1], header_winner=13)["ok"]


def test_columns_scores_before_and_phases():
    truth = list("AABABBBAAAAB" + "BBABAAAAA")
    re_, rs, pi, st, final = match(truth)
    r = build_rounds(re_, rs, pi, st, channel_set="v42", cfg=CFG).set_index("round")
    assert r.loc[1, "start_tick"] == 100  # round 1 has no round_start: first round_state tick
    assert r.loc[2, "start_tick"] == 1010
    assert r.loc[3, "freeze_end_tick"] == 2100 and r.loc[3, "end_tick"] == 3000
    assert (r.loc[1, "start_ct_score_before"], r.loc[1, "start_t_score_before"]) == (0, 0)
    assert (r.loc[4, "start_ct_score_before"], r.loc[4, "start_t_score_before"]) == (2, 1)
    assert r.loc[13, "side_start_ct"] == "T"
    # side-perspective scores: in round 13 team A plays T
    assert r.loc[13, "ct_score_before"] == r.loc[13, "start_t_score_before"]
    assert not r["is_overtime"].any() and not r["is_warmup"].any()


def test_overtime_flag_uses_regulation_rounds():
    truth = list("AAAAAABBBBBB" + "BBBBBBAAAAAA" + "AAAA")  # 28 rounds: 12-12 then A wins OT 4-0
    re_, rs, pi, st, final = match(truth)
    r = build_rounds(re_, rs, pi, st, channel_set="v42", cfg=CFG)
    assert r.loc[r["round"] > 24, "is_overtime"].all() and not r.loc[r["round"] <= 24, "is_overtime"].any()
    assert check_rounds(r, final_hi=16, final_lo=12, header_winner=16)["ok"]


def test_check_flags_count_mismatch():
    truth = list("AAAAAAAAAAAAA")  # 13 rounds
    re_, rs, pi, st, final = match(truth)
    r = build_rounds(re_, rs, pi, st, channel_set="v42", cfg=CFG)
    chk = check_rounds(r, final_hi=13, final_lo=1, header_winner=13)  # 14 expected
    assert not chk["ok"] and chk["reason"] == "round_count"


def test_check_flags_team_score_mismatch():
    truth = list("AAAAAAAAAAAAAB")  # 13-1
    re_, rs, pi, st, final = match(truth)
    r = build_rounds(re_, rs, pi, st, channel_set="v42", cfg=CFG)
    chk = check_rounds(r, final_hi=12, final_lo=2, header_winner=12)
    assert not chk["ok"] and chk["reason"] == "team_scores"


@pytest.mark.parametrize("channel_set", ["v42", "v30"])
def test_overtime_recovers_true_winners(channel_set):
    truth = list("AAAAAABBBBBB" + "BBBBBBAAAAAA" + "ABA" + "BAB" + "AAAA")  # 12-12, 15-15 draw, then A 4-0
    re_, rs, pi, st, final = match(truth, channel_set)
    r = build_rounds(re_, rs, pi, st, channel_set=channel_set, cfg=CFG)
    assert ["A" if w == "start_ct" else "B" for w in r["winner_team"]] == truth
    assert list(r.loc[r["side_swap_before"], "round"]) == [13, 28, 34]
    assert check_rounds(r, final_hi=19, final_lo=15, header_winner=19)["ok"]


def test_decided_tick_v42_is_end_tick():
    from cscoach.data.rounds import decided_ticks

    r = pd.DataFrame({"round": [1], "end_tick": [5000], "winner_side": ["CT"], "freeze_end_tick": [1000]})
    d = decided_ticks(r, deaths=pd.DataFrame(columns=["round", "tick", "player_team_code"]),
                      bomb=pd.DataFrame(columns=["round", "tick", "event_type"]), players={1: {"T": 5, "CT": 5}},
                      channel_set="v42", tick_rate=64, cfg={**CFG, "v30_end_offset_ticks_64": 429})
    assert list(d) == [5000]


def test_decided_tick_v30_uses_event_or_constant_offset():
    from cscoach.data.rounds import decided_ticks

    r = pd.DataFrame({"round": [1, 2, 3], "end_tick": [5429, 9525, 20000], "winner_side": ["T", "CT", "CT"],
                      "freeze_end_tick": [1000, 6000, 11000]})
    bomb = pd.DataFrame({"round": [1], "tick": [5000], "event_type": ["bomb_exploded"]})
    deaths = pd.DataFrame({"round": [2] * 5, "tick": [7000, 7100, 7200, 7300, 9000], "player_team_code": [2] * 5})
    d = decided_ticks(r, deaths=deaths, bomb=bomb, players={1: {"T": 5, "CT": 5}, 2: {"T": 5, "CT": 5}, 3: {"T": 5, "CT": 5}},
                      channel_set="v30", tick_rate=64, cfg={**CFG, "v30_end_offset_ticks_64": 429})
    assert list(d) == [5000, 9000, 20000 - 429]  # explosion; 5th T death (event earlier than end - 429); time-out


def test_decided_tick_v30_t_elimination_after_plant_does_not_decide():
    # F-15: after a plant the round goes on until the defuse (or explosion); only a pre-plant T elimination decides
    from cscoach.data.rounds import decided_ticks

    r = pd.DataFrame({"round": [1, 2, 3], "end_tick": [7600 + 429, 9525, 30000], "winner_side": ["CT", "CT", "T"],
                      "freeze_end_tick": [1000, 6000, 20000]})
    bomb = pd.DataFrame({"round": [1, 1, 2, 3], "tick": [6000, 7600, 9400, 22000],
                         "event_type": ["bomb_planted", "bomb_defused", "bomb_planted", "bomb_planted"]})
    deaths = pd.DataFrame({"round": [1] * 5 + [2] * 5 + [3] * 5,
                           "tick": [6100, 6200, 6300, 6400, 7000, 7000, 7100, 7200, 7300, 9000,
                                    22100, 22200, 22300, 22400, 22500],
                           "player_team_code": [2] * 10 + [3] * 5})
    d = decided_ticks(r, deaths=deaths, bomb=bomb, players={k: {"T": 5, "CT": 5} for k in (1, 2, 3)},
                      channel_set="v30", tick_rate=64, cfg={**CFG, "v30_end_offset_ticks_64": 429})
    # 1: T wiped at 7000 after the plant at 6000 → the defuse at 7600 decides
    # 2: T wiped at 9000 before the plant at 9400 → the elimination decides
    # 3: CT wiped after the plant → the CT elimination decides (T win)
    assert list(d) == [7600, 9000, 22500]
