"""Rank decoding and match tier labels (M1.4).

Decoding (empirical, v42 matches with ``rank_type``; see the M1.4 report):
- Steam 5v5: ``rank_type`` 11 = Premier rating (observed minimum 1,206), 12 = Competitive skill group
  (1–18); Steam wingman: ``rank_type`` 7 = Wingman skill group. ``rank`` 0 = unranked/unknown.
- ``rank_type`` is null in older (v30) matches. All players of a match share one scale, and Premier
  ratings never fall in 1–18, so a 5v5 Steam match is Premier when any rank exceeds
  ``premier_min_rating - 1``, else Competitive. Where ``rank_type`` is present it wins.
- FACEIT: ``rank`` is 0; the level (1–10) is in ``rank_platform`` (0 = unknown).
- Unknown platform: no usable rank → tier null.

Match tier: median of the known player values on the match's scale, mapped with the cut-offs
(docs/specs/06, A-11), when at least ``min_known_players`` are known (A-12); otherwise null, never guessed.
Wingman matches get no tier (out of scope for the 5v5 models). Data provided by PureSkill.gg.
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

RANK_TYPE_SCALE = {11: "premier", 12: "competitive", 7: "wingman"}


def to_tier(value, scale: str, cfg: dict):
    if value is None or pd.isna(value):
        return None
    bounds = cfg["tier_cutoffs"][scale]
    idx = int(np.searchsorted(bounds, value, side="right"))
    return cfg["tiers"][idx]


def decode_players(pi: pd.DataFrame, platform: str, fmt: str, cfg: dict) -> pd.DataFrame:
    """One row per player (latest round): scale and value (null when unknown)."""
    last = pi.sort_values("round").groupby("player_id_fixed", dropna=False).tail(1)
    out = pd.DataFrame({"player_id": last["player_id_fixed"].to_numpy(), "raw_rank": last["rank"].to_numpy()})
    if platform == "faceit":
        out["scale"] = "faceit"
        lvl = last["rank_platform"].astype(float).to_numpy()
        out["value"] = np.where(lvl > 0, lvl, np.nan)
        return out
    if platform != "steam":
        out["scale"] = "unknown"
        out["value"] = np.nan
        return out
    types = pd.to_numeric(last["rank_type"], errors="coerce").dropna().astype(int)
    known_types = {RANK_TYPE_SCALE[t] for t in types if t in RANK_TYPE_SCALE}
    if fmt == "wingman":
        scale = "wingman"
    elif len(known_types) == 1:
        scale = known_types.pop()
    elif (last["rank"] >= cfg["premier_min_rating"]).any():
        scale = "premier"
    else:
        scale = "competitive"
    out["scale"] = scale
    out["value"] = np.where(last["rank"].to_numpy() > 0, last["rank"].to_numpy().astype(float), np.nan)
    return out


def match_tier(players: pd.DataFrame, cfg: dict) -> dict:
    scale = players["scale"].iloc[0] if len(players) else "unknown"
    known = players["value"].dropna()
    res = {"tier": None, "tier_source": scale, "n_players": int(len(players)), "n_known": int(len(known)),
           "median_value": float(known.median()) if len(known) else None, "tier_spread": None, "tier_reason": None}
    if scale == "wingman":
        res["tier_reason"] = "wingman"
    elif scale == "unknown":
        res["tier_reason"] = "platform_unknown"
    elif len(known) < cfg["min_known_players"]:
        res["tier_reason"] = "too_few_known"
    else:
        res["tier"] = to_tier(res["median_value"], scale, cfg)
        idx = [cfg["tiers"].index(to_tier(v, scale, cfg)) for v in known]
        res["tier_spread"] = int(max(idx) - min(idx))
        res["tier_reason"] = "ok"
    return res


# ---------------------------------------------------------------- I/O (official loaders)

def _one(args):
    root, key, match_id, platform, fmt, cfg = args
    import structlog

    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))
    from pureskillgg_dsdk.ds_io import DsReaderFs, GameDsLoader

    loader = GameDsLoader(reader=DsReaderFs(root_path=root, manifest_key=key))
    cols = {c["name"] for ch in loader.manifest["channels"] if ch["channel"] == "player_info" for c in ch["columns"]}
    want = [c for c in ["round", "player_id_fixed", "rank", "rank_type", "rank_platform"] if c in cols]
    pi = loader.get_channels([{"channel": "player_info", "columns": want}])["player_info"]
    for c in ("rank_type", "rank_platform"):
        if c not in pi:
            pi[c] = np.nan
    players = decode_players(pi, platform, fmt, cfg)
    explicit = pd.to_numeric(pi["rank_type"], errors="coerce").dropna().astype(int).unique().tolist()
    inferred = decode_players(pi.assign(rank_type=np.nan), platform, fmt, cfg)["scale"].iloc[0] if len(pi) else None
    return {"match_id": match_id, **match_tier(players, cfg), "rank_types_present": explicit,
            "scale_without_type": inferred}


def build(cfg: dict) -> pd.DataFrame:
    from cscoach.data.quality import curator

    root = Path(cfg["root"])
    q = pd.read_parquet(root / "manifest" / "match_quality.parquet")
    h = curator(cfg).get_dataframe(cfg["header_tome"])[["match_id", "key"]]
    todo = q[q["complete"].fillna(False).astype(bool) & q["is_canonical"]].merge(h, on="match_id")
    jobs = [(cfg["root"], k, m, p, f, cfg) for k, m, p, f in zip(todo["key"], todo["match_id"], todo["platform"], todo["format"])]
    with ProcessPoolExecutor(cfg.get("workers", 12)) as pool:
        rows = list(pool.map(_one, jobs, chunksize=16))
    return pd.DataFrame(rows).merge(
        q[["match_id", "platform", "format", "month", "channel_set", "clean", "in_seeded_sample", "map_name"]], on="match_id"
    )


def validate_scale_inference(t: pd.DataFrame) -> dict:
    """On matches that carry rank_type (v42), compare the type with the scale the type-free rule infers."""
    v = t[(t["platform"] == "steam") & (t["format"] == "5v5") & t["rank_types_present"].map(len).gt(0)].copy()
    v["type_scale"] = v["rank_types_present"].map(lambda ts: RANK_TYPE_SCALE.get(ts[0]) if len(ts) == 1 else "mixed")
    agree = v["type_scale"] == v["scale_without_type"]
    known = v["n_known"] > 0  # all-unranked matches carry no information either way
    return {
        "checked": int(len(v)),
        "type_scales": v["type_scale"].value_counts().to_dict(),
        "agree_all": int(agree.sum()),
        "agree_with_any_known_rank": [int((agree & known).sum()), int(known.sum())],
        "disagreements": v.loc[~agree, ["type_scale", "scale_without_type"]].value_counts().to_dict(),
    }


def report(t: pd.DataFrame, out_dir: Path, meta: dict, inference_check: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    five = t[t["format"] == "5v5"]
    cov = (five.assign(tier=five["tier"].fillna("null"))
           .groupby(["platform", "tier_source", "tier"]).size().rename("matches").reset_index())
    cov.to_csv(out_dir / "tier_coverage.csv", index=False)
    clean_seeded = five[five["clean"] & five["in_seeded_sample"].fillna(False).astype(bool)]
    summary = {
        **meta,
        "matches_checked": int(len(t)),
        "format": t["format"].value_counts().to_dict(),
        "tier_reason_5v5": five["tier_reason"].value_counts().to_dict(),
        "tier_by_platform_5v5": {p: g["tier"].fillna("null").value_counts().to_dict() for p, g in five.groupby("platform")},
        "tier_source_5v5": five["tier_source"].value_counts().to_dict(),
        "clean_seeded_5v5_by_tier": clean_seeded["tier"].fillna("null").value_counts().to_dict(),
        "tier_spread_5v5": five["tier_spread"].value_counts(dropna=False).sort_index().to_dict(),
        "n_known_5v5_quantiles": five["n_known"].quantile([0.1, 0.5, 0.9]).to_dict(),
        "scale_inference_check": inference_check,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/tiers.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    t = build(cfg)
    t.to_parquet(Path(cfg["root"]) / "manifest" / "match_tiers.parquet", index=False)
    report(t, args.report_dir, args.meta, validate_scale_inference(t))
    print(json.dumps({"matches": len(t), "with_tier": int(t["tier"].notna().sum())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
