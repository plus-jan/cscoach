"""Loop tasks: how to get out-of-fold predictions for a config (docs/specs/07 §2).

A task turns (training frame with ``fold``, config) into pooled out-of-fold predictions. Only config-driven variants
are compared (the champion is the config at an earlier git ref), so model code changes must be exposed as config
switches. ``synthetic_wp`` is the synthetic task used to test the harness (A-33: code correctness only).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from cscoach.models.wp_gbdt import calibrated_oof, gbdt_oof


def synthetic_wp_frame(n_matches: int = 400, rounds: int = 20, snaps: int = 8, seed: int = 0,
                       match_sd: float = 0.5) -> pd.DataFrame:
    """Round outcomes driven by x1 (strong) and x2 (weak) plus a match effect; noise1–3 carry no signal."""
    rng = np.random.default_rng(seed)
    rows = []
    tiers = np.array(["low", "mid", "high"])
    for m in range(n_matches):
        u = rng.normal(0, match_sd)
        tier = tiers[m % 3]
        for r in range(rounds):
            x1, x2 = rng.normal(), rng.normal()
            logit = 1.2 * x1 + 0.5 * x2 + u
            y = int(rng.uniform() < 1 / (1 + np.exp(-logit)))
            for s in range(snaps):  # snapshots share the round label (clustered like real data)
                rows.append({"match_id": f"m{m:04d}", "round": r, "tier": tier, "x1": x1 + rng.normal(0, 0.3),
                             "x2": x2 + rng.normal(0, 0.3), "noise1": rng.normal(), "noise2": rng.normal(),
                             "noise3": rng.normal(), "y": y})
    return pd.DataFrame(rows)


def oof_predict(train: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    feats, label = cfg["features"], cfg["label"]
    out = []
    for k in sorted(train["fold"].unique()):
        fit, pred = train[train["fold"] != k], train[train["fold"] == k]
        model = LogisticRegression(C=cfg.get("C", 1.0), max_iter=1000).fit(fit[feats], fit[label])
        p = model.predict_proba(pred[feats])[:, 1]
        if cfg.get("miscalibrate"):  # test switch: a variant that breaks calibration
            p = np.clip(p + cfg["miscalibrate"], 1e-6, 1 - 1e-6)
        out.append(pred[["match_id", cfg.get("stratum", "tier"), label]].assign(p=p))
    return pd.concat(out).rename(columns={label: "y"})


TASKS = {"synthetic_wp": oof_predict, "gbdt_wp": gbdt_oof, "gbdt_wp_calibrated": calibrated_oof}
