"""Snapshot sampler and as-of join of ``player_status`` (M2.2).

Snapshot ticks per round (docs/specs/02 "snapshots"): every event tick of the configured channels plus a fixed
cadence (``cadence_s``, A-22) from the freeze-end tick (included) up to the round-end tick (excluded). Each
snapshot gets one row per player with the latest ``player_status`` row whose tick is ≤ the snapshot tick
(same round only; a row from another round is never carried over). ``staleness_ticks`` records the gap.

No future information: a snapshot's content depends only on rows with tick ≤ its tick. The round-end tick
only bounds *which* ticks are sampled (a snapshot at t exists iff t < end), and truncating every input at T
leaves all snapshots ≤ T unchanged (``truncate`` + the leakage test). Labels are attached later (M2.3/M3).

Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def sample_ticks(rounds: pd.DataFrame, events: dict[str, pd.DataFrame], *, tick_rate: int, cadence_s: float) -> pd.DataFrame:
    step = max(1, int(round(cadence_s * tick_rate)))
    parts = []
    for rnd, fe, end in zip(rounds["round"], rounds["freeze_end_tick"], rounds["end_tick"]):
        if pd.isna(fe) or pd.isna(end):
            continue
        fe, end = int(fe), int(end)
        ticks = np.arange(fe, end, step)
        parts.append(pd.DataFrame({"round": rnd, "tick": ticks, "source": "cadence"}))
        for name, ev in events.items():
            t = ev.loc[(ev["round"] == rnd) & (ev["tick"] >= fe) & (ev["tick"] < end), "tick"].unique()
            if len(t):
                parts.append(pd.DataFrame({"round": rnd, "tick": t, "source": name}))
    if not parts:
        return pd.DataFrame({"round": pd.Series(dtype=int), "tick": pd.Series(dtype=int), "source": pd.Series(dtype=str)})
    s = pd.concat(parts, ignore_index=True)
    s = (s.groupby(["round", "tick"], as_index=False)["source"]
         .agg(lambda x: "|".join(sorted(set(x), key=lambda v: (v != "cadence", v)))))
    s["tick"] = s["tick"].astype("int64")
    return s.sort_values(["round", "tick"]).reset_index(drop=True)


def asof_join(snaps: pd.DataFrame, status: pd.DataFrame, columns: list[str], deaths: pd.DataFrame) -> pd.DataFrame:
    """``player_status`` has no rows for dead players (they resume ~20 ticks after the round end), so the
    last alive row would be carried forward. A player is dead from a ``player_death`` (same round, tick ≤ t)
    until a later status row; dead players get ``is_alive = False`` and masked state columns."""
    players = status["player_id_fixed"].dropna().unique()
    grid = snaps.merge(pd.DataFrame({"player_id_fixed": players}), how="cross").sort_values("tick")
    st = (status[["tick", "round", "player_id_fixed", *columns]]
          .rename(columns={"round": "status_round"})
          .assign(status_tick=lambda d: d["tick"].astype("int64"), tick=lambda d: d["tick"].astype("int64"))
          .sort_values("tick"))
    grid["tick"] = grid["tick"].astype("int64")
    j = pd.merge_asof(grid, st, on="tick", by="player_id_fixed", direction="backward", allow_exact_matches=True)
    for c in columns:  # fixed dtypes, independent of which rows exist (nullable ints arrive as doubles anyway)
        if pd.api.types.is_bool_dtype(j[c]) or str(j[c].dtype) == "boolean":
            j[c] = j[c].astype("boolean")
        elif pd.api.types.is_numeric_dtype(j[c]):
            j[c] = j[c].astype("float64")
    de = (deaths[["round", "tick", "player_id_fixed"]].dropna()
          .rename(columns={"round": "death_round"})
          .assign(death_tick=lambda d: d["tick"].astype("int64"), tick=lambda d: d["tick"].astype("int64"))
          .sort_values("tick"))
    j = pd.merge_asof(j.sort_values("tick"), de, on="tick", by="player_id_fixed", direction="backward",
                      allow_exact_matches=True)
    died = j["death_round"].eq(j["round"]) & (j["death_tick"] >= j["status_tick"])
    j["is_alive"] = ~died
    other = j["status_round"].notna() & (j["status_round"] != j["round"])
    j["status_other_round"] = other | j["status_round"].isna()
    for c in columns:
        j[c] = j[c].mask(j["status_other_round"] | ~j["is_alive"])
    # a player with no status row at or before the snapshot tick is not known yet: no row (a row would
    # reveal a future player)
    j = j[j["status_tick"].notna()].copy()
    j["status_tick"] = j["status_tick"].astype("Int64")
    j["staleness_ticks"] = (j["tick"] - j["status_tick"]).where(~j["status_other_round"] & j["is_alive"]).astype("Int64")
    j = j.drop(columns=["status_round", "death_round", "death_tick"])
    return j.sort_values(["round", "tick", "player_id_fixed"]).reset_index(drop=True)


def snapshots(rounds, events, status, columns, deaths, *, tick_rate, cadence_s):
    return asof_join(sample_ticks(rounds, events, tick_rate=tick_rate, cadence_s=cadence_s), status, columns, deaths)


def truncate(rounds: pd.DataFrame, events: dict, status: pd.DataFrame, cut: int, deaths: pd.DataFrame):
    """Drop every row after ``cut`` (the round end becomes unknown for rounds still running at ``cut``)."""
    r = rounds[rounds["freeze_end_tick"] <= cut].copy()
    r["end_tick"] = np.minimum(r["end_tick"], cut + 1)  # still running: window bounded by what is known
    ev = {k: v[v["tick"] <= cut] for k, v in events.items()}
    return r, ev, status[status["tick"] <= cut], deaths[deaths["tick"] <= cut]


# ---------------------------------------------------------------- I/O (official loaders)

def _one(args):
    root, key, match_id, rounds_path, cfg, out_dir, check_leakage, seed = args
    import structlog

    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))
    from pureskillgg_dsdk.ds_io import DsReaderFs, GameDsLoader

    t0 = time.perf_counter()
    loader = GameDsLoader(reader=DsReaderFs(root_path=root, manifest_key=key))
    have = {c["channel"] for c in loader.manifest["channels"]}
    ev_names = [c for c in cfg["event_channels"] if c in have]
    status_cols = {c["name"] for ch_ in loader.manifest["channels"] if ch_["channel"] == "player_status"
                   for c in ch_["columns"]}
    cols = [c for c in cfg["status_columns"] if c in status_cols]  # driven by the per-match index
    ch = loader.get_channels(
        [{"channel": c, "columns": ["round", "tick", "player_id_fixed"] if c == "player_death" else ["round", "tick"]}
         for c in ev_names]
        + [{"channel": "player_status", "columns": ["round", "tick", "player_id_fixed", *cols]}]
    )
    tick_rate = int(loader.get_channel({"channel": "header", "columns": ["tick_rate"]})["tick_rate"].iloc[0])
    rounds = pd.read_parquet(rounds_path, columns=["round", "freeze_end_tick", "end_tick"])
    events = {c: ch[c] for c in ev_names}
    deaths = ch["player_death"]
    snap = snapshots(rounds, events, ch["player_status"], cols, deaths, tick_rate=tick_rate,
                     cadence_s=cfg["cadence_s"])
    snap.insert(0, "match_id", match_id)
    snap.to_parquet(Path(out_dir) / f"{match_id}.parquet", index=False)
    secs = time.perf_counter() - t0
    res = {"match_id": match_id, "missing_status_columns": ";".join(sorted(set(cfg["status_columns"]) - set(cols))),
           "snapshots": int(snap[["round", "tick"]].drop_duplicates().shape[0]),
           "rows": int(len(snap)), "seconds": round(secs, 3), "tick_rate": tick_rate,
           "alive_share": float(snap["is_alive"].mean()),
           "stale_median": float(snap["staleness_ticks"].median()), "stale_p99": float(snap["staleness_ticks"].quantile(0.99)),
           "stale_max": float(snap["staleness_ticks"].max()), "other_round_share": float(snap["status_other_round"].mean()),
           "event_share": float(snap.drop_duplicates(["round", "tick"])["source"].ne("cadence").mean())}
    if check_leakage:  # real-data leakage check at 5 random cut ticks inside rounds
        rng = np.random.default_rng(seed)
        ticks = snap["tick"].unique()
        cuts = rng.choice(ticks, size=min(5, len(ticks)), replace=False)
        ok = True
        for cut in cuts:
            r2, e2, s2, d2 = truncate(rounds, events, ch["player_status"], int(cut), deaths)
            part = snapshots(r2, e2, s2, cols, d2, tick_rate=tick_rate, cadence_s=cfg["cadence_s"])
            a = snap[snap["tick"] <= cut].drop(columns="match_id").reset_index(drop=True)
            b = part[part["tick"] <= cut].reset_index(drop=True)
            ok &= a.equals(b)
        res["leakage_check_ok"] = bool(ok)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/snapshots.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--sample", type=int, default=0, help="number of matches (0 = all eligible)")
    ap.add_argument("--meta", type=json.loads, default={})
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    from cscoach.data.quality import curator

    root = Path(cfg["root"])
    out_dir = root / "derived" / "snapshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    chk = pd.read_parquet(root / "manifest" / "rounds_check.parquet")
    elig = chk[chk["ok"] & chk["clean"] & chk["in_seeded_sample"].fillna(False).astype(bool)]
    if args.sample:
        elig = elig.sample(min(args.sample, len(elig)), random_state=cfg["seed"])
    h = curator(cfg).get_dataframe(cfg["header_tome"])[["match_id", "key"]]
    todo = elig.merge(h, on="match_id")
    jobs = [(cfg["root"], k, m, str(root / "derived" / "rounds" / f"{m}.parquet"), cfg, str(out_dir), True, cfg["seed"] + i)
            for i, (k, m) in enumerate(zip(todo["key"], todo["match_id"]))]
    with ProcessPoolExecutor(cfg.get("workers", 12)) as pool:
        res = pd.DataFrame(list(pool.map(_one, jobs, chunksize=4)))
    args.report_dir.mkdir(parents=True, exist_ok=True)
    res.to_csv(args.report_dir / "per_match.csv", index=False)
    summary = {
        **args.meta,
        "matches": int(len(res)),
        "snapshots_total": int(res["snapshots"].sum()),
        "snapshots_per_match": res["snapshots"].describe()[["mean", "50%", "min", "max"]].round(1).to_dict(),
        "player_rows_total": int(res["rows"].sum()),
        "event_snapshot_share_mean": round(float(res["event_share"].mean()), 3),
        "staleness_ticks": {"median_of_match_medians": float(res["stale_median"].median()),
                            "p99_of_match_p99": float(res["stale_p99"].quantile(0.99)),
                            "max": float(res["stale_max"].max())},
        "status_other_round_share_mean": round(float(res["other_round_share"].mean()), 4),
        "tick_rates": res["tick_rate"].value_counts().to_dict(),
        "seconds_per_match": res["seconds"].describe()[["mean", "50%", "max"]].round(2).to_dict(),
        "leakage_check_ok": [int(res["leakage_check_ok"].sum()), int(len(res))],
    }
    (args.report_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
