"""M3.2 GBDT WP: LightGBM with monotone constraints (docs/specs/03 WP, A-27), as a loop task (docs/specs/07 §2).

``gbdt_oof`` turns (training frame with ``fold``, ``model`` config) into pooled out-of-fold predictions in a fixed row
order (fold by fold, training-frame order within a fold), so the gated Verify can compare champion and candidate row
by row. Per fold, early stopping uses a grouped slice of the fitting matches (``es_fraction``, chosen by a seeded
hash of the match id, so it is independent of row order); ``train_row_fraction`` optionally thins the snapshots of the
remaining matches (snapshots of a round are strongly correlated, docs/specs/04 §2). Categorical features get one
category set per call, shared by all folds. Every config value is a loop variant; start values: A-29.
Data provided by PureSkill.gg.
"""
from __future__ import annotations

import hashlib

import lightgbm as lgb
import numpy as np
import pandas as pd


def es_matches(match_ids, *, fraction: float, seed: int) -> set[str]:
    out = set()
    for m in pd.unique(pd.Series(match_ids).astype(str)):
        h = int.from_bytes(hashlib.sha256(f"{seed}:{m}".encode()).digest()[:8], "big") / 2**64
        if h < fraction:
            out.add(m)
    return out


def categories(df: pd.DataFrame, cfg: dict) -> dict:
    return {c: sorted(df[c].astype("string").fillna("null").unique()) for c in cfg.get("categorical") or []}


def prepare(df: pd.DataFrame, cfg: dict, cats: dict | None):
    cat_cols = list(cfg.get("categorical") or [])
    if cats is None:
        cats = categories(df, cfg)
    x = pd.DataFrame(index=df.index)
    for c in cfg["features"]:
        if c in cat_cols:
            x[c] = pd.Categorical(df[c].astype("string").fillna("null"), categories=cats[c])
        else:
            x[c] = df[c].astype("float32")
    return x, cats


def _params(cfg: dict) -> dict:
    unknown = set(cfg.get("monotone") or {}) - set(cfg["features"])
    if unknown:
        raise ValueError(f"monotone constraints on features not in the model: {sorted(unknown)}")
    mono = [int((cfg.get("monotone") or {}).get(c, 0)) for c in cfg["features"]]
    return {"objective": "binary", "metric": "binary_logloss", "verbosity": -1, "seed": cfg["seed"],
            "deterministic": True, "force_row_wise": True, "monotone_constraints": mono, **cfg.get("params", {})}


def fit_one(fit: pd.DataFrame, cfg: dict, cats: dict | None = None):
    x, cats = prepare(fit, cfg, cats)
    y = fit[cfg["label"]].to_numpy()
    es = fit["match_id"].astype(str).isin(es_matches(fit["match_id"], fraction=cfg["es_fraction"], seed=cfg["seed"]))
    es = es.to_numpy()
    tr = ~es
    frac = cfg.get("train_row_fraction", 1.0)
    if frac < 1.0:
        tr &= np.random.default_rng(cfg["seed"]).uniform(size=len(fit)) < frac
    cat_cols = list(cfg.get("categorical") or [])
    dtr = lgb.Dataset(x[tr], y[tr], categorical_feature=cat_cols or "auto", free_raw_data=True)
    des = lgb.Dataset(x[es], y[es], reference=dtr, categorical_feature=cat_cols or "auto")
    booster = lgb.train(_params(cfg), dtr, num_boost_round=cfg["num_boost_round"], valid_sets=[des],
                        callbacks=[lgb.early_stopping(cfg["early_stopping_rounds"], verbose=False)])
    return booster, cats


def gbdt_oof(train: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    _params(cfg)  # validate before any fitting
    cats = categories(train, cfg)
    stratum, label = cfg.get("stratum", "tier"), cfg["label"]
    out, iters = [], []
    for k in sorted(train["fold"].unique()):
        fit, pred = train[train["fold"] != k], train[train["fold"] == k]
        booster, _ = fit_one(fit, cfg, cats)
        iters.append(booster.best_iteration)
        p = booster.predict(prepare(pred, cfg, cats)[0], num_iteration=booster.best_iteration)
        out.append(pred[["match_id", stratum, label]].assign(p=p))
    res = pd.concat(out).rename(columns={label: "y"})
    res.attrs["best_iterations"] = iters
    return res
