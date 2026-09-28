"""Header tome dedup, quality flags and subheader tomes (M1.3).

Nothing is dropped and the raw collection is only read: duplicates and defects become **flags** in
``<root>/manifest/match_quality.parquet``; subheader tomes are derived copies of header rows.

- Header flags (every match, from the header tome): ``dedup_key`` (map, server, ``number_of_points``,
  final scores — no date, so a user re-upload with its upload date still matches), ``dup_n``,
  ``is_canonical`` (one copy per group: full channels first, then newest parser, then smallest id),
  ``format`` (5v5/wingman), ``final_state`` (regulation/draw/overtime/incomplete), ``month`` and ``q_*``.
- Channel flags (matches with all channels): ``round_end`` present and consistent with the final score,
  warmup rows after the first round end, tick gaps, abandonment (a human disconnects before the last
  round end and never spawns again).

Parameters: ``configs/quality.yaml`` (docs/specs/06, assumptions A-13, A-36, A-40, A-43).
Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

DEDUP_COLUMNS = ["map_name", "server_name", "number_of_points", "t_starters_score_final", "ct_starters_score_final"]
CHANNELS = ["round_end", "round_state", "player_disconnect", "player_spawn"]


def final_state(a: int, b: int, fmt: str, cfg: dict) -> str:
    """Classify a final score: regulation win, draw, overtime result, or incomplete (anything else)."""
    hi, lo = max(a, b), min(a, b)
    need = cfg["wins_needed"][fmt]
    if hi == need and lo < need - 1:
        return "regulation"
    if hi == lo == need - 1:
        return "draw"
    if fmt == "5v5":
        # overtime from (need-1, need-1): blocks of 2*ot rounds, won with ot+1; ot all → next block
        ot, base = cfg["overtime_half_rounds"], need - 1
        extra = hi - base
        if hi == lo and extra > 0 and extra % ot == 0:
            return "draw"
        if lo >= base and extra > ot and (extra - ot - 1) % ot == 0 and hi - ot - 1 <= lo <= hi - 2:
            return "overtime"
    return "incomplete"


def _version_key(v) -> tuple:
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return ()


def header_flags(h: pd.DataFrame, complete: dict[str, bool], cfg: dict) -> pd.DataFrame:
    out = pd.DataFrame({"match_id": h["match_id"].to_numpy()})
    key_src = h[DEDUP_COLUMNS].astype(str).agg("|".join, axis=1)
    out["dedup_key"] = key_src.map(lambda s: hashlib.sha256(s.encode()).hexdigest()[:16]).to_numpy()
    out["dup_n"] = out.groupby("dedup_key")["match_id"].transform("size")

    rank = pd.DataFrame({
        "key": out["dedup_key"],
        "complete": out["match_id"].map(lambda m: bool(complete.get(m, False))),
        "ppp": h["ppp_version"].map(_version_key).to_numpy(),
        "match_id": out["match_id"],
    }).sort_values(["key", "complete", "ppp", "match_id"], ascending=[True, False, False, True])
    canonical = set(rank.drop_duplicates("key")["match_id"])
    out["is_canonical"] = out["match_id"].isin(canonical)

    wing_flag = h["is_wingman"].map(lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else bool(v))
    proxy = h["unique_steamids"] <= cfg["wingman_max_unique_steamids"]
    out["format"] = np.where(wing_flag.isna(), np.where(proxy, "wingman", "5v5"),
                             np.where(wing_flag.fillna(False).astype(bool), "wingman", "5v5"))
    out["final_state"] = [
        final_state(int(a), int(b), f, cfg)
        for a, b, f in zip(h["t_starters_score_final"], h["ct_starters_score_final"], out["format"])
    ]
    out["month"] = h["match_date"].str[:7].to_numpy()
    out["platform"] = h["platform"].to_numpy()
    out["map_name"] = h["map_name"].to_numpy()
    out["rank_known"] = (h["t_starters_avg_rank"].fillna(0) > 0).to_numpy()
    out["q_platform_unknown"] = (h["platform"] == "unknown").to_numpy()
    out["q_upload_date"] = (h["providence"] == "user").to_numpy()
    expected = np.where(out["format"] == "wingman", 4, 10)
    out["q_player_count"] = h["unique_steamids"].to_numpy() != expected
    out["q_incomplete"] = out["final_state"] == "incomplete"
    return out


def channel_flags(ch: dict[str, pd.DataFrame], *, tick_rate: int, cfg: dict) -> dict:
    """Flags from the channels. Final scores come from the last ``round_state`` row, because the header's
    loser score is unreliable (F-02)."""
    re_, rs, tk = ch["round_end"], ch["round_state"], ch["tick"]
    dc, sp = ch["player_disconnect"], ch["player_spawn"]
    n_re = int(re_["round"].nunique()) if len(re_) else 0
    first_end = re_["tick"].min() if len(re_) else None
    last_end = re_["tick"].max() if len(re_) else None
    warm = rs.loc[rs["is_warmup"].astype(bool), "tick"]
    last = rs.sort_values("tick").iloc[-1] if len(rs) else None
    hi = int(max(last["t_score"], last["ct_score"])) if last is not None else 0
    lo = int(min(last["t_score"], last["ct_score"])) if last is not None else 0
    ticks = np.sort(tk["tick"].unique())
    max_gap = float(np.diff(ticks).max()) / tick_rate if len(ticks) > 1 else float("nan")

    # abandonment: a human leaves, at least one later round is played, and they never spawn again
    # (leaving during the final round, once the match is decided, is normal)
    abandon = False
    if last_end is not None and len(dc):
        last_round = re_["round"].max()
        humans = dc[~dc["is_bot"].astype(bool)]
        for t, r, pid in zip(humans["tick"], humans["round"], humans["player_id_fixed"]):
            if r < last_round and not ((sp["player_id_fixed"] == pid) & (sp["tick"] > t)).any():
                abandon = True
                break
    return {
        "n_round_end": n_re,
        "final_hi": hi,
        "final_lo": lo,
        "q_no_round_end": n_re == 0,
        "q_rounds_vs_score": n_re != hi + lo,
        "q_warmup_after_start": bool(first_end is not None and (warm > first_end).any()),
        "max_tick_gap_s": max_gap,
        "q_tick_gap": bool(max_gap > cfg["max_tick_gap_s"]),
        "q_abandonment": abandon,
    }


# ---------------------------------------------------------------- I/O (official loaders)

def _quiet_logs():
    import structlog

    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))


def apply_round_state_scores(q: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Where channel scores exist, recompute ``final_state`` from them; record the source."""
    q = q.copy()
    has = q["final_hi"].notna()
    q["final_state_source"] = np.where(has, "round_state", "header")
    q.loc[has, "final_state"] = [
        final_state(int(a), int(b), f, cfg) for a, b, f in zip(q.loc[has, "final_hi"], q.loc[has, "final_lo"], q.loc[has, "format"])
    ]
    q["q_incomplete"] = q["final_state"] == "incomplete"
    return q


