"""State features v1 (M2.3, docs/specs/02 "snapshots → state_features").

One row per snapshot (match, round, tick) with per-side aggregates of the M2.2 player rows (alive players only),
bomb state, time and context. Sides come from ``player_info.team_code`` of the round (2 = T, 3 = CT, F-05; 99.97 %
right against the victim's side at death), filled from ``player_spawn.player_team_code`` only where
``player_info`` has no row for that player and round (spawn: 99.24 %); remaining players without a side are counted
in ``n_players_no_side``, never guessed.

- bomb: ``bomb_planted`` from ``bomb_state`` ``bomb_planted`` with tick ≤ t; ``bomb_site`` (A/B) from the planter's
  ``place_name`` at the plant tick (a snapshot tick, since ``bomb_state`` is an event channel). The raw ``site_code``
  is a per-server entity index and is not used (MV.1, docs/data/csds_decoding.md).
- time: ``time_remaining_s`` = round clock (``round_time_s`` from freeze end) before the plant, bomb clock
  (``bomb_timer_s`` from the plant tick) after it (A-44, measured in MV.1: 115 s / 41 s).
- weapons: v1 counts ``primaries`` (inv_primary > 0); weapon classes need the weapon-code decoding (MV.1).
- rank prior (M3.2, docs/specs/03 WP, A-48): each player's rank from ``player_info`` of the snapshot's round
  (Premier rating / skill group in ``rank``, FACEIT level in ``rank_platform``; 0 = unknown) on the match's scale
  (``rank_scale`` = M1.4 ``tier_source``), mapped to tier units (piecewise linear over the A-11 cut-offs: cut-off i
  → i, extrapolated with the neighbouring segment width, clipped to [0, 4]); ``ct_rank_alive`` / ``t_rank_alive`` =
  mean over the side's alive players with a known rank, missing unless at least ``rank_min_known_share`` of them are
  known; ``rank_diff_alive`` = CT − T (missing when either side is).

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


RANK_SOURCE = {"premier": "rank", "competitive": "rank", "faceit": "rank_platform"}


def rank_units(values, scale: str, cutoffs: dict) -> np.ndarray:
    v = np.asarray(values, dtype="float64")
    if scale not in RANK_SOURCE or scale not in cutoffs:
        return np.full(v.shape, np.nan)
    c1, c2, c3 = cutoffs[scale]
    u = np.interp(v, [c1 - (c2 - c1), c1, c2, c3, c3 + (c3 - c2)], [0.0, 1.0, 2.0, 3.0, 4.0])  # clips at 0 and 4
    return np.where(np.isnan(v), np.nan, u)


def rank_table(pi: pd.DataFrame, scale: str | None, cfg: dict) -> pd.DataFrame:
    """Tier-unit rank per (round, player) from that round's ``player_info`` rows (A-48)."""
    col = RANK_SOURCE.get(scale or "")
    if col is None or col not in pi or "tier_cutoffs" not in cfg:
        return pd.DataFrame({"round": pd.Series(dtype="int64"), "player_id_fixed": pd.Series(dtype="float64"),
                             "rank_units": pd.Series(dtype="float64")})
    r = pi[["round", "player_id_fixed", col]].dropna(subset=["player_id_fixed"]).drop_duplicates(
        ["round", "player_id_fixed"], keep="last")
    raw = pd.to_numeric(r[col], errors="coerce").astype("float64")
    return pd.DataFrame({"round": r["round"].to_numpy(), "player_id_fixed": r["player_id_fixed"].astype("float64").to_numpy(),
                         "rank_units": rank_units(raw.where(raw > 0).to_numpy(), scale, cfg["tier_cutoffs"])})


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
    ranks = rank_table(pi, ctx.get("rank_scale"), cfg)
    alive = alive.merge(ranks.astype({"round": alive["round"].dtype}), on=["round", "player_id_fixed"], how="left")
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
    grp = alive.groupby(keys + ["side"])["rank_units"]
    rk = grp.mean().where(grp.count() >= cfg.get("rank_min_known_share", 0.5) * grp.size()).unstack("side")
    rk = rk.reindex(columns=["CT", "T"]).rename(columns={"CT": "ct_rank_alive", "T": "t_rank_alive"}).reset_index()
    rk.columns.name = None
    out = out.merge(rk, on=keys, how="left")
    out["rank_diff_alive"] = out["ct_rank_alive"] - out["t_rank_alive"]
    out["n_players_no_side"] = out["n_players_no_side"].fillna(0).astype(int)
    out["man_advantage"] = out["ct_alive"] - out["t_alive"]

    tr = ctx["tick_rate"]
    fe = out["round"].map(rounds.astype({"round": "int64"}).set_index("round")["freeze_end_tick"]).astype("float64")
    out["second_in_round"] = (out["tick"] - fe) / tr
    plants = (bomb[bomb["event_type"] == "bomb_planted"][["round", "tick", "player_id_fixed"]]
              .dropna(subset=["round", "tick"]).astype({"round": "int64", "tick": "int64"})
              .rename(columns={"tick": "plant_tick", "player_id_fixed": "planter"}).sort_values("plant_tick"))
    site_of_place = {"BombsiteA": "A", "BombsiteB": "B"}
    if "place_name" in snap:
        at_plant = snap[["tick", "player_id_fixed", "place_name"]].assign(
            player_id_fixed=snap["player_id_fixed"].astype("float64"))
        plants = plants.assign(planter=plants["planter"].astype("float64")).merge(
            at_plant.rename(columns={"tick": "plant_tick", "player_id_fixed": "planter"}), on=["plant_tick", "planter"],
            how="left")
        plants["bomb_site"] = plants["place_name"].map(site_of_place)
    else:
        plants["bomb_site"] = None
    plants = plants[["round", "plant_tick", "bomb_site"]].drop_duplicates(["round", "plant_tick"])
    out = out.astype({"tick": "int64"}).sort_values("tick")
    out = pd.merge_asof(out, plants.assign(plant_tick_key=plants["plant_tick"]).rename(columns={"round": "plant_round"}),
                        left_on="tick", right_on="plant_tick_key", direction="backward")
    planted = out["plant_round"].eq(out["round"]).fillna(False).astype(bool)  # CSDS ints arrive nullable
    out["bomb_planted"] = planted
    out["bomb_site"] = out["bomb_site"].astype(object).where(planted & out["bomb_site"].notna(), None)
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
    pi_cols = {c["name"] for c_ in loader.manifest["channels"] if c_["channel"] == "player_info" for c in c_["columns"]}
    ch = loader.get_channels([
        {"channel": "player_info", "columns": [c for c in ["round", "player_id_fixed", "team_code", "rank", "rank_platform"]
                                               if c in pi_cols]},
        {"channel": "bomb_state", "columns": ["round", "tick", "event_type", "player_id_fixed"]},
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
    t = pd.read_parquet(root / "manifest" / "match_tiers.parquet")[["match_id", "tier", "tier_source"]]
    have = {p.stem for p in (root / "derived" / "snapshots").glob("*.parquet")}
    ids = set(match_ids) if match_ids is not None else have
    m = h[h["match_id"].isin(ids & have)].merge(q, on="match_id").merge(t, on="match_id", how="left")
    jobs = []
    for r in m.itertuples():
        ctx = {"match_id": r.match_id, "tick_rate": int(r.tick_rate), "map_name": r.map_name, "platform": r.platform,
               "tier": None if pd.isna(r.tier) else r.tier, "build_num": int(r.build_num), "channel_set": r.channel_set,
               "rank_scale": None if pd.isna(r.tier_source) else r.tier_source}
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
