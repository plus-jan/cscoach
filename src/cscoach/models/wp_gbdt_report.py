"""M3.2 loop report: the loop champion's out-of-fold metrics next to the M3.1 logistic baseline on identical rows.

Training matches only (sealed folds stay unread; docs/specs/07 §3). The champion's out-of-fold predictions come from
the Verify cache (``cscoach.loops.gated_verify.cached_oof``), the baseline is refitted on the same folds. Metrics as
in M3.1 (``cscoach.models.wp_baseline``): log-loss and Brier with match-cluster bootstrap CIs, ECE, residual ESS, the
paired Δlog-loss, per stratum. The ECE gates (docs/specs/06, A-06) are reported on these out-of-fold predictions as
information; the gate verdict that counts is the single sealed-test evaluation (M3.4). Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cscoach.eval.metrics import logloss_rows
from cscoach.loops.gated_verify import cached_oof, champion_config
from cscoach.loops.sealed import LoopData
from cscoach.loops.tasks import TASKS
from cscoach.models.wp_baseline import cluster_ci, metrics, oof, strata

STRATA_COLUMNS = ["round_uid", "second_in_round", "bomb_planted", "ct_alive", "t_alive", "ct_hp_sum", "t_hp_sum",
                  "time_remaining_s", "tier", "platform", "map_name", "channel_set"]


def fold_order(train: pd.DataFrame, label: str = "y") -> pd.DataFrame:
    """The training frame in the row order of a loop task's out-of-fold predictions (fold by fold)."""
    parts = [train[train["fold"] == k] for k in sorted(train["fold"].unique())]
    out = pd.concat(parts).reset_index(drop=True)
    out["y"] = out[label].to_numpy()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/wp_gbdt.yaml"))
    ap.add_argument("--ref", default="HEAD", help="git ref of the champion config")
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    ap.add_argument("--n-resamples", type=int, default=500)  # A-10
    args = ap.parse_args(argv)
    cfg = champion_config(args.config, args.ref)
    loop, model = cfg["loop"], cfg["model"]
    cols = list(dict.fromkeys([*loop["columns"], *STRATA_COLUMNS]))
    data = LoopData(Path(loop["work_dir"]), pd.read_parquet(loop["data"], columns=cols))
    train = data.training()
    champ = cached_oof(TASKS[loop["task"]], train, loop, model, data.body["sha256"])
    df = fold_order(train, model["label"]).assign(y_ct_win=lambda d: d["y"])
    if not (df["match_id"].astype(str).equals(champ["match_id"].astype(str)) and df["y"].equals(champ["y"])):
        raise ValueError("cached out-of-fold predictions do not align with the training frame")
    preds = {"gbdt_wp": champ["p"].to_numpy(), "baseline_wp": oof(df, "baseline_wp")}
    B, seed = args.n_resamples, loop["seed"]
    res = {m: metrics(df, p, n_resamples=B, seed=seed, with_ess=True) for m, p in preds.items()}
    d = logloss_rows(preds["baseline_wp"], df["y"]) - logloss_rows(preds["gbdt_wp"], df["y"])
    res["delta_logloss_baseline_minus_gbdt"] = {"mean": float(d.mean()),
                                                "ci": cluster_ci(d, df["match_id"].to_numpy(), n_resamples=B, seed=seed)}
    rows = []
    for name, s in strata(df).items():
        for level, idx in df.groupby(s.values).groups.items():
            sub = df.loc[idx]
            if sub["match_id"].nunique() < 30:
                continue
            for m, p in preds.items():
                rows.append({"stratum": name, "level": level, "model": m,
                             **metrics(sub, p[idx], n_resamples=B, seed=seed)})
    st = pd.DataFrame(rows)
    g = st[st["model"] == "gbdt_wp"]
    gates = {"ece_overall": {"value": res["gbdt_wp"]["ece"], "max": 0.02},
             "ece_per_tier_max": {"value": float(g.loc[g["stratum"] == "tier", "ece"].max()), "max": 0.03},
             "ece_per_map_max": {"value": float(g.loc[g["stratum"] == "map_name", "ece"].max()), "max": 0.035}}
    for v in gates.values():
        v["pass"] = v["value"] <= v["max"]
    args.report_dir.mkdir(parents=True, exist_ok=True)
    st.to_csv(args.report_dir / "strata.csv", index=False)
    summary = {**args.meta, "champion_ref": args.ref, "model": model, "split_sha256": data.body["sha256"],
               "training_matches": int(df["match_id"].nunique()), "training_rows": int(len(df)), **res,
               "oof_ece_gates_information_only": gates,
               "benchmark_pro_csgo": {"xgboost": 0.5353, "map_only": 0.6917, "source": "xenopoulos_valuing_actions_csgo"}}
    (args.report_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in ("training_matches", "gbdt_wp", "baseline_wp",
                                              "delta_logloss_baseline_minus_gbdt", "oof_ece_gates_information_only")},
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
