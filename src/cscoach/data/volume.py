"""Data volume check against the targets (M1.5, A-32, A-07).

The full-channel data is a seeded random sample of fraction ``f`` (F-01), so expected counts at another
fraction ``f'`` are ``count × f'/f`` (the sample is nested: raising the fraction only adds matches). For every
stratum we report the matches and rounds available now, the expected test-split rounds, and the smallest
fraction that meets both targets (``inf`` when even 1.0 is not enough). The download size for a fraction is
computed exactly from the ADX asset index.

Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def fraction_needed(count: float, current_fraction: float, target: float) -> float:
    if count <= 0:
        return float("inf")
    f = max(current_fraction, current_fraction * target / count)
    return f if f <= 1.0 else float("inf")


def gap_table(df: pd.DataFrame, dims: list[str], *, current_fraction: float, targets: dict) -> pd.DataFrame:
    g = df.groupby(dims, dropna=False).agg(matches=("rounds", "size"), rounds=("rounds", "sum")).reset_index()
    share = targets["test_share"]
    g["test_rounds_expected"] = g["rounds"] * share
    g["fraction_needed_matches"] = [
        fraction_needed(m, current_fraction, targets["min_matches_per_bucket"]) for m in g["matches"]
    ]
    g["fraction_needed_rounds"] = [
        fraction_needed(r * share, current_fraction, targets["min_test_rounds_per_stratum"]) for r in g["rounds"]
    ]
    g["fraction_needed"] = g[["fraction_needed_matches", "fraction_needed_rounds"]].max(axis=1)
    g["meets_targets"] = g["fraction_needed"] <= current_fraction + 1e-12
    return g


def download_size(assets: pd.DataFrame, local_sizes: dict[str, int], *, seed: int, fraction: float) -> float:
    """GB still to download for a given full-channel fraction (exact, from the ADX asset index)."""
    from cscoach.data.export import plan_export

    return float(plan_export(assets, local_sizes=local_sizes, seed=seed, fraction=fraction)["size"].sum() / 1e9)


def analysis_frame(root: Path) -> pd.DataFrame:
    """Clean, canonical 5v5 matches of the seeded sample with tier and round count."""
    q = pd.read_parquet(root / "manifest" / "match_quality.parquet")
    t = pd.read_parquet(root / "manifest" / "match_tiers.parquet")[["match_id", "tier", "tier_source"]]
    df = q[q["clean"] & q["in_seeded_sample"].fillna(False).astype(bool)].merge(t, on="match_id", how="left")
    df["rounds"] = (df["final_hi"] + df["final_lo"]).astype(int)
    df["tier"] = df["tier"].fillna("null")
    return df


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/volume.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    exp = yaml.safe_load(Path(cfg["export_config"]).read_text())
    root, f0 = Path(exp["root"]), exp["full_channel_fraction"]
    df = analysis_frame(root)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    targets = cfg["targets"]
    tables = {}
    for name, dims in cfg["strata"].items():
        g = gap_table(df, dims, current_fraction=f0, targets=targets)
        g.to_csv(args.report_dir / f"gap_{name}.csv", index=False)
        tables[name] = g
    # download size per candidate fraction (exact)
    from cscoach.data.export import local_sizes

    assets = pd.read_parquet(root / "manifest" / "adx_assets.parquet")
    sizes = local_sizes(root, assets["name"])
    cost = {
        str(f): {"gb": round(download_size(assets, sizes, seed=exp["sample_seed"], fraction=f), 1),
                 "usd_egress": None}
        for f in cfg["candidate_fractions"]
    }
    for v in cost.values():
        v["usd_egress"] = round(v["gb"] * exp["egress_usd_per_gb"], 0)
    tiered = df[df["tier"] != "null"]
    summary = {
        **args.meta,
        "current_fraction": f0,
        "targets": targets,
        "clean_seeded_5v5_matches": int(len(df)),
        "clean_seeded_5v5_tiered": int(len(tiered)),
        "maps_with_ge_300": int((df["map_name"].value_counts() >= targets["min_matches_per_bucket"]).sum()),
        "strata_meeting_targets": {k: [int(g["meets_targets"].sum()), int(len(g))] for k, g in tables.items()},
        "fraction_needed_max_over_tier_platform_excl_null": float(
            tables["tier_platform"].query("tier != 'null'")["fraction_needed"].max()
        ),
        "download_by_fraction": cost,
    }
    (args.report_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