def _load_match(args):
    root, key, tick_rate, cfg = args
    _quiet_logs()
    from pureskillgg_dsdk.ds_io import DsReaderFs, GameDsLoader

    loader = GameDsLoader(reader=DsReaderFs(root_path=root, manifest_key=key))
    have = {c["channel"] for c in loader.manifest["channels"]}
    want = [{"channel": c} for c in CHANNELS if c in have]
    if "tick" in have:
        want.append({"channel": "tick", "columns": ["tick"]})
    try:
        ch = loader.get_channels(want)
    except Exception as err:  # unreadable channel → report, don't guess
        return {"key": key, "channel_error": repr(err)[:200]}
    for c, cols in (("player_spawn", ["tick", "player_id_fixed"]), ("tick", ["tick"])):
        ch.setdefault(c, pd.DataFrame(columns=cols))
    return {"key": key, "channel_error": None,
            **channel_flags(ch, tick_rate=tick_rate, cfg=cfg)}


def curator(cfg):
    from pureskillgg_dsdk.tome import TomeCuratorFs

    return TomeCuratorFs(
        ds_type="csds", tome_collection_root_path=cfg["tome_root"], ds_collection_root_path=cfg["root"],
        default_header_name=cfg["header_tome"],
    )


def build(cfg: dict) -> pd.DataFrame:
    _quiet_logs()
    root = Path(cfg["root"])
    h = curator(cfg).get_dataframe(cfg["header_tome"])
    manifest = pd.read_parquet(root / "manifest" / "matches.parquet")
    complete = dict(zip(manifest["match_id"], manifest["complete"].astype(bool)))
    flags = header_flags(h, complete, cfg)
    flags = flags.merge(
        manifest[["match_id", "channel_set", "complete", "in_seeded_sample", "revision_id", "adx_revision_date"]],
        on="match_id", how="left",
    )
    full = h[h["match_id"].map(complete).fillna(False).astype(bool)]
    jobs = [(cfg["root"], k, int(tr), cfg) for k, tr in zip(full["key"], full["tick_rate"])]
    with ProcessPoolExecutor(cfg.get("workers", 12)) as pool:
        rows = list(pool.map(_load_match, jobs, chunksize=16))
    ch = pd.DataFrame(rows).merge(h[["key", "match_id"]], on="key").drop(columns="key")
    q = flags.merge(ch, on="match_id", how="left")
    hdr_lo = h.set_index("match_id")[["t_starters_score_final", "ct_starters_score_final"]].min(axis=1)
    q["q_header_loser_score"] = q["final_lo"].notna() & (q["match_id"].map(hdr_lo) != q["final_lo"])
    return apply_round_state_scores(q, cfg)


