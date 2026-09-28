"""MV.1 collector: raw facts for decoding CSDS codes and checking timers and ticks.

Per sampled match (clean, seeded, reconciled rounds) it gathers:
- ``rounds``: round timing (round_start, freeze end, end), winner side and ``win_reason_code``, bomb plant /
  explode / defuse ticks, plant ``site_code`` and the planter's ``place_name`` at the plant, deaths per side;
- ``weapons``: co-occurrence of weapon codes and ``weapon_name`` (player_death, player_hurt, weapon_fire);
- ``hitboxes``: ``hit_box_code`` × weapon with damage, and the hit box of the killing hit × ``is_headshot``;
- ``ticks``: tick-rate, tick-channel coverage and gaps, and the lag of merged event positions (player_death
  attacker position vs ``player_vector``).
The analysis lives in the MV.1 report; decoding tables go to docs/data/. Data provided by PureSkill.gg.
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


def _load(root, key):
    import structlog

    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))
    from pureskillgg_dsdk.ds_io import DsReaderFs, GameDsLoader

    return GameDsLoader(reader=DsReaderFs(root_path=root, manifest_key=key))


def collect_match(args):
    root, key, match_id, meta = args
    L = _load(root, key)
    cols = {ch["channel"]: {c["name"] for c in ch["columns"]} for ch in L.manifest["channels"]}

    def get(ch, want):
        return L.get_channel({"channel": ch, "columns": [c for c in want if c in cols.get(ch, set())]})

    tick_rate = int(get("header", ["tick_rate"])["tick_rate"].iloc[0])
    r = pd.read_parquet(Path(root) / "derived" / "rounds" / f"{match_id}.parquet")
    re_ = get("round_end", ["round", "win_reason_message"])
    r = r.merge(re_, on="round", how="left")
    rs = get("round_state", ["round", "tick", "event_type"])
    for ev, name in (("round_start", "rs_round_start_tick"), ("round_prestart", "rs_prestart_tick"),
                     ("round_officially_ended", "rs_official_end_tick")):
        r[name] = r["round"].map(rs[rs["event_type"] == ev].groupby("round")["tick"].min())
    bomb = get("bomb_state", ["round", "tick", "event_type", "site_code", "player_id_fixed"])
    for ev in ("bomb_planted", "bomb_exploded", "bomb_defused"):
        b = bomb[bomb["event_type"] == ev].sort_values("tick").drop_duplicates("round")
        r[f"{ev}_tick"] = r["round"].map(b.set_index("round")["tick"])
        if ev == "bomb_planted":
            r["plant_site_code"] = r["round"].map(b.set_index("round")["site_code"])
            planter = b[["round", "tick", "player_id_fixed"]].dropna()
    st = get("player_status", ["tick", "player_id_fixed", "place_name"]).dropna(subset=["player_id_fixed"])
    places = {}
    for rnd, t, pid in zip(planter["round"], planter["tick"], planter["player_id_fixed"]):
        s = st[(st["player_id_fixed"] == pid) & (st["tick"] <= t)]
        places[rnd] = s["place_name"].iloc[-1] if len(s) else None
    r["planter_place"] = r["round"].map(places)
    pdth = get("player_death", ["round", "tick", "player_id_fixed", "player_team_code", "attacker_id_fixed",
                                "weapon_name", "attacker_weapon_code", "player_weapon_code", "is_headshot",
                                "attacker_x_pos", "attacker_y_pos"])
    for code, side in ((3, "ct"), (2, "t")):
        r[f"deaths_{side}"] = r["round"].map(pdth[pdth["player_team_code"] == code].groupby("round").size()).fillna(0)
    pi = get("player_info", ["round", "team_code"])
    for code, side in ((3, "ct"), (2, "t")):
        r[f"players_{side}"] = r["round"].map(pi[pi["team_code"] == code].groupby("round").size()).fillna(0)
    r["tick_rate"] = tick_rate
    r = r.assign(match_id=match_id, **meta)

    # weapons: code ↔ name co-occurrence
    w = []
    for ch, code_col in (("player_death", "attacker_weapon_code"), ("player_hurt", "attacker_weapon_code"),
                         ("weapon_fire", "player_weapon_code")):
        if ch not in cols or code_col not in cols[ch]:
            continue
        d = get(ch, ["weapon_name", code_col]).rename(columns={code_col: "code"})
        w.append(d.groupby(["code", "weapon_name"], dropna=False).size().rename("n").reset_index().assign(channel=ch))
    weapons = pd.concat(w, ignore_index=True).assign(channel_set=meta["channel_set"]) if w else pd.DataFrame()

    # hit boxes
    hurt = get("player_hurt", ["round", "tick", "player_id_fixed", "hit_box_code", "health_removed", "weapon_name"])
    hb = (hurt.groupby(["hit_box_code", "weapon_name"], dropna=False)
          .agg(n=("health_removed", "size"), dmg_mean=("health_removed", "mean")).reset_index()
          .assign(channel_set=meta["channel_set"]))
    kill_hit = pdth[["round", "tick", "player_id_fixed", "is_headshot"]].merge(
        hurt[["round", "tick", "player_id_fixed", "hit_box_code"]], on=["round", "tick", "player_id_fixed"], how="left")
    kh = (kill_hit.groupby(["hit_box_code", "is_headshot"], dropna=False).size().rename("n").reset_index()
          .assign(channel_set=meta["channel_set"]))

    # ticks: coverage, gaps, merged-position lag
    tk = get("tick", ["tick", "second"]).drop_duplicates("tick").sort_values("tick")
    gaps = np.diff(tk["tick"].to_numpy())
    sec_err = float(np.abs(tk["second"] - (tk["tick"] - tk["tick"].iloc[0]) / tick_rate - tk["second"].iloc[0]).max()) \
        if "second" in tk else None
    pv = get("player_vector", ["tick", "player_id_fixed", "x_pos", "y_pos"]).dropna(subset=["player_id_fixed"])
    lags = []
    kills = pdth.dropna(subset=["attacker_id_fixed", "attacker_x_pos"]).head(60)
    for t, a, x, y in zip(kills["tick"], kills["attacker_id_fixed"], kills["attacker_x_pos"], kills["attacker_y_pos"]):
        v = pv[(pv["player_id_fixed"] == a) & (pv["tick"] <= t) & (pv["tick"] >= t - 64)]
        hit = v[np.isclose(v["x_pos"], x) & np.isclose(v["y_pos"], y)]
        lags.append(int(t - hit["tick"].max()) if len(hit) else None)
    ticks = {"match_id": match_id, **meta, "tick_rate": tick_rate, "n_ticks": int(len(tk)),
             "span": int(tk["tick"].iloc[-1] - tk["tick"].iloc[0] + 1), "max_gap": int(gaps.max()) if len(gaps) else 0,
             "n_gaps_gt1": int((gaps > 1).sum()), "second_max_err": sec_err,
             "pos_lag_exact_share": float(np.mean([x == 0 for x in lags if x is not None])) if lags else None,
             "pos_lag_max": max([x for x in lags if x is not None], default=None),
             "pos_lag_unmatched": int(sum(x is None for x in lags)), "pos_lag_n": len(lags)}
    return r, weapons, hb, kh, ticks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/mv1.yaml"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    from cscoach.data.quality import curator

    root = Path(cfg["root"])
    chk = pd.read_parquet(root / "manifest" / "rounds_check.parquet")
    elig = chk[chk["ok"] & chk["clean"] & chk["in_seeded_sample"].fillna(False).astype(bool)]
    sample = pd.concat([g.sample(min(cfg["per_channel_set"], len(g)), random_state=cfg["seed"])
                        for _, g in elig.groupby("channel_set")])
    h = curator(cfg).get_dataframe(cfg["header_tome"])[["match_id", "key", "build_num", "platform"]]
    sample = sample.drop(columns=["platform"]).merge(h, on="match_id")
    jobs = [(cfg["root"], k, m, {"channel_set": cs, "platform": p, "build_num": int(b)})
            for k, m, cs, p, b in zip(sample["key"], sample["match_id"], sample["channel_set"], sample["platform"], sample["build_num"])]
    with ProcessPoolExecutor(cfg.get("workers", 12)) as pool:
        res = list(pool.map(collect_match, jobs, chunksize=4))
    args.out.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(["rounds", "weapons", "hitboxes", "kill_hitboxes"]):
        pd.concat([x[i] for x in res], ignore_index=True).to_parquet(args.out / f"{name}.parquet", index=False)
    pd.DataFrame([x[4] for x in res]).to_parquet(args.out / "ticks.parquet", index=False)
    print(json.dumps({"matches": len(res), "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
