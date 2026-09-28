"""M3.1 baseline WP on CSDS: reference metrics from grouped out-of-fold predictions on the **training matches only**
(the calibration, test and temporal folds stay sealed for M3.3/M3.4; data path = ``cscoach.loops.sealed.LoopData``).

Models (docs/specs/03 WP):
- ``base_rate``: the CT round-win share of the fitting folds;
- ``map_only``: the CT round-win share per map (comparable to the pro "map-only" benchmark 0.692);
- ``baseline_wp``: logistic regression on ct/t alive, ct/t HP sum, bomb planted, time remaining, plus alive-diff ×
  planted and time × planted (standardised).
Metrics: log-loss and Brier with match-level cluster-bootstrap CIs, ECE (15 quantile bins), ESS of the residuals
clustered by round (docs/specs/04 §2/§7) — overall and per tier, platform, map, round phase and alive state.
Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression

from cscoach.eval.metrics import ece, logloss_rows
from cscoach.eval.uncertainty import ess

BASE = ["ct_alive", "t_alive", "ct_hp_sum", "t_hp_sum", "bomb_planted", "time_remaining_s"]


def design(df: pd.DataFrame) -> pd.DataFrame:
    x = df[BASE].astype("float32").copy()
    x["alive_diff_x_planted"] = (df["ct_alive"] - df["t_alive"]).astype("float32") * x["bomb_planted"]
    x["time_x_planted"] = x["time_remaining_s"] * x["bomb_planted"]
    return x


def oof(train: pd.DataFrame, model: str, C: float = 1.0) -> np.ndarray:
    p = np.empty(len(train), dtype="float64")
    for k in sorted(train["fold"].unique()):
        fit, pred = (train["fold"] != k).to_numpy(), (train["fold"] == k).to_numpy()
        yf = train.loc[fit, "y_ct_win"]
        if model == "base_rate":
            p[pred] = yf.mean()
        elif model == "map_only":
            rate = yf.groupby(train.loc[fit, "map_name"]).mean()
            p[pred] = train.loc[pred, "map_name"].map(rate).fillna(yf.mean()).to_numpy()
        elif model == "baseline_wp":
            xf, xp = design(train.loc[fit]), design(train.loc[pred])
            mu, sd = xf.mean(), xf.std().replace(0, 1)
            lr = LogisticRegression(C=C, max_iter=500).fit(((xf - mu) / sd).to_numpy(), yf.to_numpy())
            p[pred] = lr.predict_proba(((xp - mu) / sd).to_numpy())[:, 1]
        else:
            raise ValueError(model)
    return p


def cluster_ci(values: np.ndarray, groups: np.ndarray, *, n_resamples: int, seed: int):
    codes, _ = pd.factorize(groups)
    s = np.bincount(codes, weights=values)
    n = np.bincount(codes).astype(float)
    idx = np.random.default_rng(seed).integers(0, len(s), size=(n_resamples, len(s)))
    boot = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    return float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def metrics(df: pd.DataFrame, p: np.ndarray, *, n_resamples: int, seed: int, with_ess: bool = False) -> dict:
    y = df["y_ct_win"].to_numpy()
    ll = logloss_rows(p, y)
    br = (p - y) ** 2
    out = {"rows": int(len(df)), "matches": int(df["match_id"].nunique()), "rounds": int(df["round_uid"].nunique()),
           "logloss": float(ll.mean()), "logloss_ci": cluster_ci(ll, df["match_id"].to_numpy(), n_resamples=n_resamples, seed=seed),
           "brier": float(br.mean()), "brier_ci": cluster_ci(br, df["match_id"].to_numpy(), n_resamples=n_resamples, seed=seed),
           "ece": float(ece(p, y))}
    if with_ess:
        out["ess_rounds_residual"] = float(ess(y - p, df["round_uid"].to_numpy()))
    return out


def strata(df: pd.DataFrame) -> dict[str, pd.Series]:
    phase = np.where(df["bomb_planted"], "post_plant",
                     np.where(df["second_in_round"] < 20, "early", np.where(df["second_in_round"] < 60, "mid", "late")))
    alive = df["ct_alive"].astype(int).astype(str) + "v" + df["t_alive"].astype(int).astype(str)
    return {"tier": df["tier"].fillna("null"), "platform": df["platform"], "map_name": df["map_name"],
            "phase": pd.Series(phase, index=df.index), "alive_state": alive, "channel_set": df["channel_set"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/wp_baseline.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    from cscoach.loops.sealed import LoopData

    root = Path(cfg["root"])
    table = pd.read_parquet(root / "derived" / "wp_table_v1.parquet")
    train = LoopData(root / "splits" / cfg["split_name"], table).training().reset_index(drop=True)
    preds = {m: oof(train, m, C=cfg.get("C", 1.0)) for m in cfg["models"]}
    B, seed = cfg["n_resamples"], cfg["seed"]
    res = {"overall": {m: metrics(train, p, n_resamples=B, seed=seed, with_ess=(m == "baseline_wp")) for m, p in preds.items()}}
    # paired difference baseline_wp vs map_only (same resamples)
    d = logloss_rows(preds["map_only"], train["y_ct_win"]) - logloss_rows(preds["baseline_wp"], train["y_ct_win"])
    res["delta_logloss_map_only_minus_baseline"] = {"mean": float(d.mean()),
                                                    "ci": cluster_ci(d, train["match_id"].to_numpy(), n_resamples=B, seed=seed)}
    rows = []
    for name, s in strata(train).items():
        for level, idx in train.groupby(s.values).groups.items():
            sub = train.loc[idx]
            if sub["match_id"].nunique() < cfg["min_matches_per_stratum_report"]:
                continue
            for m in ("map_only", "baseline_wp"):
                r = metrics(sub, preds[m][idx], n_resamples=B, seed=seed)
                rows.append({"stratum": name, "level": level, "model": m, **{k: v for k, v in r.items()}})
    args.report_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.report_dir / "strata.csv", index=False)
    summary = {**args.meta, "split": cfg["split_name"], "training_matches": int(train["match_id"].nunique()),
               "training_rows": int(len(train)), **res,
               "benchmark_pro_csgo": {"xgboost": 0.5353, "map_only": 0.6917, "source": "xenopoulos_valuing_actions_csgo"}}
    (args.report_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in ("training_matches", "training_rows", "overall",
                                              "delta_logloss_map_only_minus_baseline")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
