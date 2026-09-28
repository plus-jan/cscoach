"""Round reconstruction (M2.1): one row per round with phases, winner side/team and scores before the round.

Decoding (M2.1 report, A-15):
- ``team_code`` / ``winner_team_code``: 2 = T, 3 = CT (``win_reason_message`` agrees).
- Each player's side per round comes from ``player_info.team_code``; sides swap where the players' codes
  flip (no hard-coded schedule). ``start_ct`` = the team that plays CT in round 1.
- The v30 parser reports the winner's side with a stale mapping in the first round of every half: after each
  side swap (13, 28, 34, …) and at the start of each overtime block (25, 31, …) where the sides do not change
  (round 13: 322/322 disagreements with ``round_state``; rounds 14–24: 100 % agreement; with this rule
  overtime and draw matches reconcile 100 %). For channel sets in ``flip_winner_after_swap`` that side is
  flipped. v42 needs no correction.
- ``round_state`` scores are not used for winners (their convention differs by parser and swaps on display);
  they are the independent check: final team scores must equal the last ``round_state`` scores and the header
  winner score.
- ``win_reason_code``: v30 only carries 8/9 (winner side); v42 carries the full reason (MV.1 table).
- ``decided_tick`` (MV.1): the tick the round was decided. v42 ``round_end.tick`` is that tick (explosion/defuse
  gap 0; ``round_officially_ended`` a constant 448 ticks later). The v30 ``round_end.tick`` is 19–20 ticks before
  ``round_officially_ended``, i.e. ~6.7 s after the decision; there ``decided_tick`` = min(end − 429 ticks at 64 Hz,
  deciding event: explosion, defuse, or the death that eliminated the losing side — except a T elimination after
  the plant, where the round runs on to the defuse or explosion, F-15). Snapshots end here.
- ``is_overtime``: rounds after ``regulation_rounds`` (the ``pop_overtime`` rule, max_rounds_csgo = 24).

Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def sides_by_round(pi: pd.DataFrame) -> pd.Series:
    """Side of the team that is CT in round 1, per round (majority of that team's players)."""
    pi = pi[pi["team_code"].isin([2, 3])]
    first = pi["round"].min()
    start_ct = set(pi.loc[(pi["round"] == first) & (pi["team_code"] == 3), "player_id_fixed"])
    team = pi[pi["player_id_fixed"].isin(start_ct)]
    ct_share = team.groupby("round")["team_code"].apply(lambda s: (s == 3).mean())
    return ct_share.map(lambda x: "CT" if x >= 0.5 else "T")


def build_rounds(re_: pd.DataFrame, rs: pd.DataFrame, pi: pd.DataFrame, rstart: pd.DataFrame, *,
                 channel_set: str, cfg: dict) -> pd.DataFrame:
    from pureskillgg_csgo_dsdk import pop_overtime

    side_a = sides_by_round(pi)
    r = re_.sort_values("round").drop_duplicates("round", keep="last").reset_index(drop=True)
    r["side_start_ct"] = r["round"].map(side_a).ffill().bfill()
    swapped = r["side_start_ct"].ne(r["side_start_ct"].shift()) & r.index.to_series().gt(0)
    side = r["winner_team_code"].map(cfg["code_side"])
    if channel_set in cfg["flip_winner_after_swap"]:
        ot_block = 2 * cfg["overtime_half_rounds"]
        half_start = swapped | ((r["round"] > cfg["regulation_rounds"])
                                & ((r["round"] - cfg["regulation_rounds"] - 1) % ot_block == 0))
        side = np.where(half_start, side.map({"T": "CT", "CT": "T"}), side)
    r["winner_side"] = side
    r["winner_team"] = np.where(r["winner_side"] == r["side_start_ct"], "start_ct", "start_t")
    a_win = (r["winner_team"] == "start_ct").astype(int)
    r["start_ct_score_before"] = a_win.cumsum().shift(fill_value=0)
    r["start_t_score_before"] = (1 - a_win).cumsum().shift(fill_value=0)
    a_is_ct = r["side_start_ct"] == "CT"
    r["ct_score_before"] = np.where(a_is_ct, r["start_ct_score_before"], r["start_t_score_before"])
    r["t_score_before"] = np.where(a_is_ct, r["start_t_score_before"], r["start_ct_score_before"])

    starts = rstart.groupby("round")["tick"].min()
    first_rs = rs.groupby("round")["tick"].min()
    r["start_tick"] = r["round"].map(starts).fillna(r["round"].map(first_rs)).astype("Int64")
    fe = rs[rs["event_type"] == "round_freeze_end"].groupby("round")["tick"].min()
    r["freeze_end_tick"] = r["round"].map(fe).astype("Int64")
    r = r.rename(columns={"tick": "end_tick"})
    warm = rs[rs["is_warmup"].astype(bool)].groupby("round").size() if "is_warmup" in rs else pd.Series(dtype=int)
    r["is_warmup"] = r["round"].map(warm).fillna(0).gt(0)
    ot = pop_overtime(r[["round"]].copy(), max_rounds_csgo=cfg["regulation_rounds"])
    r["is_overtime"] = r.index.isin(ot.index)
    r["side_swap_before"] = swapped.to_numpy()
    cols = ["round", "start_tick", "freeze_end_tick", "end_tick", "winner_side", "winner_team", "winner_team_code",
            "win_reason_code", "side_start_ct", "side_swap_before", "is_overtime", "is_warmup",
            "ct_score_before", "t_score_before", "start_ct_score_before", "start_t_score_before"]
    return r[cols]


def decided_ticks(r: pd.DataFrame, *, deaths: pd.DataFrame, bomb: pd.DataFrame, players: dict, channel_set: str,
                  tick_rate: int, cfg: dict) -> pd.Series:
    if channel_set not in cfg["flip_winner_after_swap"]:  # v42: round_end.tick is exact
        return r["end_tick"].astype("int64").rename("decided_tick")
    offset = int(round(cfg["v30_end_offset_ticks_64"] * tick_rate / 64))
    side_code = {"T": 2, "CT": 3}
    out = []
    for rnd, end, winner in zip(r["round"], r["end_tick"], r["winner_side"]):
        cand = [int(end) - offset]
        b = bomb[(bomb["round"] == rnd) & bomb["event_type"].isin(["bomb_exploded", "bomb_defused"])]
        if len(b):
            cand.append(int(b["tick"].min()))
        loser = "T" if winner == "CT" else "CT"
        n = players.get(rnd, {}).get(loser, 0)
        dl = deaths[(deaths["round"] == rnd) & (deaths["player_team_code"] == side_code[loser])]["tick"].sort_values()
        if n > 0 and len(dl) >= n:
            elim = int(dl.iloc[n - 1])
            plants = bomb[(bomb["round"] == rnd) & (bomb["event_type"] == "bomb_planted")]["tick"]
            # after a plant, eliminating the T side does not end the round: the defuse or explosion does (F-15)
            if not (loser == "T" and len(plants) and int(plants.min()) <= elim):
                cand.append(elim)
        out.append(min(cand))
    return pd.Series(out, index=r.index, name="decided_tick", dtype="int64")


def check_rounds(r: pd.DataFrame, *, final_hi: int, final_lo: int, header_winner: int) -> dict:
    a = int((r["winner_team"] == "start_ct").sum())
    b = int(len(r) - a)
    hi, lo = max(a, b), min(a, b)
    res = {"n_rounds": int(len(r)), "team_scores": (hi, lo), "ok": True, "reason": None}
    if len(r) != final_hi + final_lo:
        res.update(ok=False, reason="round_count")
    elif (hi, lo) != (final_hi, final_lo):
        res.update(ok=False, reason="team_scores")
    elif hi != header_winner:
        res.update(ok=False, reason="header_winner")
    return res


# ---------------------------------------------------------------- I/O (official loaders)

def _one(args):
    root, key, match_id, channel_set, final_hi, final_lo, header_winner, cfg, out_dir = args
    import structlog

    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))
    from pureskillgg_dsdk.ds_io import DsReaderFs, GameDsLoader

    loader = GameDsLoader(reader=DsReaderFs(root_path=root, manifest_key=key))
    try:
        ch = loader.get_channels([
            {"channel": "round_end", "columns": ["round", "tick", "winner_team_code", "win_reason_code"]},
            {"channel": "round_state", "columns": ["round", "tick", "event_type", "is_warmup"]},
            {"channel": "round_start", "columns": ["round", "tick"]},
            {"channel": "player_info", "columns": ["round", "player_id_fixed", "team_code"]},
            {"channel": "player_death", "columns": ["round", "tick", "player_team_code"]},
            {"channel": "bomb_state", "columns": ["round", "tick", "event_type"]},
            {"channel": "header", "columns": ["tick_rate"]},
        ])
        r = build_rounds(ch["round_end"], ch["round_state"], ch["player_info"], ch["round_start"],
                         channel_set=channel_set, cfg=cfg)
        pi = ch["player_info"][ch["player_info"]["team_code"].isin([2, 3])]
        players = {rnd: {cfg["code_side"][c]: int(n) for c, n in g.groupby("team_code").size().items()}
                   for rnd, g in pi.groupby("round")}
        r["decided_tick"] = decided_ticks(r, deaths=ch["player_death"], bomb=ch["bomb_state"], players=players,
                                          channel_set=channel_set, tick_rate=int(ch["header"]["tick_rate"].iloc[0]), cfg=cfg)
    except Exception as err:
        return {"match_id": match_id, "ok": False, "reason": f"error: {err!r}"[:200]}
    r.insert(0, "match_id", match_id)
    r.to_parquet(Path(out_dir) / f"{match_id}.parquet", index=False)
    chk = check_rounds(r, final_hi=final_hi, final_lo=final_lo, header_winner=header_winner)
    return {"match_id": match_id, **chk, "team_scores": list(chk["team_scores"]),
            "n_swaps": int(r["side_swap_before"].sum()), "n_overtime": int(r["is_overtime"].sum())}


