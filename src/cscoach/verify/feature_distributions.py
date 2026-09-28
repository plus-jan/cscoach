"""M2.3 report: state-feature distributions per platform × tier (docs/specs/02; DoD "feature distributions per
tier/platform in PROGRESS"). Descriptive only; matches are the unit (per-match means first, then quantiles across
matches), so long matches do not dominate. Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

FREEZE = ["ct_equip_value", "t_equip_value", "ct_money_sum", "t_money_sum", "ct_primaries", "t_primaries",
          "ct_kits", "ct_armor_sum", "t_armor_sum", "ct_flashes", "t_flashes", "ct_smokes", "t_smokes"]
ROUND = ["man_advantage", "ct_alive", "t_alive", "ct_hp_sum", "t_hp_sum", "time_remaining_s", "second_in_round"]


def per_match(path: str) -> dict:
    cols = ["match_id", "round_uid", "tick", "second_in_round", "bomb_planted", "bomb_site", "platform", "tier",
            "channel_set", "n_players_no_side", *FREEZE, *ROUND]
    d = pd.read_parquet(path, columns=list(dict.fromkeys(cols)))
    fe = d[d["second_in_round"] == 0]
    last = d.sort_values("tick").groupby("round_uid").tail(1)
    out = {"match_id": d["match_id"].iloc[0], "platform": d["platform"].iloc[0], "tier": d["tier"].iloc[0] or "null",
           "channel_set": d["channel_set"].iloc[0], "rounds": int(d["round_uid"].nunique()), "snapshots": int(len(d)),
           "fe_5v5_share": float(((fe["ct_alive"] == 5) & (fe["t_alive"] == 5)).mean()) if len(fe) else np.nan,
           "plant_round_share": float(d.groupby("round_uid")["bomb_planted"].any().mean()),
           "site_a_share": float((last.loc[last["bomb_planted"], "bomb_site"] == "A").mean()) if last["bomb_planted"].any() else np.nan,
           "no_side_share": float((d["n_players_no_side"] > 0).mean()),
           "round_length_s": float(last["second_in_round"].median()),
           "time_remaining_neg_share": float((d["time_remaining_s"] < 0).mean())}
    for c in FREEZE:
        out[f"fe_{c}"] = float(fe[c].mean()) if len(fe) else np.nan
    for c in ("man_advantage", "ct_alive", "t_alive", "ct_hp_sum", "t_hp_sum"):
        out[f"all_{c}"] = float(d[c].mean())
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/features.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    root = Path(cfg["root"])
    files = sorted(str(p) for p in (root / "derived" / "state_features").glob("*.parquet"))
    with ProcessPoolExecutor(cfg.get("workers", 12)) as pool:
        m = pd.DataFrame(list(pool.map(per_match, files, chunksize=32)))
    q = pd.read_parquet(root / "manifest" / "match_quality.parquet")[["match_id", "clean", "in_seeded_sample"]]
    m = m.merge(q, on="match_id", how="left")
    m = m[m["clean"].fillna(False).astype(bool) & m["in_seeded_sample"].fillna(False).astype(bool)]
    args.report_dir.mkdir(parents=True, exist_ok=True)
    m.to_csv(args.report_dir / "per_match.csv", index=False)
    order = ["low", "mid", "high", "semipro", "null"]
    m["tier"] = pd.Categorical(m["tier"], order)
    g = m.groupby(["platform", "tier"], observed=True)
    table = g.agg(matches=("match_id", "size"), rounds=("rounds", "sum"), snapshots=("snapshots", "sum"),
                  **{c: (c, "median") for c in m.columns if c.startswith(("fe_", "all_")) or c in (
                      "plant_round_share", "site_a_share", "round_length_s", "no_side_share")}).reset_index()
    table.round(3).to_csv(args.report_dir / "distributions_platform_tier.csv", index=False)
    summary = {**args.meta, "matches": int(len(m)), "rounds": int(m["rounds"].sum()), "snapshots": int(m["snapshots"].sum()),
               "fe_5v5_share_median": float(m["fe_5v5_share"].median()),
               "time_remaining_neg_share_mean": float(m["time_remaining_neg_share"].mean()),
               "no_side_share_mean": float(m["no_side_share"].mean()),
               "by_channel_set_matches": m["channel_set"].value_counts().to_dict()}
    (args.report_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    cols = ["platform", "tier", "matches", "rounds", "fe_ct_equip_value", "fe_t_equip_value", "fe_ct_money_sum",
            "plant_round_share", "site_a_share", "round_length_s", "all_man_advantage"]
    print(table[cols].round(3).to_string(index=False))
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
