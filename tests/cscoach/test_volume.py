"""Tests for the data volume check (M1.5). Synthetic frames: code behaviour only (A-33)."""
import math

import pandas as pd
import pytest

from cscoach.data.volume import fraction_needed, gap_table

TARGETS = {"min_matches_per_bucket": 300, "min_test_rounds_per_stratum": 500, "test_share": 0.2}


def test_fraction_needed_scales_linearly_and_caps_at_one():
    # 150 matches at fraction 0.15 → 300 needs 0.30
    assert fraction_needed(150, 0.15, 300) == pytest.approx(0.30)
    assert fraction_needed(300, 0.15, 300) == pytest.approx(0.15)
    assert fraction_needed(400, 0.15, 300) == pytest.approx(0.15)  # never below the current fraction
    assert math.isinf(fraction_needed(0, 0.15, 300))
    assert fraction_needed(20, 0.15, 300) == float("inf")  # would need > 1.0: unreachable


def test_gap_table_counts_matches_and_rounds():
    df = pd.DataFrame({
        "platform": ["steam"] * 3 + ["faceit"],
        "tier": ["low", "low", "mid", "low"],
        "rounds": [20, 22, 24, 21],
    })
    g = gap_table(df, ["platform", "tier"], current_fraction=0.15, targets=TARGETS).set_index(["platform", "tier"])
    assert g.loc[("steam", "low"), "matches"] == 2 and g.loc[("steam", "low"), "rounds"] == 42
    assert g.loc[("steam", "low"), "test_rounds_expected"] == pytest.approx(8.4)
    # matches: 2 → 300 needs ×150 → fraction 22.5 → unreachable
    assert math.isinf(g.loc[("steam", "low"), "fraction_needed"])
    assert not g.loc[("steam", "low"), "meets_targets"]


def test_gap_table_binding_constraint_is_the_larger_fraction():
    df = pd.DataFrame({"tier": ["low"] * 250, "rounds": [10] * 250})
    g = gap_table(df, ["tier"], current_fraction=0.15, targets=TARGETS).iloc[0]
    # matches: 250 → 300 needs 0.18; test rounds: 0.2 * 2500 = 500 → already met
    assert g["fraction_needed_matches"] == pytest.approx(0.18)
    assert g["fraction_needed_rounds"] == pytest.approx(0.15)
    assert g["fraction_needed"] == pytest.approx(0.18)


def test_gap_table_uses_stratum_inclusion_probability():
    df = pd.DataFrame({"platform": ["steam"] * 200 + ["faceit"] * 200, "rounds": [20] * 400,
                       "inclusion_prob": [0.35] * 200 + [1.0] * 200})
    g = gap_table(df, ["platform"], current_fraction=0.35, targets=TARGETS).set_index("platform")
    assert g.loc["steam", "fraction_needed"] == pytest.approx(0.525)  # 200 → 300 needs 0.35·1.5
    assert math.isinf(g.loc["faceit", "fraction_needed"])  # already fully included, still short
    assert g.loc["faceit", "current_fraction"] == pytest.approx(1.0)
