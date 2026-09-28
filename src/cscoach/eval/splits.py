"""Match-grouped splits (docs/specs/04 §1 and §7, ADR-0001)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def grouped_split(groups: pd.DataFrame, *, fractions: dict[str, float], seed: int,
                  group_col: str = "match_id", stratum_col: str = "stratum") -> dict[str, str]:
    """Shuffle the groups within each stratum with a seeded RNG and cut them by ``fractions`` (in the given order).
    The last split gets the remainder, and each non-empty stratum puts at least one group into every split listed
    after the first one when it has enough groups (so every stratum appears in the test split)."""
    rng = np.random.default_rng(seed)
    names = list(fractions)
    out: dict[str, str] = {}
    for _, g in groups.sort_values(group_col).groupby(stratum_col, sort=True):
        ids = g[group_col].to_numpy().copy()
        rng.shuffle(ids)
        n = len(ids)
        cuts, start = {}, 0
        for i, name in enumerate(names):
            if i == len(names) - 1:
                k = n - start
            else:
                k = int(round(fractions[name] * n))
                remaining = len(names) - 1 - i
                k = min(k, n - start - min(remaining, max(0, n - start - 1)))  # leave ≥1 for later splits if possible
            cuts[name] = ids[start:start + k]
            start += k
        for name, part in cuts.items():
            for m in part:
                out[str(m)] = name
    assert len(out) == len(groups), "split must be complete"
    return out


def kfold_groups(match_ids, *, k: int, seed: int) -> dict[str, int]:
    ids = np.array(sorted(map(str, match_ids)))
    np.random.default_rng(seed).shuffle(ids)
    return {m: int(i % k) for i, m in enumerate(ids)}
