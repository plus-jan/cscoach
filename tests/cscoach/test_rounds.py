"""Tests for round reconstruction (M2.1). Synthetic frames: code behaviour only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.data.rounds import build_rounds, check_rounds, sides_by_round

CFG = {"regulation_rounds": 24, "flip_winner_after_swap": ["v30"], "code_side": {2: "T", 3: "CT"}}


def player_info(n_rounds, swap_after=12, ot_half=3):
    """Players 0-4 start CT (3), 5-9 start T (2); sides swap after `swap_after`, then every `ot_half`."""
    rows = []
    for r in range(1, n_rounds + 1):
        if r <= swap_after:
            flipped = False
        elif r <= 2 * swap_after:
            flipped = True
        else:
            flipped = ((r - 2 * swap_after - 1) // ot_half) % 2 == 0  # OT half 1 swaps back? keep simple: alternate
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
    if channel_set == "v30":  # simulate the old parser: side mapping is stale in the first round after a swap
        swaps = [r for r in range(2, n + 1) if side.loc[r] != side.loc[r - 1]]
        for r in swaps:
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
