"""Navigation graph per map and shortest-path utilities (M7.1–M7.3)."""

from __future__ import annotations

from collections.abc import Iterable

import networkx as nx


def load_nav_graph(map_name: str) -> nx.Graph:
    """Load nav areas/connections for ``map_name`` (source decided in ADR, e.g. awpy)."""
    raise NotImplementedError("M7.1: nav graph loading")


def shortest_time(g: nx.Graph, src: int, dst: int, weight: str = "time_s") -> float:
    try:
        return float(nx.shortest_path_length(g, src, dst, weight=weight))
    except nx.NetworkXNoPath:
        return float("inf")


def utility_delay_s(
    g: nx.Graph, src: int, dst: int, blocked_nodes: Iterable[int], weight: str = "time_s"
) -> float:
    """Extra travel time from ``src`` to ``dst`` when ``blocked_nodes`` (smoke/molly
    covered areas) are impassable. inf if fully blocked."""
    base = shortest_time(g, src, dst, weight)
    h = g.subgraph(n for n in g.nodes if n not in set(blocked_nodes))
    if src not in h or dst not in h:
        return float("inf")
    return shortest_time(h, src, dst, weight) - base
