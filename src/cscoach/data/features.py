"""State features v1 (M2.3, docs/specs/02 "snapshots → state_features").

One row per snapshot (match, round, tick) with per-side aggregates of the M2.2 player rows (alive players only),
bomb state, time and context. Sides come from ``player_info.team_code`` of the round (2 = T, 3 = CT, F-05; 99.97 %
right against the victim's side at death), filled from ``player_spawn.player_team_code`` only where
``player_info`` has no row for that player and round (spawn: 99.24 %); remaining players without a side are counted
in ``n_players_no_side``, never guessed.

- bomb: ``bomb_planted`` from ``bomb_state`` ``bomb_planted`` with tick ≤ t; ``bomb_site_code`` is the raw
  per-map entity code (A/B mapping in MV.1).
- time: ``time_remaining_s`` = round clock (``round_time_s`` from freeze end) before the plant, bomb clock
  (``bomb_timer_s`` from the plant tick) after it (A-44, measured in MV.1: 115 s / 41 s).
- weapons: v1 counts ``primaries`` (inv_primary > 0); weapon classes need the weapon-code decoding (MV.1).

Leakage: inputs are rows with tick ≤ t plus the round's freeze-end tick; ``DENYLIST`` names (docs/specs/02) never
appear as columns (tested). Labels are attached only in the modelling table. Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

DENYLIST = [r"round_end", r"^winner", r"end_reason", r"end_tick", r"score_final", r"^y_", r"wp_after", r"^wpa",
            r"rank_update", r"after_round", r"^outcome"]

UTILITY = {"flashes": ["inv_flashbang"], "hes": ["inv_hegrenade"], "smokes": ["inv_smokegrenade"],
           "molotovs": ["inv_molotov", "inv_incgrenade"]}


def denylisted(columns) -> list[str]:
    return [c for c in columns if any(re.search(p, c) for p in DENYLIST)]


def side_table(pi: pd.DataFrame, spawn: pd.DataFrame | None, cfg: dict) -> pd.DataFrame:
    primary = (pi.assign(player_id_fixed=pi["player_id_fixed"].astype("float64"), side=pi["team_code"].map(cfg["code_side"]))
               .dropna(subset=["side", "player_id_fixed"]).drop_duplicates(["round", "player_id_fixed"], keep="last")
               [["round", "player_id_fixed", "side"]].assign(side_source="player_info"))
    if spawn is None or not len(spawn):
        return primary
    fill = (spawn.assign(player_id_fixed=spawn["player_id_fixed"].astype("float64"),
                         side=spawn["player_team_code"].map(cfg["code_side"]))
            .dropna(subset=["side", "player_id_fixed"]).sort_values("tick")
            .drop_duplicates(["round", "player_id_fixed"], keep="last")[["round", "player_id_fixed", "side"]]
            .assign(side_source="player_spawn"))
    fill = fill.merge(primary[["round", "player_id_fixed"]], on=["round", "player_id_fixed"], how="left", indicator=True)
    fill = fill[fill["_merge"] == "left_only"].drop(columns="_merge")
    return pd.concat([primary, fill], ignore_index=True)


def build_features(snap: pd.DataFrame, pi: pd.DataFrame, bomb: pd.DataFrame, rounds: pd.DataFrame,
                   ctx: dict, cfg: dict, spawn: pd.DataFrame | None = None) -> pd.DataFrame:
    sides = side_table(pi, spawn, cfg)[["round", "player_id_fixed", "side"]]
    p = snap.assign(player_id_fixed=snap["player_id_fixed"].astype("float64")).merge(
        sides, on=["round", "player_id_fixed"], how="left")
    keys = ["round", "tick"]
    base = snap.drop_duplicates(keys)[keys + ["source"]].reset_index(drop=True)
    no_side = p[p["side"].isna()].groupby(keys).size().rename("n_players_no_side")
    alive = p[p["is_alive"].astype(bool) & p["side"].notna()].copy()
    alive["primaries"] = (alive["inv_primary"].fillna(0) > 0).astype(int)
    for name, cols in UTILITY.items():
        alive[name] = alive[[c for c in cols if c in alive]].fillna(0).sum(axis=1)
    agg = {"alive": ("player_id_fixed", "size"), "hp_sum": ("health", "sum"), "armor_sum": ("armor", "sum"),
           "helmets": ("has_helmet", lambda s: int(s.fillna(False).astype(bool).sum())),
           "kits": ("has_defuser", lambda s: int(s.fillna(False).astype(bool).sum())),
           "equip_value": ("current_equipment_cost", "sum"), "money_sum": ("money", "sum"),
           "primaries": ("primaries", "sum"), **{k: (k, "sum") for k in UTILITY}}
    g = alive.groupby(keys + ["side"]).agg(**agg).unstack("side")
    g.columns = [f"{side.lower()}_{name}" for name, side in g.columns]
    out = base.merge(g.reset_index(), on=keys, how="left").merge(no_side.reset_index(), on=keys, how="left")
    for side in ("ct", "t"):
        for name in agg:
            col = f"{side}_{name}"
            out[col] = out[col].fillna(0) if col in out else 0
    out = out.drop(columns=["t_kits"])  # only CT can carry a defuse kit
    out["n_players_no_side"] = out["n_players_no_side"].fillna(0).astype(int)
    out["man_advantage"] = out["ct_alive"] - out["t_alive"]

    tr = ctx["tick_rate"]
    fe = out["round"].map(rounds.astype({"round": "int64"}).set_index("round")["freeze_end_tick"]).astype("float64")
    out["second_in_round"] = (out["tick"] - fe) / tr
    plants = (bomb[bomb["event_type"] == "bomb_planted"][["round", "tick", "site_code"]].dropna(subset=["round", "tick"])
              .astype({"round": "int64", "tick": "int64"})
              .rename(columns={"tick": "plant_tick", "site_code": "bomb_site_code"}).sort_values("plant_tick"))
    out = out.astype({"tick": "int64"}).sort_values("tick")
    out = pd.merge_asof(out, plants.assign(plant_tick_key=plants["plant_tick"]).rename(columns={"round": "plant_round"}),
                        left_on="tick", right_on="plant_tick_key", direction="backward")
    planted = out["plant_round"].eq(out["round"]).fillna(False).astype(bool)  # CSDS ints arrive nullable
    out["bomb_planted"] = planted
    out["bomb_site_code"] = out["bomb_site_code"].where(planted).astype("Int64")
    since_plant = ((out["tick"] - out["plant_tick"]) / tr).astype("float64")
    out["second_in_round"] = out["second_in_round"].astype("float64")
    out["time_remaining_s"] = np.where(planted, cfg["bomb_timer_s"] - since_plant, cfg["round_time_s"] - out["second_in_round"])
    out = out.drop(columns=["plant_round", "plant_tick", "plant_tick_key"])

    out.insert(0, "match_id", ctx["match_id"])
    out.insert(1, "round_uid", ctx["match_id"] + ":" + out["round"].astype(str))
    for k in ("map_name", "platform", "tier", "build_num", "channel_set"):
        out[k] = ctx.get(k)
    return out.sort_values(keys).reset_index(drop=True)


# ---------------------------------------------------------------- I/O (official loaders)

def _one(args):
    root, key, match_id, ctx, cfg, out_dir = args
    import structlog

    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))
    from pureskillgg_dsdk.ds_io import DsReaderFs, GameDsLoader

    t0 = time.perf_counter()
    snap_path = Path(root) / "derived" / "snapshots" / f"{match_id}.parquet"
    if not snap_path.exists():
        return {"match_id": match_id, "ok": False, "reason": "no snapshots"}
    loader = GameDsLoader(reader=DsReaderFs(root_path=root, manifest_key=key))
    ch = loader.get_channels([
        {"channel": "player_info", "columns": ["round", "player_id_fixed", "team_code"]},
        {"channel": "bomb_state", "columns": ["round", "tick", "event_type", "site_code"]},
        {"channel": "player_spawn", "columns": ["round", "tick", "player_id_fixed", "player_team_code"]},
    ])
    rounds = pd.read_parquet(Path(root) / "derived" / "rounds" / f"{match_id}.parquet", columns=["round", "freeze_end_tick"])
    f = build_features(pd.read_parquet(snap_path), ch["player_info"], ch["bomb_state"], rounds, ctx, cfg,
                       spawn=ch["player_spawn"])
    bad = denylisted(f.columns)
    if bad:
        raise AssertionError(f"denylisted feature columns: {bad}")
    f.to_parquet(Path(out_dir) / f"{match_id}.parquet", index=False)
    return {"match_id": match_id, "ok": True, "rows": int(len(f)), "seconds": round(time.perf_counter() - t0, 3)}


def build(cfg: dict, match_ids: list[str] | None = None) -> pd.DataFrame:
    from cscoach.data.quality import curator

    root = Path(cfg["root"])
    out_dir = root / "derived" / "state_features"
    out_dir.mkdir(parents=True, exist_ok=True)
    h = curator(cfg).get_dataframe(cfg["header_tome"])[["match_id", "key", "tick_rate", "map_name", "platform", "build_num"]]
    q = pd.read_parquet(root / "manifest" / "match_quality.parquet")[["match_id", "channel_set"]]
    t = pd.read_parquet(root / "manifest" / "match_tiers.parquet")[["match_id", "tier"]]
    have = {p.stem for p in (root / "derived" / "snapshots").glob("*.parquet")}
    ids = set(match_ids) if match_ids is not None else have
    m = h[h["match_id"].isin(ids & have)].merge(q, on="match_id").merge(t, on="match_id", how="left")
    jobs = []
    for r in m.itertuples():
        ctx = {"match_id": r.match_id, "tick_rate": int(r.tick_rate), "map_name": r.map_name, "platform": r.platform,
               "tier": None if pd.isna(r.tier) else r.tier, "build_num": int(r.build_num), "channel_set": r.channel_set}
        jobs.append((cfg["root"], r.key, r.match_id, ctx, cfg, str(out_dir)))
    with ProcessPoolExecutor(cfg.get("workers", 12)) as pool:
        return pd.DataFrame(list(pool.map(_one, jobs, chunksize=4)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/features.yaml"))
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    cfg["code_side"] = {int(k): v for k, v in cfg["code_side"].items()}
    res = build(cfg)
    print(json.dumps({"matches": int(len(res)), "ok": int(res["ok"].sum()), "rows": int(res["rows"].sum()),
                      "seconds_mean": float(res["seconds"].mean())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
