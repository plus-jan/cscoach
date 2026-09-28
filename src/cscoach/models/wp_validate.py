"""M3.4 WP validation: the single sealed evaluation of ``models/wp_v1`` on the test fold and the temporal holdout.

docs/specs/04 §2–3, gates docs/specs/06 (A-06, A-07). Metrics per fold, overall and per tier, platform, map, round
phase, alive state and channel set: log-loss, Brier (match-cluster bootstrap CIs, no refit), ECE with a cluster CI
(15 quantile bins fixed on the evaluated rows), MCE, AUC, residual ESS; Brier skill score and Δlog-loss vs the M3.1
logistic baseline (refitted once on all training matches) with paired cluster CIs; map-only reference. Reliability
curves per tier and per tier × man-advantage sign (A-01). The look is recorded in ``<work_dir>/sealed_looks.json``
**before** any metric is computed; a second look at the same model is refused unless it is declared a new experiment
(docs/specs/07 §3). Only test and temporal matches are read for evaluation (training matches only for the baseline).
Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from cscoach.eval.metrics import logloss_rows, reliability
from cscoach.models.wp_baseline import cluster_ci, design, metrics, strata

EVAL_SPLITS = ("test", "temporal")


class SealedLookError(RuntimeError):
    pass


def _bins(p, n_bins):
    edges = np.unique(np.quantile(p, np.linspace(0, 1, n_bins + 1)))
    edges[0], edges[-1] = 0.0, 1.0
    if len(edges) < 2:
        edges = np.array([0.0, 1.0])
    return np.clip(np.searchsorted(edges, p, side="right") - 1, 0, len(edges) - 2), len(edges) - 1


def ece_ci(p, y, groups, *, n_bins: int = 15, n_resamples: int = 500, seed: int = 0, alpha: float = 0.05):
    """ECE (as ``cscoach.eval.metrics.ece``) and its match-cluster bootstrap CI with the bin edges held fixed."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    b, nb = _bins(p, n_bins)
    codes, uniq = pd.factorize(np.asarray(groups))
    g = len(uniq)
    cell = codes * nb + b
    sp = np.bincount(cell, weights=p, minlength=g * nb).reshape(g, nb)
    sy = np.bincount(cell, weights=y, minlength=g * nb).reshape(g, nb)
    n = np.bincount(codes, minlength=g).astype(float)
    point = float(np.abs(sp.sum(0) - sy.sum(0)).sum() / n.sum())
    rng = np.random.default_rng(seed)
    w = np.stack([np.bincount(rng.integers(0, g, g), minlength=g) for _ in range(n_resamples)]).astype(float)
    boot = np.abs(w @ sp - w @ sy).sum(1) / (w @ n)
    return point, (float(np.quantile(boot, alpha / 2)), float(np.quantile(boot, 1 - alpha / 2)))


def mce(p, y, n_bins: int = 15) -> float:
    rel = reliability(p, y, n_bins)
    return float((rel["mean_y"] - rel["mean_p"]).abs().max())


def bss_ci(p, p_base, y, groups, *, n_resamples: int = 500, seed: int = 0, alpha: float = 0.05) -> dict:
    y = np.asarray(y, float)
    bm, bb = (np.asarray(p, float) - y) ** 2, (np.asarray(p_base, float) - y) ** 2
    codes, uniq = pd.factorize(np.asarray(groups))
    sm, sb = np.bincount(codes, weights=bm), np.bincount(codes, weights=bb)
    idx = np.random.default_rng(seed).integers(0, len(uniq), size=(n_resamples, len(uniq)))
    boot = 1 - sm[idx].sum(1) / sb[idx].sum(1)
    return {"bss": float(1 - sm.sum() / sb.sum()),
            "ci": (float(np.quantile(boot, alpha / 2)), float(np.quantile(boot, 1 - alpha / 2)))}


def select_eval_rows(frame: pd.DataFrame, body: dict) -> pd.DataFrame:
    return frame[frame["match_id"].astype(str).map(body["split"]).isin(EVAL_SPLITS)]


