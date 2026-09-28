import numpy as np
import pandas as pd
import pytest

from cscoach.loops.tasks import TASKS, synthetic_wp_frame
from cscoach.models.wp_gbdt import es_matches, gbdt_oof, prepare


def _train(n_matches=120, seed=0):
    df = synthetic_wp_frame(n_matches=n_matches, rounds=10, snaps=3, seed=seed)
    ids = sorted(df["match_id"].unique())
    df["fold"] = df["match_id"].map({m: i % 3 for i, m in enumerate(ids)})
    return df


CFG = {"features": ["x1", "x2", "tier"], "categorical": ["tier"], "label": "y", "stratum": "tier",
       "monotone": {"x1": 1}, "num_boost_round": 60, "early_stopping_rounds": 10, "es_fraction": 0.15,
       "train_row_fraction": 1.0, "seed": 7,
       "params": {"learning_rate": 0.1, "num_leaves": 7, "min_child_samples": 20, "num_threads": 2}}


def test_registered_as_loop_task():
    assert TASKS["gbdt_wp"] is gbdt_oof


def test_oof_rows_in_train_order_and_valid_probabilities():
    train = _train()
    out = gbdt_oof(train, CFG)
    assert list(out.columns) == ["match_id", "tier", "y", "p"]
    # the gated Verify compares champion and candidate row by row: order must not depend on the config
    expect = pd.concat([train[train["fold"] == k] for k in sorted(train["fold"].unique())])
    assert out["match_id"].tolist() == expect["match_id"].tolist() and out["y"].tolist() == expect["y"].tolist()
    assert out["p"].between(0, 1).all() and out["p"].std() > 0.05


def test_deterministic_for_a_seed():
    train = _train()
    a, b = gbdt_oof(train, CFG), gbdt_oof(train, CFG)
    np.testing.assert_array_equal(a["p"].to_numpy(), b["p"].to_numpy())


def test_early_stopping_slice_is_grouped_by_match():
    ids = pd.Series([f"m{i:03d}" for i in range(200)])
    es = es_matches(ids, fraction=0.2, seed=3)
    assert 20 <= len(es) <= 60 and es <= set(ids)
    assert es == es_matches(ids.sample(frac=1, random_state=1), fraction=0.2, seed=3)  # order-free


def test_monotone_constraint_holds():
    train = _train(seed=1)
    cfg = {**CFG, "features": ["x1", "noise1"], "categorical": [], "monotone": {"x1": 1}}
    from cscoach.models.wp_gbdt import fit_one

    fit = train[train["fold"] != 0]
    booster, cats = fit_one(fit, cfg)
    grid = pd.DataFrame({"x1": np.linspace(-3, 3, 50), "noise1": 0.0})
    p = booster.predict(prepare(grid, cfg, cats)[0])
    assert np.all(np.diff(p) >= -1e-12)


def test_categories_fixed_across_folds():
    train = _train()
    x, cats = prepare(train, CFG, None)
    x2, _ = prepare(train[train["tier"] == "low"], CFG, cats)
    assert list(x2["tier"].cat.categories) == list(x["tier"].cat.categories)


def test_unknown_monotone_feature_is_an_error():
    with pytest.raises(ValueError):
        gbdt_oof(_train(), {**CFG, "monotone": {"not_a_feature": 1}})
