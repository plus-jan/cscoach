"""Meta-analytics for player metrics (after Franks, D'Amour, Cervone & Bornn, 2016).

Practical approximations used here (documented in docs/specs/04_validation_protocol.md):

- discrimination: 1 - E[within-player sampling variance] / total between-player variance,
  sampling variance estimated by bootstrapping each player's observations.
- stability: split-half correlation (odd vs even observations, or two periods) with the
  Spearman-Brown correction.
- independence: 1 - R^2 of the metric regressed on reference stats (K/D, ADR, ...).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _player_means(df: pd.DataFrame, player_col: str, value_col: str) -> pd.Series:
    return df.groupby(player_col)[value_col].mean()


def discrimination(
    df: pd.DataFrame,
    player_col: str,
    value_col: str,
    n_boot: int = 200,
    seed: int = 0,
    min_obs: int = 2,
) -> float:
    """Fraction of between-player variance of the player-mean not explained by noise."""
    rng = np.random.default_rng(seed)
    groups = [g.to_numpy(float) for _, g in df.groupby(player_col)[value_col] if len(g) >= min_obs]
    if len(groups) < 2:
        return float("nan")
    means = np.array([g.mean() for g in groups])
    total = means.var(ddof=1)
    if total <= 0:
        return 0.0
    within = []
    for g in groups:
        boots = rng.choice(g, size=(n_boot, len(g)), replace=True).mean(axis=1)
        within.append(boots.var(ddof=1))
    return float(np.clip(1.0 - np.mean(within) / total, 0.0, 1.0))


def stability(
    df: pd.DataFrame,
    player_col: str,
    value_col: str,
    order_col: str | None = None,
    min_obs: int = 4,
) -> float:
    """Spearman-Brown corrected split-half reliability of player means.

    Observations are ordered by ``order_col`` (e.g. match date) and split odd/even.
    """
    d = df.sort_values(order_col) if order_col else df
    d = d.assign(_half=d.groupby(player_col).cumcount() % 2)
    counts = d.groupby(player_col).size()
    d = d[d[player_col].isin(counts.index[counts >= min_obs])]
    halves = d.groupby([player_col, "_half"])[value_col].mean().unstack()
    halves = halves.dropna()
    if len(halves) < 3:
        return float("nan")
    r = float(np.corrcoef(halves[0], halves[1])[0, 1])
    if not np.isfinite(r):
        return float("nan")
    return float(2 * r / (1 + r)) if r > -1 else float("nan")


def independence(player_table: pd.DataFrame, metric_col: str, reference_cols: list[str]) -> float:
    """1 - R^2 of metric on reference metrics across players (OLS with intercept)."""
    d = player_table[[metric_col, *reference_cols]].dropna()
    if len(d) <= len(reference_cols) + 1:
        return float("nan")
    X = np.column_stack([np.ones(len(d)), d[reference_cols].to_numpy(float)])
    y = d[metric_col].to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    ss_tot = float(((y - y.mean()) ** 2).sum())
    if ss_tot == 0:
        return float("nan")
    return float(np.clip(resid @ resid / ss_tot, 0.0, 1.0))
