"""End-to-end WP training entry point used by the CLI and tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from cscoach.models.baseline_wp import BaselineWinProbability
from cscoach.models.win_probability import GBDTWinProbability
from cscoach.validation.splits import GroupSplit, assert_no_group_leakage, grouped_split


@dataclass
class WPTrainingResult:
    model: GBDTWinProbability
    baseline: BaselineWinProbability
    split: GroupSplit
    test_frame: pd.DataFrame  # test rows with columns p_wp and p_baseline


def train_wp(df: pd.DataFrame, cfg: dict[str, Any]) -> WPTrainingResult:
    """Grouped split → baseline + GBDT (early stopping on a slice of train matches) →
    per-tier calibration on the calibration fold → predictions on the test fold."""
    target, group = cfg["target"], cfg["group_col"]
    s = cfg["split"]
    split = grouped_split(
        df, group, (s["train"], s["calibration"], s["test"]), cfg.get("tier_col"), s["seed"]
    )
    train, cal, test = df.loc[split.train], df.loc[split.calibration], df.loc[split.test]
    # early-stopping slice: hold out ~15% of *training matches*
    inner = grouped_split(train, group, (0.85, 0.0, 0.15), seed=s["seed"] + 1)
    fit_part, es_part = train.loc[inner.train], train.loc[inner.test]
    assert_no_group_leakage(df, group, fit_part, es_part, cal, test)

    baseline = BaselineWinProbability().fit(train, train[target])
    model = GBDTWinProbability(cfg).fit(
        fit_part,
        fit_part[target],
        valid=(es_part, es_part[target]),
        calibration=(cal, cal[target]),
    )
    test = test.assign(p_wp=model.predict_proba(test), p_baseline=baseline.predict_proba(test))
    return WPTrainingResult(model, baseline, split, test)
