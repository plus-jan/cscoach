"""Tests for the gated loop harness (M2.5). Synthetic data: code behaviour only (A-33)."""
import json
import subprocess

import numpy as np
import pandas as pd
import pytest
import yaml

from cscoach.loops.gated_verify import improvement_lower_bound
from cscoach.loops.guard import run_checks
from cscoach.loops.sealed import LoopData, SealedFoldError, load_split, make_split
from cscoach.loops.tasks import oof_predict, synthetic_wp_frame


@pytest.fixture(scope="module")
def data():
    return synthetic_wp_frame(n_matches=240, rounds=12, snaps=4, seed=1)


@pytest.fixture
def work(tmp_path, data):
    groups = data.drop_duplicates("match_id")[["match_id", "tier"]].rename(columns={"tier": "stratum"})
    make_split(groups, tmp_path, fractions={"train": 0.7, "calibration": 0.1, "test": 0.2}, k=5, seed=11)
    return tmp_path


def test_training_only_and_folds(work, data):
    ld = LoopData(work, data)
    tr = ld.training()
    split = load_split(work)["split"]
    assert set(tr["match_id"].map(split)) == {"train"}
    assert tr["fold"].notna().all() and set(tr["fold"]) == {0, 1, 2, 3, 4}


def test_sealed_fold_read_fails_and_is_logged(work, data):
    ld = LoopData(work, data)
    sealed = [m for m, s in load_split(work)["split"].items() if s == "test"][:2]
    with pytest.raises(SealedFoldError):
        ld.read(sealed)
    res = run_checks(work, oof=None, gates=None)
    assert not res["ok"] and "sealed" in " ".join(res["failures"])


def test_modified_split_fails_guard(work):
    body = json.loads((work / "split.json").read_text())
    m = next(k for k, v in body["split"].items() if v == "test")
    body["split"][m] = "train"  # someone moves a test match into training
    (work / "split.json").write_text(json.dumps(body))
    assert not run_checks(work, oof=None, gates=None)["ok"]


def test_lower_bound_positive_for_real_improvement_and_not_for_noise(work, data):
    tr = LoopData(work, data).training()
    base = {"features": ["x1"], "label": "y"}
    champ = oof_predict(tr, base)
    better = oof_predict(tr, {**base, "features": ["x1", "x2"]})
    noise = oof_predict(tr, {**base, "features": ["x1", "noise1"]})
    kw = dict(alpha=0.05, budget=15, n_resamples=2000, seed=5)
    assert improvement_lower_bound(champ, better, **kw)["lower_bound"] > 0
    assert improvement_lower_bound(champ, noise, **kw)["lower_bound"] <= 0
    assert improvement_lower_bound(champ, champ, **kw)["lower_bound"] <= 0


def test_guard_calibration_gate(tmp_path):
    # ECE is biased upward by estimation noise (≈ 0.8·0.5/√rows-per-bin); a calibrated model needs thousands of
    # independent rows per stratum to stay under 0.03, so this test uses ~8k rows per stratum and no match effect.
    data = synthetic_wp_frame(n_matches=3000, rounds=12, snaps=1, seed=2, match_sd=0.0)
    groups = data.drop_duplicates("match_id")[["match_id", "tier"]].rename(columns={"tier": "stratum"})
    make_split(groups, tmp_path, fractions={"train": 0.7, "calibration": 0.1, "test": 0.2}, k=5, seed=11)
    work = tmp_path
    tr = LoopData(work, data).training()
    gates = {"ece_max": 0.02, "ece_max_per_stratum": 0.03, "min_rows_per_stratum": 500, "stratum": "tier"}
    good = oof_predict(tr, {"features": ["x1", "x2"], "label": "y"})
    bad = oof_predict(tr, {"features": ["x1", "x2"], "label": "y", "miscalibrate": 0.12})
    assert run_checks(work, oof=good, gates=gates)["ok"]
    res = run_checks(work, oof=bad, gates=gates)
    assert not res["ok"] and any("ECE" in f for f in res["failures"])


def test_verify_caches_oof_per_model_config(work, data, monkeypatch):
    # a kept candidate is the next champion: its out-of-fold predictions are reused, not refitted
    from cscoach.loops import gated_verify, tasks

    calls = []

    def counting(train, cfg):
        calls.append(tuple(cfg["features"]))
        return oof_predict(train, cfg)

    monkeypatch.setitem(tasks.TASKS, "count", counting)
    loop = {"task": "count", "data": str(work / "none.parquet"), "work_dir": str(work), "alpha": 0.05, "budget": 15,
            "n_resamples": 200, "seed": 5}
    a = {"loop": loop, "model": {"features": ["x1"], "label": "y"}}
    b = {"loop": loop, "model": {"features": ["x1", "x2"], "label": "y"}}
    c = {"loop": loop, "model": {"features": ["x1", "x2", "noise1"], "label": "y"}}
    for cand, champ in ((b, a), (c, b)):
        path = work / "cfg.yaml"
        path.write_text(yaml.safe_dump(cand))
        gated_verify.run(path, "HEAD~1", frame=data, champion_cfg=champ)
    assert calls == [("x1",), ("x1", "x2"), ("x1", "x2", "noise1")]
