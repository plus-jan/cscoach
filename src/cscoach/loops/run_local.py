"""Synthetic end-to-end run of the gated loop (M2.5 DoD; A-33: proves code correctness only).

Builds a scratch git repository with synthetic WP-like data and a task config, commits the champion, then walks a
fixed list of variants exactly like the autoresearch cycle: commit → Verify (``cscoach.loops.gated_verify``, champion
= HEAD~1) → Guard (``cscoach.loops.guard``) → keep iff lower bound > 0 and the guard passes, else ``git revert``.
Writes the loop ledger (TSV) and a summary to ``--out``.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

from cscoach.loops.sealed import make_split
from cscoach.loops.tasks import synthetic_wp_frame

GIT = ["git", "-c", "user.name=loop", "-c", "user.email=loop@example.invalid"]

VARIANTS = [
    ("add informative feature x2", {"features": ["x1", "x2"]}, "keep"),
    ("add noise feature", {"features": ["x1", "x2", "noise1"]}, "revert"),
    ("heavy regularisation C=0.0005", {"features": ["x1", "x2"], "C": 0.0005}, "revert"),
    ("miscalibrated output (+0.12)", {"features": ["x1", "x2", "noise2"], "miscalibrate": 0.12}, "revert"),
    ("add noise features 2+3", {"features": ["x1", "x2", "noise2", "noise3"]}, "revert"),
]


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True, help="scratch directory for the throwaway git repo")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20260928)
    args = ap.parse_args(argv)
    repo = args.repo
    if repo.exists():
        shutil.rmtree(repo)
    (repo / "configs").mkdir(parents=True)
    data = synthetic_wp_frame(n_matches=3000, rounds=12, snaps=1, seed=args.seed, match_sd=0.0)
    data.to_parquet(repo / "data.parquet", index=False)
    groups = data.drop_duplicates("match_id")[["match_id", "tier"]].rename(columns={"tier": "stratum"})
    split = make_split(groups, repo / "work", fractions={"train": 0.7, "calibration": 0.1, "test": 0.2}, k=5, seed=args.seed)
    cfg = {"loop": {"task": "synthetic_wp", "data": str(repo / "data.parquet"), "work_dir": str(repo / "work"),
                    "alpha": 0.05, "budget": 15, "n_resamples": 2000, "seed": args.seed,
                    "gates": {"ece_max": 0.02, "ece_max_per_stratum": 0.03, "min_rows_per_stratum": 500, "stratum": "tier"}},
           "model": {"features": ["x1"], "label": "y", "C": 1.0}}
    path = repo / "configs" / "synthetic_wp.yaml"
    path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    (repo / ".gitignore").write_text("work/\ndata.parquet\n")
    sh(["git", "init", "-q"], repo)
    sh(GIT + ["add", "-A"], repo)
    sh(GIT + ["commit", "-q", "-m", "champion: features x1"], repo)
    rows = []
    for i, (name, change, expected) in enumerate(VARIANTS, start=1):
        cur = yaml.safe_load(path.read_text())
        cur["model"] = {"label": "y", "C": 1.0, **{k: v for k, v in cur["model"].items() if k in ("label",)}, **change}
        path.write_text(yaml.safe_dump(cur, sort_keys=False))
        sh(GIT + ["commit", "-q", "-am", f"variant {i}: {name}"], repo)
        v = sh([sys.executable, "-m", "cscoach.loops.gated_verify", "--config", "configs/synthetic_wp.yaml"], repo)
        lb = float(v.stdout.strip().splitlines()[-1]) if v.returncode == 0 else float("nan")
        g = sh([sys.executable, "-m", "cscoach.loops.guard", "--config", "configs/synthetic_wp.yaml"], repo)
        keep = v.returncode == 0 and lb > 0 and g.returncode == 0
        if not keep:
            sh(GIT + ["revert", "--no-edit", "HEAD"], repo)
        rows.append({"iteration": i, "variant": name, "lower_bound": lb, "guard": "ok" if g.returncode == 0 else
                     " | ".join(l for l in g.stdout.splitlines() if l.startswith("GUARD FAIL")) or "failed",
                     "decision": "keep" if keep else "revert", "expected": expected})
    args.out.mkdir(parents=True, exist_ok=True)
    led = pd.DataFrame(rows)
    led.to_csv(args.out / "loop_ledger.tsv", sep="\t", index=False)
    shutil.copy(repo / "work" / "ledger.tsv", args.out / "verify_ledger.tsv")
    log = sh(["git", "log", "--oneline"], repo).stdout
    summary = {"variants": len(led), "kept": int((led["decision"] == "keep").sum()),
               "as_expected": bool((led["decision"] == led["expected"]).all()), "split_sha256": split["sha256"],
               "seed": args.seed, "alpha": 0.05, "budget": 15, "one_sided_level": 1 - 0.05 / 15, "n_resamples": 2000,
               "git_log": log.splitlines(), "note": "synthetic data (A-33): proves code correctness only"}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(led.to_string(index=False))
    print(json.dumps({k: summary[k] for k in ("variants", "kept", "as_expected")}))
    return 0 if summary["as_expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
