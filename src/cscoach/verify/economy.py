"""MV.1 economy collector: observed money changes to reconcile against the rule set (A-13 → A-45).

Per sampled match and player-round it records the money at the player's last ``player_status`` row of round r at or
before the tick the round was decided (``rounds.decided_tick``) and at the first row of round r+1 (the round reward
lands in between; kills after the decision add noise), with the round context needed by the rules:
winner, end reason (explosion / defuse / elimination / time, from events — v30 has no reason codes), bomb planted,
side, half starts. Kill rewards: the attacker's money change across each kill tick, with the weapon.
Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from cscoach.verify.mv1 import _load


def end_reason(row) -> str:
    if pd.notna(row["bomb_exploded_tick"]):
        return "exploded"
    if pd.notna(row["bomb_defused_tick"]):
        return "defused"
    loser_dead = row["deaths_t"] >= row["players_t"] if row["winner_side"] == "CT" else row["deaths_ct"] >= row["players_ct"]
    if loser_dead:
        return "elimination"
    if row["winner_side"] == "CT" and pd.isna(row["bomb_planted_tick"]):
        return "time"
    return "other"


def collect(args):
    root, key, match_id, rounds_ext = args
    L = _load(root, key)
    st = L.get_channel({"channel": "player_status", "columns": ["round", "tick", "player_id_fixed", "money"]})
    st = st.dropna(subset=["player_id_fixed"]).sort_values("tick")
    pi = L.get_channel({"channel": "player_info", "columns": ["round", "player_id_fixed", "team_code"]})
    side = pi[pi["team_code"].isin([2, 3])].drop_duplicates(["round", "player_id_fixed"]).set_index(["round", "player_id_fixed"])["team_code"]
    decided = pd.read_parquet(Path(root) / "derived" / "rounds" / f"{match_id}.parquet",
                              columns=["round", "decided_tick"]).set_index("round")["decided_tick"]
    st["decided"] = st["round"].map(decided)
    first = st.groupby(["round", "player_id_fixed"])["money"].first()
    # money when the round was decided (dead players: their last row before death); the reward lands after it
    last = st[st["tick"] < st["decided"]].groupby(["round", "player_id_fixed"])["money"].last()
    r = rounds_ext.set_index("round")
    rows = []
    for (rnd, pid), m_end in last.items():
        nxt = (rnd + 1, pid)
        if nxt not in first.index or rnd not in r.index:
            continue
        x = r.loc[rnd]
        s = side.get((rnd, pid))
        rows.append({"match_id": match_id, "round": int(rnd), "player": pid, "side": {2: "T", 3: "CT"}.get(s),
                     "money_end": int(m_end), "money_next": int(first.loc[nxt]),
                     "won": None if s is None else ({2: "T", 3: "CT"}[s] == x["winner_side"]),
                     "reason": end_reason(x), "planted": pd.notna(x["bomb_planted_tick"]),
                     "next_is_half_start": bool(r["side_swap_before"].get(rnd + 1, False)) or rnd + 1 in (13, 25),
                     "winner_side": x["winner_side"], "enemy_deaths": int(x["deaths_t"] if s == 3 else x["deaths_ct"]),
                     "own_deaths": int(x["deaths_ct"] if s == 3 else x["deaths_t"])})
    pr = pd.DataFrame(rows)
    # kill rewards: attacker money just before vs at/after the kill tick (same round)
    d = L.get_channel({"channel": "player_death", "columns": ["round", "tick", "attacker_id_fixed", "weapon_name",
                                                              "player_team_code", "attacker_team_code"]})
    d = d.dropna(subset=["attacker_id_fixed"])
    kills = []
    for rnd, t, a, w, vt, at in zip(d["round"], d["tick"], d["attacker_id_fixed"], d["weapon_name"],
                                    d["player_team_code"], d["attacker_team_code"]):
        s = st[(st["player_id_fixed"] == a) & (st["round"] == rnd)]
        before = s[s["tick"] < t]["money"]
        after = s[(s["tick"] >= t) & (s["tick"] <= t + 16)]["money"]
        if len(before) and len(after):
            kills.append({"match_id": match_id, "weapon_name": w, "team_kill": vt == at,
                          "delta": int(after.iloc[-1] - before.iloc[-1])})
    return pr, pd.DataFrame(kills)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/mv1.yaml"))
    ap.add_argument("--mv1-dir", type=Path, required=True)
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    from cscoach.data.quality import curator

    rounds = pd.read_parquet(args.mv1_dir / "rounds.parquet")
    h = curator(cfg).get_dataframe(cfg["header_tome"]).set_index("match_id")["key"]
    jobs = [(cfg["root"], h.loc[m], m, g) for m, g in rounds.groupby("match_id")]
    with ProcessPoolExecutor(cfg.get("workers", 12)) as pool:
        res = list(pool.map(collect, jobs, chunksize=4))
    pd.concat([x[0] for x in res], ignore_index=True).merge(
        rounds.drop_duplicates("match_id")[["match_id", "channel_set", "platform", "build_num"]], on="match_id"
    ).to_parquet(args.mv1_dir / "economy_rounds.parquet", index=False)
    pd.concat([x[1] for x in res], ignore_index=True).to_parquet(args.mv1_dir / "economy_kills.parquet", index=False)
    print(json.dumps({"matches": len(res)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
