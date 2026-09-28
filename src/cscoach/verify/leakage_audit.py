"""Leakage audit (M2.4): no single state feature separates the round winner almost perfectly at freeze end.

At the freeze-end snapshot only economy/equipment information exists, so an honest feature has a modest AUC; one
with AUC > ``threshold`` (0.99) signals leaked outcome information. AUCs are orientation-free (max(A, 1 − A)) with
cluster-bootstrap CIs over matches (docs/specs/04 §7, A-10). A supplementary profile reports the top AUC per
``second_in_round`` bin (late-round features are legitimately predictive; the profile shows where).

Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def auc(x: np.ndarray, y: np.ndarray) -> float:
    """Mann–Whitney AUC with ties counted half (rank formulation)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y).astype(bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    ranks = pd.Series(x).rank(method="average").to_numpy()
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _oriented(a: float) -> float:
    return max(a, 1 - a)


def audit(df: pd.DataFrame, features: list[str], *, label: str, threshold: float, n_boot: int, seed: int,
          cluster: str = "match_id") -> dict:
    rng = np.random.default_rng(seed)
    groups = df.groupby(cluster).indices
    keys = list(groups)
    out = {}
    boots = [np.concatenate([groups[keys[i]] for i in rng.integers(0, len(keys), len(keys))]) for _ in range(n_boot)]
    y = df[label].to_numpy()
    for f in features:
        x = df[f].astype(float).to_numpy()
        ok = ~np.isnan(x)
        a = _oriented(auc(x[ok], y[ok]))
        bs = []
        for idx in boots:
            xi, yi = x[idx], y[idx]
            m = ~np.isnan(xi)
            bs.append(_oriented(auc(xi[m], yi[m])))
        out[f] = {"auc": a, "ci": [float(np.nanquantile(bs, 0.025)), float(np.nanquantile(bs, 0.975))], "n": int(ok.sum())}
    flagged = [f for f, v in out.items() if v["auc"] > threshold]
    return {"features": out, "flagged": flagged, "threshold": threshold, "n_rows": int(len(df)),
            "n_clusters": int(len(keys))}


def load(root: Path, match_ids=None) -> pd.DataFrame:
    fdir = root / "derived" / "state_features"
    files = sorted(fdir.glob("*.parquet"))
    if match_ids is not None:
        files = [f for f in files if f.stem in set(match_ids)]
    parts = []
    for f in files:
        d = pd.read_parquet(f)
        r = pd.read_parquet(root / "derived" / "rounds" / f"{f.stem}.parquet", columns=["round", "winner_side"])
        parts.append(d.merge(r, on="round"))
    df = pd.concat(parts, ignore_index=True)
    df["y_ct_win"] = (df["winner_side"] == "CT").astype(int)  # label attached only here (modelling table)
    return df.drop(columns=["winner_side"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/leakage_audit.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    df = load(Path(cfg["root"]))
    skip = {"match_id", "round_uid", "round", "tick", "source", "map_name", "platform", "tier", "channel_set",
            "y_ct_win", "build_num"}
    feats = [c for c in df.columns if c not in skip and pd.api.types.is_numeric_dtype(df[c]) or c == "bomb_planted"]
    feats = [c for c in feats if c not in skip]
    fe = df[df["second_in_round"] == 0].copy()
    res = audit(fe, feats, label="y_ct_win", threshold=cfg["auc_threshold"], n_boot=cfg["n_boot"], seed=cfg["seed"])
    # supplementary profile: top feature AUC per time bin (point estimates)
    bins = cfg["profile_bins_s"]
    df["t_bin"] = pd.cut(df["second_in_round"], bins=bins, right=False)
    prof = []
    for b, g in df.groupby("t_bin", observed=True):
        aucs = {f: _oriented(auc(g[f].astype(float).fillna(g[f].astype(float).median()), g["y_ct_win"])) for f in feats}
        top = max(aucs, key=aucs.get)
        prof.append({"bin": str(b), "rows": int(len(g)), "top_feature": top, "top_auc": round(aucs[top], 4)})
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary = {**args.meta, "freeze_end": res, "profile": prof,
               "gate_pass": not res["flagged"]}
    (args.report_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    top = sorted(res["features"].items(), key=lambda kv: -kv[1]["auc"])[:8]
    print(json.dumps({"gate_pass": summary["gate_pass"], "n_rows": res["n_rows"], "n_clusters": res["n_clusters"],
                      "top": {k: [round(v["auc"], 4), [round(c, 4) for c in v["ci"]]] for k, v in top},
                      "profile": prof}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
