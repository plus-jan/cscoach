"""Counterfactual recourse (M9.2): minimal feasible alternative action → ΔWP with CI."""

from __future__ import annotations

import pandas as pd


def evaluate_counterfactuals(candidates: pd.DataFrame, context: dict[str, object]) -> pd.DataFrame:
    """Add ``wpa_at_stake``, ``ci_low``, ``ci_high`` to each candidate.

    CI from model uncertainty (bootstrap ensemble of WP models trained on match
    resamples) — items whose CI contains 0 must be dropped (docs/specs/04 §5).
    """
    raise NotImplementedError("M9.2: counterfactual state construction + WP re-evaluation")
