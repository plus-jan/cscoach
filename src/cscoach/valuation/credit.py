"""Shapley-value credit assignment over contributors (M5.3).

``value_fn(coalition)`` must return the team WP of the counterfactual state in which only
the contributors in ``coalition`` performed their actions (built from the WP model).
Efficiency holds by construction: sum(credits) == value_fn(all) - value_fn(empty).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from itertools import permutations
from math import factorial

import numpy as np

ValueFn = Callable[[frozenset[str]], float]


def shapley_values(
    players: Sequence[str],
    value_fn: ValueFn,
    n_permutations: int | None = None,
    seed: int = 0,
) -> dict[str, float]:
    """Exact Shapley values for <= 7 players, else Monte-Carlo permutation sampling."""
    players = list(players)
    phi = dict.fromkeys(players, 0.0)
    cache: dict[frozenset[str], float] = {}

    def v(s: frozenset[str]) -> float:
        if s not in cache:
            cache[s] = float(value_fn(s))
        return cache[s]

    if n_permutations is None and len(players) <= 7:
        orders: list[tuple[str, ...]] = list(permutations(players))
    else:
        rng = np.random.default_rng(seed)
        k = n_permutations or 200
        orders = [tuple(rng.permutation(players)) for _ in range(k)]
    for order in orders:
        coalition: frozenset[str] = frozenset()
        for p in order:
            nxt = coalition | {p}
            phi[p] += v(nxt) - v(coalition)
            coalition = nxt
    n = len(orders) if orders else factorial(len(players))
    return {p: val / n for p, val in phi.items()}
