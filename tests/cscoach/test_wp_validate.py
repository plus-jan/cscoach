"""Tests for the WP validation (M3.4). Synthetic data: code behaviour only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.eval.metrics import ece
from cscoach.models.wp_validate import (SealedLookError, bss_ci, ece_ci, gate_verdicts, mce, record_look,
                                        select_eval_rows)


def clustered(n_matches=300, per=40, seed=0, shift=0.0):
    rng = np.random.default_rng(seed)
    m = np.repeat([f"m{i:03d}" for i in range(n_matches)], per)
    p = rng.uniform(0.05, 0.95, len(m))
    y = (rng.uniform(size=len(m)) < p).astype(int)
    return pd.DataFrame({"match_id": m, "p": np.clip(p + shift, 0.001, 0.999), "y": y})


def test_ece_ci_point_matches_ece_and_covers_it():
    d = clustered()
    point, (lo, hi) = ece_ci(d["p"], d["y"], d["match_id"], n_resamples=200, seed=1)
    assert point == pytest.approx(ece(d["p"], d["y"]))
    assert lo <= point <= hi and hi - lo > 0
    bad = clustered(shift=0.1)
    assert ece_ci(bad["p"], bad["y"], bad["match_id"], n_resamples=200, seed=1)[1][0] > 0.05


def test_mce_is_the_worst_bin():
    d = clustered()
    assert mce(d["p"], d["y"]) >= ece(d["p"], d["y"])


def test_bss_ci_sign():
    d = clustered()
    base = np.full(len(d), d["y"].mean())
    good = bss_ci(d["p"], base, d["y"], d["match_id"], n_resamples=200, seed=2)
    assert good["bss"] > 0 and good["ci"][0] > 0
    same = bss_ci(base, base, d["y"], d["match_id"], n_resamples=200, seed=2)
    assert same["bss"] == pytest.approx(0.0) and same["ci"][0] <= 0 <= same["ci"][1]


def test_select_eval_rows_only_sealed_evaluation_folds():
    body = {"split": {"a": "train", "b": "calibration", "c": "test", "d": "temporal"}}
    f = pd.DataFrame({"match_id": list("abcd")})
    assert select_eval_rows(f, body)["match_id"].tolist() == ["c", "d"]


def test_sealed_look_is_recorded_once_per_model(tmp_path):
    rec = record_look(tmp_path, model_sha="abc", commit="c1", folds=["test", "temporal"])
    assert rec["look"] == 1
    with pytest.raises(SealedLookError):
        record_look(tmp_path, model_sha="abc", commit="c2", folds=["test"])
    again = record_look(tmp_path, model_sha="abc", commit="c2", folds=["test"], new_experiment=True)
    assert again["look"] == 2 and again["total_looks_this_model"] == 2


def test_gate_verdicts_respect_min_rounds():
    strata = pd.DataFrame({"stratum": ["tier", "tier", "map_name"], "level": ["low", "semipro", "de_x"],
                           "model": "wp", "rounds": [900, 100, 800], "ece": [0.01, 0.2, 0.04]})
    g = gate_verdicts({"ece": 0.01, "bss_ci_low": 0.05}, strata, model="wp",
                      gates={"ece_max": 0.02, "ece_max_per_tier": 0.03, "ece_max_per_map": 0.035,
                             "bss_ci_low_min": 0.0, "min_rounds_per_stratum": 500})
    assert g["ece_overall"]["pass"] and g["bss_vs_baseline"]["pass"]
    assert g["ece_per_tier"]["pass"] and g["ece_per_tier"]["skipped_small"] == ["semipro"]
    assert not g["ece_per_map"]["pass"] and g["ece_per_map"]["failing"] == ["de_x"]
    assert not g["all_pass"]