def record_look(work_dir: Path, *, model_sha: str, commit: str, folds, new_experiment: bool = False) -> dict:
    path = Path(work_dir) / "sealed_looks.json"
    looks = json.loads(path.read_text()) if path.exists() else []
    same = [x for x in looks if x["model_sha"] == model_sha]
    if same and not new_experiment:
        raise SealedLookError(f"model {model_sha} was already evaluated on the sealed folds ({len(same)} look(s)); "
                              "a further look must be declared a new experiment (docs/specs/07 §3)")
    rec = {"look": len(looks) + 1, "total_looks_this_model": len(same) + 1, "model_sha": model_sha, "commit": commit,
           "folds": list(folds), "time": dt.datetime.now().isoformat(timespec="seconds"),
           "new_experiment": bool(new_experiment)}
    path.write_text(json.dumps([*looks, rec], indent=2))
    return rec


def gate_verdicts(overall: dict, st: pd.DataFrame, *, model: str, gates: dict) -> dict:
    out = {"ece_overall": {"value": overall["ece"], "max": gates["ece_max"], "pass": overall["ece"] <= gates["ece_max"]},
           "bss_vs_baseline": {"ci_low": overall["bss_ci_low"], "min": gates["bss_ci_low_min"],
                               "pass": overall["bss_ci_low"] > gates["bss_ci_low_min"]}}
    for key, stratum, lim in (("ece_per_tier", "tier", gates["ece_max_per_tier"]),
                              ("ece_per_map", "map_name", gates["ece_max_per_map"])):
        s = st[(st["stratum"] == stratum) & (st["model"] == model)]
        big = s[s["rounds"] >= gates["min_rounds_per_stratum"]]
        failing = big.loc[big["ece"] > lim, "level"].astype(str).tolist()
        out[key] = {"max": lim, "worst": float(big["ece"].max()) if len(big) else None, "failing": failing,
                    "skipped_small": s.loc[s["rounds"] < gates["min_rounds_per_stratum"], "level"].astype(str).tolist(),
                    "pass": not failing}
    out["all_pass"] = all(v["pass"] for v in out.values() if isinstance(v, dict))
    return out


def fit_baseline(train: pd.DataFrame, C: float):
    x = design(train)
    mu, sd = x.mean(), x.std().replace(0, 1)
    lr = LogisticRegression(C=C, max_iter=500).fit(((x - mu) / sd).to_numpy(), train["y_ct_win"].to_numpy())
    rate = train.groupby("map_name")["y_ct_win"].mean()
    base = float(train["y_ct_win"].mean())
    return (lambda df: lr.predict_proba(((design(df) - mu) / sd).to_numpy())[:, 1],
            lambda df: df["map_name"].map(rate).fillna(base).to_numpy())


def evaluate(df: pd.DataFrame, preds: dict, *, B: int, seed: int, min_matches: int = 30):
    y, g = df["y_ct_win"].to_numpy(), df["match_id"].to_numpy()
    res = {}
    for m, p in preds.items():
        r = metrics(df, p, n_resamples=B, seed=seed, with_ess=True)
        r["ece"], r["ece_ci"] = ece_ci(p, y, g, n_resamples=B, seed=seed)
        r["mce"], r["auc"] = mce(p, y), float(roc_auc_score(y, p))
        res[m] = r
    d = logloss_rows(preds["baseline_wp"], y) - logloss_rows(preds["wp_v1"], y)
    res["delta_logloss_baseline_minus_wp_v1"] = {"mean": float(d.mean()), "ci": cluster_ci(d, g, n_resamples=B, seed=seed)}
    bss = bss_ci(preds["wp_v1"], preds["baseline_wp"], y, g, n_resamples=B, seed=seed)
    res["bss_vs_baseline"] = bss
    rows = []
    for name, s in strata(df).items():
        for level, idx in df.groupby(s.values).groups.items():
            sub = df.loc[idx]
            if sub["match_id"].nunique() < min_matches:
                continue
            for m in ("wp_v1", "baseline_wp"):
                p = preds[m][df.index.get_indexer(idx)]
                r = metrics(sub, p, n_resamples=B, seed=seed)
                r["ece"], r["ece_ci"] = ece_ci(p, sub["y_ct_win"], sub["match_id"], n_resamples=B, seed=seed)
                r["mce"] = mce(p, sub["y_ct_win"])
                rows.append({"stratum": name, "level": level, "model": m, **r})
    return res, pd.DataFrame(rows)


def curves(df: pd.DataFrame, p: np.ndarray) -> pd.DataFrame:
    out = []
    sign = np.sign(df["ct_alive"].to_numpy() - df["t_alive"].to_numpy())
    tier = df["tier"].astype("string").fillna("null").to_numpy()
    for t in pd.unique(tier):
        for s_name, mask in (("all", np.ones(len(df), bool)), ("ct_ahead", sign > 0), ("even", sign == 0),
                             ("t_ahead", sign < 0)):
            idx = (tier == t) & mask
            if idx.sum() < 1000:
                continue
            rel = reliability(p[idx], df["y_ct_win"].to_numpy()[idx])
            out.append(rel.assign(tier=t, man_advantage=s_name))
    return pd.concat(out, ignore_index=True)


