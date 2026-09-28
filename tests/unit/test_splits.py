import pandas as pd
import pytest

from cscoach.validation.splits import (
    LeakageError,
    assert_no_group_leakage,
    grouped_kfold,
    grouped_split,
)


def test_grouped_split_disjoint_and_complete(synth_df):
    s = grouped_split(synth_df, "match_id", (0.7, 0.1, 0.2), stratify_col="tier", seed=0)
    parts = [set(synth_df.loc[i, "match_id"]) for i in (s.train, s.calibration, s.test)]
    assert not (parts[0] & parts[1]) and not (parts[0] & parts[2]) and not (parts[1] & parts[2])
    assert len(s.train) + len(s.calibration) + len(s.test) == len(synth_df)
    # every tier present in test
    assert set(synth_df.loc[s.test, "tier"]) == set(synth_df["tier"])


def test_kfold_disjoint(synth_df):
    for tr, va in grouped_kfold(synth_df, n_splits=4):
        assert not set(synth_df.loc[tr, "match_id"]) & set(synth_df.loc[va, "match_id"])


def test_leakage_detected():
    df = pd.DataFrame({"match_id": ["a", "a", "b"]})
    with pytest.raises(LeakageError):
        assert_no_group_leakage(df, "match_id", df.iloc[[0]], df.iloc[[1, 2]])
