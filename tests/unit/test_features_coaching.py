import numpy as np
import pandas as pd
import pytest

from cscoach.coaching.narrative import UngroundedNumberError, assert_grounded
from cscoach.coaching.shrinkage import normal_normal_shrinkage
from cscoach.features.duel import view_offset_deg
from cscoach.features.state import aggregate_team_state
from cscoach.ingest.tiers import TierMapper
from cscoach.spatial.navgraph import utility_delay_s


def test_aggregate_team_state():
    rows = []
    for side in ("CT", "T"):
        for i in range(5):
            rows.append(
                dict(
                    match_id="m",
                    round_num=1,
                    tick=100,
                    side=side,
                    is_alive=i < 4,
                    health=100,
                    armor=100,
                    has_helmet=True,
                    has_defuser=side == "CT",
                    equipment_value=4000,
                )
            )
    out = aggregate_team_state(pd.DataFrame(rows))
    r = out.iloc[0]
    assert r.alive_ct == 4 and r.alive_t == 4 and r.hp_sum_ct == 400 and r.n_kits_ct == 4
    assert r.man_advantage == 0


def test_view_offset():
    assert view_offset_deg([0, 0, 0], 0, 0, [100, 0, 0])[0] == pytest.approx(0, abs=1e-6)
    assert view_offset_deg([0, 0, 0], 90, 0, [100, 0, 0])[0] == pytest.approx(90)


def test_tier_mapper():
    tm = TierMapper()
    assert tm.from_faceit_level(10) == "semipro"
    assert tm.from_premier_rating(12000) == "mid"
    assert tm.match_tier(["low"] * 3) is None
    assert tm.match_tier(["mid"] * 6 + ["high"] * 4) == "mid"


def test_shrinkage_pulls_small_samples_harder():
    rng = np.random.default_rng(0)
    rows = [
        {"tier": "mid", "p": f"p{i}", "v": rng.normal(i % 3, 1)}
        for i in range(30)
        for _ in range(40)
    ]
    rows += [{"tier": "mid", "p": "tiny", "v": 5.0}, {"tier": "mid", "p": "tiny", "v": 6.0}]
    out = normal_normal_shrinkage(pd.DataFrame(rows), "p", "v").set_index("p")
    assert out.loc["tiny", "shrink_weight"] < out.loc["p0", "shrink_weight"]
    assert out.loc["tiny", "post_mean"] < 5.5


def test_grounding():
    assert_grounded("Round 7: WP 48% vs 22%", [7, 48, 22])
    with pytest.raises(UngroundedNumberError):
        assert_grounded("WP rises by 14%", [7])


def test_utility_delay():
    import networkx as nx

    g = nx.Graph()
    g.add_weighted_edges_from([(0, 1, 2.0), (1, 3, 2.0), (0, 2, 5.0), (2, 3, 5.0)], weight="time_s")
    assert utility_delay_s(g, 0, 3, blocked_nodes=[1]) == pytest.approx(6.0)
