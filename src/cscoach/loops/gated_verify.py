"""Gated Verify for modelling loops (docs/specs/07 §2, A-42).

Prints ONE number: the lower bound of the one-sided cluster-bootstrap CI (clusters = matches) of the log-loss
improvement of the candidate over the champion on pooled out-of-fold predictions of the **training matches only**,
at level 1 − alpha/budget. Keep iff > 0. The champion is the task config at ``--champion-ref`` (default HEAD~1, the
last kept state in the autoresearch commit → verify → keep/revert cycle); the candidate is the working-tree config.
Every run appends a ledger row (raw delta, lower bound, seeds) to ``<work_dir>/ledger.tsv``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from cscoach.eval.metrics import logloss_rows


def improvement_lower_bound(champ: pd.DataFrame, cand: pd.DataFrame, *, alpha: float, budget: int,
                            n_resamples: int, seed: int) -> dict:
    a = champ.reset_index(drop=True)
    b = cand.reset_index(drop=True)
    if not (a["match_id"].equals(b["match_id"]) and a["y"].equals(b["y"])):
        raise ValueError("champion and candidate predictions must cover the same rows in the same order")
    d = logloss_rows(a["p"], a["y"]) - logloss_rows(b["p"], b["y"])  # > 0: candidate better
    per = pd.DataFrame({"m": a["match_id"].to_numpy(), "d": d}).groupby("m")["d"].agg(["sum", "size"])
    s, n = per["sum"].to_numpy(), per["size"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(n_resamples, len(s)))
    boot = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    level = alpha / budget
    return {"delta": float(d.mean()), "lower_bound": float(np.quantile(boot, level)), "one_sided_level": 1 - level,
            "n_rows": int(len(d)), "n_matches": int(len(s))}


def champion_config(path: Path, ref: str) -> dict:
    txt = subprocess.run(["git", "show", f"{ref}:{path.as_posix()}"], capture_output=True, text=True, check=True,
                         cwd=path.parent if path.is_absolute() else None).stdout
    return yaml.safe_load(txt)


def run(cfg_path: Path, champion_ref: str, frame: pd.DataFrame | None = None, champion_cfg: dict | None = None) -> dict:
    from cscoach.loops.sealed import LoopData
    from cscoach.loops.tasks import TASKS

    cand_cfg = yaml.safe_load(Path(cfg_path).read_text())
    champ_cfg = champion_cfg if champion_cfg is not None else champion_config(Path(cfg_path), champion_ref)
    loop = cand_cfg["loop"]
    work = Path(loop["work_dir"])
    if frame is None:
        frame = pd.read_parquet(loop["data"])
    train = LoopData(work, frame).training()
    task = TASKS[loop["task"]]
    champ, cand = task(train, champ_cfg["model"]), task(train, cand_cfg["model"])
    res = improvement_lower_bound(champ, cand, alpha=loop["alpha"], budget=loop["budget"],
                                  n_resamples=loop["n_resamples"], seed=loop["seed"])
    cand.to_parquet(work / "candidate_oof.parquet", index=False)
    ledger = work / "ledger.tsv"
    new = not ledger.exists()
    with open(ledger, "a", encoding="utf-8") as f:
        if new:
            f.write("time\ttask\tdelta_logloss\tlower_bound\tlevel\tn_matches\tseed\tcandidate_model\n")
        f.write(f"{dt.datetime.now().isoformat(timespec='seconds')}\t{loop['task']}\t{res['delta']:.6f}\t"
                f"{res['lower_bound']:.6f}\t{res['one_sided_level']:.5f}\t{res['n_matches']}\t{loop['seed']}\t"
                f"{yaml.safe_dump(cand_cfg['model'], default_flow_style=True).strip()}\n")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--champion-ref", default="HEAD~1")
    args = ap.parse_args(argv)
    print(f"{run(args.config, args.champion_ref)['lower_bound']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