def main(argv=None) -> int:
    from cscoach.models.wp_fit import WPModel

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/wp_validate.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    ap.add_argument("--new-experiment", action="store_true", help="declare a further sealed look (counted)")
    ap.add_argument("--dry-run", action="store_true",
                    help="code smoke test on 300 training matches as stand-in folds; no sealed read, no look recorded")
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    work, model_dir = Path(cfg["work_dir"]), Path(cfg["model_dir"])
    card = json.loads((model_dir / "card.json").read_text())
    body = json.loads((work / "split.json").read_text())
    if body["sha256"] != card["split_sha256"]:
        raise ValueError("split changed since the model was fitted")
    cols = cfg["columns"]
    by_split = pd.Series(body["split"])
    if args.dry_run:  # stand-in folds from training matches; in-sample for the model, so the numbers mean nothing
        dry = sorted(by_split.index[by_split == "train"])[:300]
        by_split = pd.Series({m: EVAL_SPLITS[i % 2] for i, m in enumerate(dry)})
        look = {"dry_run": True}
        ev = pd.read_parquet(cfg["data"], columns=cols, filters=[("match_id", "in", dry)])
    else:
        look = record_look(work, model_sha=card["booster_sha256_12"], commit=args.meta.get("commit", "?"),
                           folds=EVAL_SPLITS, new_experiment=args.new_experiment)
        ev_ids = sorted(by_split.index[by_split.isin(EVAL_SPLITS)])
        ev = select_eval_rows(pd.read_parquet(cfg["data"], columns=cols, filters=[("match_id", "in", ev_ids)]), body)
    tr_ids = sorted(m for m, s_ in body["split"].items() if s_ == "train")
    tr = pd.read_parquet(cfg["data"], columns=["match_id", "y_ct_win", "map_name", "ct_alive", "t_alive", "ct_hp_sum",
                                               "t_hp_sum", "bomb_planted", "time_remaining_s"],
                         filters=[("match_id", "in", tr_ids)])
    base_wp, map_only = fit_baseline(tr, cfg["baseline_C"])
    del tr
    model = WPModel.load(model_dir)
    B, seed = cfg["n_resamples"], cfg["seed"]
    summary = {**args.meta, "look": look, "model_card": {k: card[k] for k in ("commit", "booster_sha256_12",
                                                                             "best_iteration", "calibrators")},
               "gates": cfg["gates"], "folds": {}}
    args.report_dir.mkdir(parents=True, exist_ok=True)
    for fold in EVAL_SPLITS:
        df = ev[ev["match_id"].map(by_split) == fold].reset_index(drop=True)
        preds = {"wp_v1": model.predict(df), "wp_v1_uncalibrated": model.predict(df, calibrated=False),
                 "baseline_wp": base_wp(df), "map_only": map_only(df)}
        res, st = evaluate(df, preds, B=B, seed=seed)
        st.to_csv(args.report_dir / f"strata_{fold}.csv", index=False)
        curves(df, preds["wp_v1"]).to_csv(args.report_dir / f"reliability_{fold}.csv", index=False)
        verdict = gate_verdicts({"ece": res["wp_v1"]["ece"], "bss_ci_low": res["bss_vs_baseline"]["ci"][0]}, st,
                                model="wp_v1", gates=cfg["gates"])
        summary["folds"][fold] = {"matches": int(df["match_id"].nunique()), "rounds": int(df["round_uid"].nunique()),
                                  "rows": int(len(df)), "build_num": [int(df["build_num"].min()), int(df["build_num"].max())],
                                  **res, "gate_verdicts": verdict}
    summary["benchmark_pro_csgo"] = {"xgboost": 0.5353, "map_only": 0.6917, "source": "xenopoulos_valuing_actions_csgo"}
    (args.report_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    for fold, r in summary["folds"].items():
        print(fold, r["matches"], "log-loss", round(r["wp_v1"]["logloss"], 4), r["wp_v1"]["logloss_ci"],
              "ECE", round(r["wp_v1"]["ece"], 4), "BSS", r["bss_vs_baseline"], "gates all pass:", r["gate_verdicts"]["all_pass"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
