"""Leakage-safe data splits. See ADR-0001: always group by match."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd


class LeakageError(AssertionError):
    """Raised when a group appears in more than one split."""


@dataclass(frozen=True)
class GroupSplit:
    train: pd.Index
    calibration: pd.Index
    test: pd.Index


def grouped_split(
    df: pd.DataFrame,
    group_col: str = "match_id",
    fractions: Sequence[float] = (0.7, 0.1, 0.2),
    stratify_col: str | None = None,
    seed: int = 42,
) -> GroupSplit:
    """Split rows into train/calibration/test so every group lands in exactly one split.

    If ``stratify_col`` is given (e.g. ``tier``), groups are allocated per stratum using the
    group's most frequent stratum value, keeping tier proportions similar across splits.
    """
    if len(fractions) != 3 or not np.isclose(sum(fractions), 1.0):
        raise ValueError("fractions must be 3 values summing to 1")
    rng = np.random.default_rng(seed)
    if stratify_col is None:
        strata = {None: df[group_col].unique()}
    else:
        g2s = df.groupby(group_col)[stratify_col].agg(
            lambda s: s.mode().iloc[0] if s.notna().any() else "__na__"
        )
        strata = {k: v.index.to_numpy() for k, v in g2s.groupby(g2s)}
    buckets: list[list[object]] = [[], [], []]
    for groups in strata.values():
        groups = np.array(groups, dtype=object)
        rng.shuffle(groups)
        n = len(groups)
        n_train = int(round(fractions[0] * n))
        n_cal = int(round(fractions[1] * n))
        buckets[0].extend(groups[:n_train])
        buckets[1].extend(groups[n_train : n_train + n_cal])
        buckets[2].extend(groups[n_train + n_cal :])
    g = df[group_col]
    split = GroupSplit(
        train=df.index[g.isin(buckets[0])],
        calibration=df.index[g.isin(buckets[1])],
        test=df.index[g.isin(buckets[2])],
    )
    assert_no_group_leakage(
        df, group_col, df.loc[split.train], df.loc[split.calibration], df.loc[split.test]
    )
    return split


def grouped_kfold(
    df: pd.DataFrame, group_col: str = "match_id", n_splits: int = 5, seed: int = 42
) -> Iterator[tuple[pd.Index, pd.Index]]:
    """Yield (train_index, val_index) pairs with groups never shared across folds."""
    rng = np.random.default_rng(seed)
    groups = np.array(df[group_col].unique(), dtype=object)
    rng.shuffle(groups)
    folds = np.array_split(groups, n_splits)
    for k in range(n_splits):
        val_mask = df[group_col].isin(folds[k])
        yield df.index[~val_mask], df.index[val_mask]


def temporal_split(
    df: pd.DataFrame, time_col: str, cutoff: object, group_col: str = "match_id"
) -> tuple[pd.Index, pd.Index]:
    """Train on groups whose (min) time < cutoff, test on the rest (drift check)."""
    gtime = df.groupby(group_col)[time_col].min()
    train_groups = gtime.index[gtime < cutoff]
    mask = df[group_col].isin(train_groups)
    return df.index[mask], df.index[~mask]


def assert_no_group_leakage(df: pd.DataFrame, group_col: str, *parts: pd.DataFrame) -> None:
    """Raise :class:`LeakageError` if any group value occurs in two parts."""
    seen: dict[object, int] = {}
    for i, part in enumerate(parts):
        for gval in part[group_col].unique():
            if gval in seen and seen[gval] != i:
                raise LeakageError(f"group {gval!r} in split {seen[gval]} and {i}")
            seen[gval] = i
