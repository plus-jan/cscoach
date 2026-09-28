"""Guard for modelling loops (docs/specs/07 §2): a failing guard means revert, whatever the metric says.

Checks: the split file is unchanged (hash) and complete/disjoint; no sealed match appears in the access log; the
candidate's out-of-fold predictions pass the ECE gates overall and per stratum (docs/specs/06, A-06); optionally the
leakage tests (``--pytest``). Exit code 0 = pass.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

from cscoach.eval.metrics import ece
from cscoach.loops.sealed import SEALED, load_split, split_hash_ok

LEAKAGE_TESTS = ["tests/cscoach/test_snapshots.py", "tests/cscoach/test_features.py", "tests/cscoach/test_leakage_audit.py"]


def run_checks(work_dir: Path, *, oof: pd.DataFrame | None, gates: dict | None) -> dict:
    work_dir = Path(work_dir)
    fails = []
    body = load_split(work_dir)
    if not split_hash_ok(body):
        fails.append("split.json changed since the loop started (hash mismatch)")
    if set(body["split"].values()) - {"train", *SEALED}:
        fails.append("unknown split names")
    train = {m for m, s in body["split"].items() if s == "train"}
    if set(body["folds"]) != train:
        fails.append("folds do not cover exactly the training matches")
    log = work_dir / "access.log"
    if log.exists():
        read = set(log.read_text().split())
        sealed = sorted(m for m in read if body["split"].get(m) in SEALED)
        if sealed:
            fails.append(f"sealed matches were read: {len(sealed)} (e.g. {sealed[:3]})")
        unknown = sorted(read - set(body["split"]))
        if unknown:
            fails.append(f"matches outside the split were read: {len(unknown)}")
    if oof is not None and gates:
        e = ece(oof["p"], oof["y"])
        if e > gates["ece_max"]:
            fails.append(f"ECE {e:.4f} > {gates['ece_max']} overall")
        for st, g in oof.groupby(gates["stratum"]):
            if len(g) >= gates["min_rows_per_stratum"]:
                es = ece(g["p"], g["y"])
                if es > gates["ece_max_per_stratum"]:
                    fails.append(f"ECE {es:.4f} > {gates['ece_max_per_stratum']} in stratum {st}")
    return {"ok": not fails, "failures": fails}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--pytest", action="store_true", help="also run the leakage tests")
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    work = Path(cfg["loop"]["work_dir"])
    oof_path = work / "candidate_oof.parquet"
    oof = pd.read_parquet(oof_path) if oof_path.exists() else None
    res = run_checks(work, oof=oof, gates=cfg["loop"].get("gates"))
    if args.pytest:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", *LEAKAGE_TESTS], capture_output=True, text=True)
        if r.returncode != 0:
            res["ok"] = False
            res["failures"].append("leakage tests failed")
    for f in res["failures"]:
        print(f"GUARD FAIL: {f}")
    print("GUARD OK" if res["ok"] else "GUARD FAILED")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
