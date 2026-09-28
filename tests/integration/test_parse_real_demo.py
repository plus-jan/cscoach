"""Runs only when real demos exist in data/raw (M1.1)."""

from pathlib import Path

import pytest

DEMOS = sorted(Path(__file__).resolve().parents[2].joinpath("data/raw").rglob("*.dem"))

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not DEMOS, reason="no demos in data/raw")
@pytest.mark.parametrize("demo", DEMOS[:3], ids=lambda p: p.name)
def test_parse_demo(demo):
    pytest.importorskip("demoparser2")
    from cscoach.ingest.demo_parser import parse_demo

    parsed = parse_demo(demo, tick_stride=64)
    assert len(parsed.ticks) > 0
    assert "player_death" in parsed.events
    # TODO(M1.1): validate derived tables against schemas once rounds/state are built
