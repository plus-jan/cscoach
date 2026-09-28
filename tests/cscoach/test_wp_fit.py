"""Tests for the final WP fit (M3.3): GBDT on training matches, calibrator on the calibration fold, never test or
temporal. Synthetic data: code behaviour only (A-33)."""
import json

import numpy as np
import pandas as pd
import pytest

from cscoach.loops.sealed import make_split
from cscoach.loops.tasks import synthetic_wp_frame
from cscoach.models.wp_fit import WPModel, fit, select_rows

GBDT = {"features": ["x1", "x2", "tier"], "categorical": ["tier"], "label": "y", "stratum": "tier",
        "monotone": {"x1": 1}, "num_boost_round": 60, "early_stopping_rounds": 10, "es_fraction": 0.15, "seed": 7,
        "train_row_fraction": 1.0, "params": {"learning_rate": 0.1, "num_leaves": 7, "min_child_samples": 20,
                                               "num_threads": 2}}
CAL = {"method": "auto", "by": "tier", "isotonic_min_rows": 500, "min_rows_per_group": 200}


@pytest.fixture
def setup(tmp_path):
    data = synthetic_wp_frame(n_matches=300, rounds=10, snaps=3, seed=2)
    groups = data.drop_duplicates("match_id")[["match_id", "tier"]].rename(columns={"tier": "stratum"})
    body = make_split(groups, tmp_path / "split", fractions={"train": 0.7, "calibration": 0.1, "test": 0.2}, k=3,
                      seed=4)
    return data, body, tmp_path


def test_select_rows_excludes_sealed_evaluation_folds(setup):
    data, body, _ = setup
    rows = select_rows(data, body, ("train", "calibration"))
    assert set(rows["match_id"].map(body["split"])) == {"train", "calibration"}
    with pytest.raises(ValueError):
        select_rows(data, body, ("train", "test"))  # the fit may never ask for test/temporal


def test_fit_writes_a_loadable_model_and_access_record(setup):
    data, body, tmp = setup
    out = tmp / "model"
    card = fit(select_rows(data, body, ("train", "calibration")), body, {"gbdt": GBDT, "calibration": CAL}, out,
               meta={"commit": "abc"})
    assert (out / "booster.txt").exists() and (out / "calibrator.json").exists()
    access = json.loads((out / "access.json").read_text())
    assert set(access["splits_read"]) == {"train", "calibration"} and access["split_sha256"] == body["sha256"]
    assert card["train"]["matches"] > card["calibration"]["matches"] > 0 and card["best_iteration"] > 0
    assert card["commit"] == "abc"
    m = WPModel.load(out)
    test = data[data["match_id"].map(body["split"]) == "test"]
    p = m.predict(test)
    assert len(p) == len(test) and np.all((p > 0) & (p < 1))
    raw = m.predict(test, calibrated=False)
    assert not np.allclose(p, raw)  # the calibrator is applied


def test_calibrator_is_fitted_on_calibration_rows_only(setup):
    data, body, tmp = setup
    rows = select_rows(data, body, ("train", "calibration"))
    a = fit(rows, body, {"gbdt": GBDT, "calibration": CAL}, tmp / "a")
    flipped = rows.copy()
    cal = flipped["match_id"].map(body["split"]) == "calibration"
    flipped.loc[cal, "y"] = 1 - flipped.loc[cal, "y"]
    b = fit(flipped, body, {"gbdt": GBDT, "calibration": CAL}, tmp / "b")
    assert a["best_iteration"] == b["best_iteration"]          # GBDT does not see calibration labels
    x = pd.DataFrame({"x1": [0.0], "x2": [0.0], "tier": ["low"]})
    assert WPModel.load(tmp / "a").predict(x) != pytest.approx(WPModel.load(tmp / "b").predict(x))