def build(cfg: dict) -> pd.DataFrame:
    from cscoach.data.quality import curator

    root = Path(cfg["root"])
    out_dir = root / "derived" / "rounds"
    out_dir.mkdir(parents=True, exist_ok=True)
    q = pd.read_parquet(root / "manifest" / "match_quality.parquet")
    h = curator(cfg).get_dataframe(cfg["header_tome"])
    h["header_winner"] = h[["t_starters_score_final", "ct_starters_score_final"]].max(axis=1)
    todo = q[q["is_canonical"] & (q["format"] == "5v5") & q["complete"].fillna(False).astype(bool)
             & q["final_hi"].notna()].merge(h[["match_id", "key", "header_winner"]], on="match_id")
    jobs = [(cfg["root"], k, m, cs, int(a), int(b), int(w), cfg, str(out_dir)) for k, m, cs, a, b, w in
            zip(todo["key"], todo["match_id"], todo["channel_set"], todo["final_hi"], todo["final_lo"], todo["header_winner"])]
    with ProcessPoolExecutor(cfg.get("workers", 12)) as pool:
        rows = list(pool.map(_one, jobs, chunksize=16))
    return pd.DataFrame(rows).merge(
        q[["match_id", "channel_set", "platform", "clean", "in_seeded_sample", "final_state", "month"]], on="match_id"
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/rounds.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    cfg["code_side"] = {int(k): v for k, v in cfg["code_side"].items()}
    res = build(cfg)
    res.to_parquet(Path(cfg["root"]) / "manifest" / "rounds_check.parquet", index=False)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    seeded = res[res["in_seeded_sample"].fillna(False).astype(bool)]
    summary = {
        **args.meta,
        "matches": int(len(res)),
        "ok_share_all": round(float(res["ok"].mean()), 5),
        "ok_share_seeded": round(float(seeded["ok"].mean()), 5),
        "ok_by_channel_set": res.groupby("channel_set")["ok"].agg(["mean", "size"]).round(5).to_dict("index"),
        "ok_by_final_state": res.groupby("final_state")["ok"].agg(["mean", "size"]).round(5).to_dict("index"),
        "fail_reasons": res.loc[~res["ok"], "reason"].value_counts().to_dict(),
        "rounds_total": int(res["n_rounds"].sum()),
        "overtime_rounds": int(res["n_overtime"].sum()),
        "swaps_per_match": res["n_swaps"].value_counts().sort_index().to_dict(),
        "dod_ge_0995": bool(res["ok"].mean() >= 0.995),
    }
    (args.report_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
