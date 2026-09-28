"""A-47 check: win reasons and bomb plants by map type (cs_ hostage vs de_ defusal) in the eligible WP matches.
Run: uv run python reports/experiments/20260928-2030_a47_map_modes/check.py <report_dir>. Data provided by PureSkill.gg."""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import yaml

from cscoach.models.wp_data import eligible

cfg = yaml.safe_load(open("configs/wp_split.yaml"))
root, out = Path(cfg["root"]), Path(sys.argv[1])
e = eligible(root).merge(pd.read_parquet(root / "manifest/match_quality.parquet", columns=["match_id", "map_name"]),
                         on="match_id")
e["kind"] = e["map_name"].str[:3]
rounds = pd.concat(ThreadPoolExecutor(16).map(
    lambda m: pd.read_parquet(root / "derived/rounds" / f"{m}.parquet", columns=["match_id", "win_reason_code"]),
    e["match_id"])).merge(e[["match_id", "kind"]], on="match_id")
ct = pd.crosstab(rounds["win_reason_code"].fillna(-1).astype(int), rounds["kind"])
ct.to_csv(out / "win_reason_by_map_kind.csv")
plants = {}
for m, k in zip(e["match_id"], e["kind"]):
    f = pd.read_parquet(root / "derived/state_features" / f"{m}.parquet", columns=["bomb_planted"])
    a = plants.setdefault(k, [0, 0]); a[0] += int(f["bomb_planted"].sum()); a[1] += len(f)
summary = {"commit": subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip(),
           "matches_by_kind": e["kind"].value_counts().to_dict(),
           "cs_maps": e.loc[e["kind"] == "cs_", "map_name"].value_counts().to_dict(),
           "rounds_by_kind": rounds["kind"].value_counts().to_dict(),
           "bomb_planted_snapshots": {k: {"planted": v[0], "rows": v[1]} for k, v in plants.items()},
           "win_reason_by_kind": {str(i): r.to_dict() for i, r in ct.iterrows()}}
(out / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=1))