HEADER_DEFECTS = ["q_platform_unknown", "q_player_count", "q_incomplete"]
CHANNEL_DEFECTS = ["q_no_round_end", "q_rounds_vs_score", "q_warmup_after_start", "q_tick_gap", "q_abandonment"]


def add_clean(q: pd.DataFrame) -> pd.DataFrame:
    """``clean``: canonical 5v5 copy without header defects; channel defects count where known."""
    q = q.copy()
    ch_bad = q[CHANNEL_DEFECTS].fillna(False).astype(bool).any(axis=1) | q["channel_error"].notna()
    q["clean"] = q["is_canonical"] & (q["format"] == "5v5") & ~q[HEADER_DEFECTS].any(axis=1) & ~ch_bad
    return q


SUBHEADERS = {
    # name suffix → selector on the quality table (subheader tomes are copies of header rows)
    "clean": lambda q: q["clean"],
    "clean_full_seeded": lambda q: q["clean"] & q["in_seeded_sample"].fillna(False).astype(bool),
    "clean_steam": lambda q: q["clean"] & (q["platform"] == "steam"),
    "clean_faceit": lambda q: q["clean"] & (q["platform"] == "faceit"),
    "clean_v30": lambda q: q["clean"] & (q["channel_set"] == "v30"),
    "clean_v42": lambda q: q["clean"] & (q["channel_set"] == "v42"),
    "clean_rank_known": lambda q: q["clean"] & q["rank_known"],
}


def write_subheaders(cfg: dict, q: pd.DataFrame) -> dict[str, int]:
    c = curator(cfg)
    base = cfg["header_tome"].split(".", 1)[1].rsplit(".", 1)[0]  # date window
    counts = {}
    for suffix, sel in SUBHEADERS.items():
        ids = set(q.loc[sel(q), "match_id"])
        name = f"subheader.{base}.{suffix}"
        old = Path(cfg["tome_root"]) / "tome" / "csds" / name
        if old.is_dir():  # derived tome: rebuild from scratch so no stale pages remain
            shutil.rmtree(old)
        c.create_subheader_tome(name, lambda df, ids=ids: df["match_id"].isin(ids).to_numpy(),
                                src_tome_name=cfg["header_tome"])
        counts[name] = len(ids)
    return counts


def report(q: pd.DataFrame, out_dir: Path, meta: dict, sub_counts: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = (q.groupby(["platform", "map_name", "month", "channel_set"], dropna=False)
              .agg(matches=("match_id", "size"), canonical=("is_canonical", "sum"), clean=("clean", "sum"),
                   full_channels=("complete", lambda s: int(s.fillna(False).astype(bool).sum())))
              .reset_index())
    counts.to_csv(out_dir / "counts_platform_map_month_channelset.csv", index=False)
    flag_cols = ["q_platform_unknown", "q_upload_date", "q_player_count", "q_incomplete", *CHANNEL_DEFECTS,
                 "q_header_loser_score"]
    flags = {c: int(q[c].fillna(False).astype(bool).sum()) for c in flag_cols}
    flags["channel_error"] = int(q["channel_error"].notna().sum())
    summary = {
        **meta,
        "matches": int(len(q)),
        "dedup_groups_with_copies": int((q.groupby("dedup_key").size() > 1).sum()),
        "duplicate_rows_non_canonical": int((~q["is_canonical"]).sum()),
        "canonical": int(q["is_canonical"].sum()),
        "format": q.loc[q["is_canonical"], "format"].value_counts().to_dict(),
        "final_state_canonical": q.loc[q["is_canonical"], "final_state"].value_counts().to_dict(),
        "final_state_source_canonical": q.loc[q["is_canonical"], "final_state_source"].value_counts().to_dict(),
        "channel_checked": int(q["n_round_end"].notna().sum()),
        "flags_all_rows": flags,
        "clean": int(q["clean"].sum()),
        "clean_by_platform": q.loc[q["clean"], "platform"].value_counts().to_dict(),
        "clean_by_channel_set": q.loc[q["clean"], "channel_set"].value_counts().to_dict(),
        "subheader_tomes": sub_counts,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/quality.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={}, help="JSON with commit/config hash for the report")
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    q = add_clean(build(cfg))
    q.to_parquet(Path(cfg["root"]) / "manifest" / "match_quality.parquet", index=False)
    sub = write_subheaders(cfg, q)
    report(q, args.report_dir, args.meta, sub)
    print(json.dumps({"matches": len(q), "canonical": int(q["is_canonical"].sum()), "clean": int(q["clean"].sum())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
