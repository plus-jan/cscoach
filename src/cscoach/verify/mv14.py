"""MV.14: false-keep rate and power of the gated keep rule (A-42). Simulation with known truth (A-33 permits it:
it tests a method property, not a CS2 fact).

Truth: each round is a Brownian path B on [0, 1]; the round is won iff B_1 > 0, and a snapshot at time t has the true
win probability p_t = Φ(B_t / sqrt(1 − t)) — a martingale, so the truth is exactly calibrated and all snapshots of a
round share one outcome (clustered like CSDS: matches × rounds × snapshots).

Models: logit(p̂) = logit(p) + e, with e = row noise (σ_row) + a per-match offset (σ_match). No-effect variants have
the champion's error; the planted variant's σ_row is lowered so that its expected log-loss is ``target`` (0.002)
better. A loop compares ``budget`` variants with the champion on the same data and the same bootstrap resamples; a
variant is kept iff the lower bound of the one-sided cluster-bootstrap CI of Δlog-loss (clusters = matches) is > 0 at
level 1 − α/budget (corrected) — the uncorrected level 1 − α is recorded alongside. A kept variant becomes the
champion (docs/specs/07 §2).
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.special import expit, logit, ndtr

EPS = 1e-12


def simulate_truth(rng, *, n_matches: int, rounds: int, snaps: int) -> dict:
    n_rounds = n_matches * rounds
    t = np.arange(snaps) / snaps  # 0, 1/S, …: freeze end and later snapshots, never t = 1
    steps = rng.normal(0, np.sqrt(1 / snaps), size=(n_rounds, snaps))
    b = np.concatenate([np.zeros((n_rounds, 1)), np.cumsum(steps, axis=1)[:, :-1]], axis=1)  # B at the snapshot times
    b_final = b[:, -1] + rng.normal(0, np.sqrt(1 - t[-1]), size=n_rounds)
    p = ndtr(b / np.sqrt(1 - t))
    y = np.repeat((b_final > 0).astype(float), snaps)
    match = np.repeat(np.arange(n_matches), rounds * snaps)
    return {"p": np.clip(p.ravel(), 1e-6, 1 - 1e-6), "y": y, "match": match, "n_matches": n_matches}


def variant_losses(rng, truth: dict, *, sigma_row: float, sigma_match: float) -> np.ndarray:
    e = rng.normal(0, sigma_row, truth["p"].size) + rng.normal(0, sigma_match, truth["n_matches"])[truth["match"]]
    q = np.clip(expit(logit(truth["p"]) + e), EPS, 1 - EPS)
    y = truth["y"]
    return -(y * np.log(q) + (1 - y) * np.log(1 - q))


def calibrate_sigma(truth: dict, *, sigma_row: float, sigma_match: float, target: float, seed: int) -> float:
    """σ_row of a variant whose expected log-loss is ``target`` below a σ_row variant (bisection on a fixed draw)."""
    base = variant_losses(np.random.default_rng(seed), truth, sigma_row=sigma_row, sigma_match=sigma_match).mean()
    lo, hi = 0.0, sigma_row
    for _ in range(40):
        mid = (lo + hi) / 2
        gain = base - variant_losses(np.random.default_rng(seed), truth, sigma_row=mid, sigma_match=sigma_match).mean()
        lo, hi = (mid, hi) if gain > target else (lo, mid)
    return (lo + hi) / 2


def resample_index(n_matches: int, *, n_resamples: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n_matches, size=(n_resamples, n_matches))


def lower_bounds(sum_d: np.ndarray, n: np.ndarray, *, levels, n_resamples: int, seed: int,
                 idx: np.ndarray | None = None) -> np.ndarray:
    """sum_d: variants × matches (per-match sum of Δ log-loss), n: rows per match. Returns variants × levels lower
    bounds of the pooled mean Δ from one shared set of cluster resamples (``idx``, or drawn from ``seed``)."""
    if idx is None:
        idx = resample_index(sum_d.shape[1], n_resamples=n_resamples, seed=seed)
    denom = n[idx].sum(axis=1)
    out = np.empty((sum_d.shape[0], len(levels)))
    for v in range(sum_d.shape[0]):
        boot = sum_d[v][idx].sum(axis=1) / denom
        out[v] = np.quantile(boot, levels)
    return out


def simulate_loop(*, seed: int, n_matches: int, rounds: int, snaps: int, budget: int, planted: int | None,
                  target: float = 0.002, sigma_row: float = 0.5, sigma_match: float = 0.2, alpha: float = 0.05,
                  n_resamples: int = 2000, sigma_planted: float | None = None) -> dict:
    rng = np.random.default_rng(seed)
    truth = simulate_truth(rng, n_matches=n_matches, rounds=rounds, snaps=snaps)
    n = np.bincount(truth["match"], minlength=n_matches).astype(float)
    if planted is not None and sigma_planted is None:
        sigma_planted = calibrate_sigma(truth, sigma_row=sigma_row, sigma_match=sigma_match, target=target, seed=seed + 1)
    champ = {"corrected": variant_losses(rng, truth, sigma_row=sigma_row, sigma_match=sigma_match)}
    champ["uncorrected"] = champ["corrected"]
    boot_seed = seed + 7  # identical resamples for every iteration of the loop
    idx = resample_index(n_matches, n_resamples=n_resamples, seed=boot_seed)
    keeps = {"corrected": [], "uncorrected": []}
    for i in range(budget):
        s = sigma_planted if (planted is not None and i == planted) else sigma_row
        cand = variant_losses(rng, truth, sigma_row=s, sigma_match=sigma_match)
        for mode, level in (("corrected", alpha / budget), ("uncorrected", alpha)):
            d = champ[mode] - cand
            sum_d = np.bincount(truth["match"], weights=d, minlength=n_matches)[None, :]
            lb = lower_bounds(sum_d, n, levels=(level,), n_resamples=n_resamples, seed=boot_seed, idx=idx)[0, 0]
            keep = lb > 0
            keeps[mode].append(bool(keep))
            if keep:
                champ[mode] = cand
    res = {"seed": seed, "n_matches": n_matches, "planted": planted}
    for mode in keeps:
        k = np.array(keeps[mode])
        null = np.ones(budget, bool)
        if planted is not None:
            null[planted] = False
            res[f"planted_kept_{mode}"] = bool(k[planted])
        res[f"any_keep_{mode}"] = bool(k[null].any())
        res[f"null_keeps_{mode}"] = int(k[null].sum())
    return res


def _run(args):
    return simulate_loop(**args)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--loops", type=int, default=200)
    ap.add_argument("--sizes", type=int, nargs="+", default=[2000, 4000, 6900])
    ap.add_argument("--rounds", type=int, default=21)
    ap.add_argument("--snaps", type=int, default=6)
    ap.add_argument("--budget", type=int, default=15)
    ap.add_argument("--n-resamples", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260928)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args(argv)
    jobs = []
    for size in args.sizes:
        for scenario in ("null", "planted"):
            for i in range(args.loops):
                s = args.seed + 100_000 * args.sizes.index(size) + (50_000 if scenario == "planted" else 0) + i
                planted = None if scenario == "null" else int(np.random.default_rng(s).integers(0, args.budget))
                jobs.append({"seed": s, "n_matches": size, "rounds": args.rounds, "snaps": args.snaps,
                             "budget": args.budget, "planted": planted, "n_resamples": args.n_resamples})
    with ProcessPoolExecutor(args.workers) as pool:
        res = list(pool.map(_run, jobs, chunksize=2))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "loops.jsonl").write_text("\n".join(json.dumps(r) for r in res))
    summary = {"loops_per_cell": args.loops, "budget": args.budget, "alpha": 0.05, "n_resamples": args.n_resamples,
               "rounds": args.rounds, "snaps": args.snaps, "sigma_row": 0.5, "sigma_match": 0.2, "target": 0.002,
               "seed": args.seed, "cells": {}}
    for size in args.sizes:
        null = [r for r in res if r["n_matches"] == size and r["planted"] is None]
        pl = [r for r in res if r["n_matches"] == size and r["planted"] is not None]
        cell = {}
        for mode in ("corrected", "uncorrected"):
            fk = np.array([r[f"any_keep_{mode}"] for r in null])
            pw = np.array([r[f"planted_kept_{mode}"] for r in pl])
            se_fk, se_pw = np.sqrt(fk.mean() * (1 - fk.mean()) / len(fk)), np.sqrt(pw.mean() * (1 - pw.mean()) / len(pw))
            cell[mode] = {"false_keep_rate": round(float(fk.mean()), 4), "fkr_ci95": [round(float(fk.mean() - 1.96 * se_fk), 4), round(float(fk.mean() + 1.96 * se_fk), 4)],
                          "power": round(float(pw.mean()), 4), "power_ci95": [round(float(pw.mean() - 1.96 * se_pw), 4), round(float(pw.mean() + 1.96 * se_pw), 4)],
                          "false_keeps_in_planted_loops": round(float(np.mean([r[f"any_keep_{mode}"] for r in pl])), 4)}
        summary["cells"][str(size)] = cell
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary["cells"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
