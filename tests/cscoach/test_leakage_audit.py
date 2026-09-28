"""Tests for the leakage audit (M2.4). Synthetic data: code behaviour only (A-33)."""
import numpy as np
import pandas as pd
import pytest

from cscoach.verify.leakage_audit import audit, auc


def test_auc_basic_properties():
    y = np.array([0, 0, 1, 1])
    assert auc(np.array([0.1, 0.2, 0.8, 0.9]), y) == pytest.approx(1.0)
    assert auc(np.array([0.9, 0.8, 0.2, 0.1]), y) == pytest.approx(0.0)
    assert auc(np.array([1, 1, 1, 1]), y) == pytest.approx(0.5)  # ties count half
    assert auc(np.array([0.1, 0.5, 0.5, 0.9]), y) == pytest.approx(0.875)


def frame(n_matches=60, rounds=20, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for m in range(n_matches):
        for r in range(rounds):
            y = rng.integers(0, 2)
            rows.append({"match_id": f"m{m}", "round": r, "y_ct_win": y,
                         "ct_equip_value": rng.normal(20000 + 3000 * y, 5000),  # weak honest signal
                         "noise": rng.normal()})
    return pd.DataFrame(rows)


def test_audit_passes_honest_features():
    res = audit(frame(), ["ct_equip_value", "noise"], label="y_ct_win", threshold=0.99, n_boot=100, seed=1)
    assert not res["flagged"]
    top = res["features"]["ct_equip_value"]
    assert 0.6 < top["auc"] < 0.8 and top["ci"][0] < top["auc"] < top["ci"][1]


def test_audit_flags_a_planted_leak():
    df = frame()
    df["leak"] = df["y_ct_win"] + np.random.default_rng(2).normal(0, 0.01, len(df))
    res = audit(df, ["ct_equip_value", "noise", "leak"], label="y_ct_win", threshold=0.99, n_boot=100, seed=1)
    assert res["flagged"] == ["leak"]


def test_orientation_free():
    df = frame()
    df["neg"] = -df["ct_equip_value"]
    res = audit(df, ["ct_equip_value", "neg"], label="y_ct_win", threshold=0.99, n_boot=50, seed=1)
    assert res["features"]["neg"]["auc"] == pytest.approx(res["features"]["ct_equip_value"]["auc"])
