"""Empirical-Bayes shrinkage of per-player metrics toward the tier prior (M8.1)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def normal_normal_shrinkage(
    df: pd.DataFrame,
    player_col: str,
    value_col: str,
    prior_group_col: str | None = "tier",
    cred: float = 0.8,
) -> pd.DataFrame:
    """Posterior mean and credible interval per player under a normal-normal model.

    For each prior group: tau^2 = max(var(player means) - mean(sigma^2/n), eps), with
    sigma^2 the pooled within-player variance. Posterior mean
    = w * player_mean + (1 - w) * group_mean, w = tau^2 / (tau^2 + sigma^2/n).
    """
    keys = [prior_group_col] if prior_group_col else []
    g = df.groupby([*keys, player_col])[value_col].agg(["mean", "var", "count"]).reset_index()
    out = []
    parts = g.groupby(prior_group_col) if prior_group_col else [(None, g)]
    z = stats.norm.ppf(0.5 + cred / 2)
    for _, part in parts:
        sigma2 = float(np.nanmean(part["var"])) if part["var"].notna().any() else 0.0
        se2 = sigma2 / part["count"]
        mu = float(np.average(part["mean"], weights=part["count"]))
        tau2 = (
            max(float(part["mean"].var(ddof=1)) - float(se2.mean()), 1e-12)
            if len(part) > 1
            else 1e-12
        )
        w = tau2 / (tau2 + se2)
        post_mean = w * part["mean"] + (1 - w) * mu
        post_sd = np.sqrt(1.0 / (1.0 / tau2 + 1.0 / se2.clip(lower=1e-12)))
        out.append(
            part.assign(
                prior_mean=mu,
                shrink_weight=w,
                post_mean=post_mean,
                ci_low=post_mean - z * post_sd,
                ci_high=post_mean + z * post_sd,
            )
        )
    return pd.concat(out, ignore_index=True)
