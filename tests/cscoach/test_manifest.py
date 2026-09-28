"""Tests for the export manifest (M1.2). Synthetic fixtures: they prove code behaviour only (A-33)."""
import gzip
import json

import pandas as pd
import pytest

from cscoach.data.manifest import build_manifest, channel_set_version, summarize_by_revision_date

CHANNELS_V42 = [f"ch{i:02d}" for i in range(39)] + ["header", "player_vector", "player_status"]
CHANNELS_V30 = [f"ch{i:02d}" for i in range(27)] + ["header", "player_vector", "player_status"]


def make_match(root, day, match_id, channels, downloaded, ppp="8.5.0", platform="steam"):
    y, m, d = day.split("-")
    mdir = root / "csds" / y / m / d / match_id
    mdir.mkdir(parents=True)
    index = {
        "id": match_id,
        "platform": platform,
        "matchDate": f"{day}T20:06+00:00",
        "context": {"version": ppp},
        "channels": [{"channel": c, "columns": []} for c in channels],
    }
    (mdir / "csds").write_bytes(gzip.compress(json.dumps(index).encode()))
    for c in downloaded:
        (mdir / c).write_bytes(b"x" * 10)
    return mdir


@pytest.fixture
def corpus(tmp_path):
    make_match(tmp_path, "2026-08-10", "m1", CHANNELS_V42, CHANNELS_V42)
    make_match(tmp_path, "2026-08-10", "m2", CHANNELS_V42, ["header"])
    make_match(tmp_path, "2026-07-20", "m3", CHANNELS_V30, CHANNELS_V30, ppp="8.4.0", platform="faceit")
    return tmp_path


def test_channel_set_version():
    assert channel_set_version(42) == "v42"
    assert channel_set_version(30) == "v30"
    assert channel_set_version(31) == "other"


def test_manifest_one_row_per_match(corpus):
    m = build_manifest(corpus).set_index("match_id")
    assert list(m.index.sort_values()) == ["m1", "m2", "m3"]
    assert m.loc["m1", "revision_date"] == "2026-08-10"
    assert m.loc["m1", "channel_set"] == "v42" and m.loc["m3", "channel_set"] == "v30"
    assert m.loc["m3", "ppp_version"] == "8.4.0" and m.loc["m3", "platform"] == "faceit"


def test_manifest_completeness(corpus):
    m = build_manifest(corpus).set_index("match_id")
    assert m.loc["m1", "complete"] and m.loc["m1", "has_telemetry"]
    assert not m.loc["m2", "complete"] and m.loc["m2", "n_channels_present"] == 1
    assert m.loc["m2", "n_channels_indexed"] == 42
    assert m.loc["m1", "bytes"] == 42 * 10 + m.loc["m1", "index_bytes"]


def test_missing_or_broken_index_is_flagged_not_dropped(corpus):
    mdir = corpus / "csds" / "2026" / "08" / "10" / "m4"
    mdir.mkdir()
    (mdir / "header").write_bytes(b"x")
    (mdir / "csds").write_bytes(b"not gzip")
    m = build_manifest(corpus).set_index("match_id")
    assert not m.loc["m4", "index_ok"]
    assert pd.isna(m.loc["m4", "channel_set"])


def test_summary_by_revision_date(corpus):
    s = summarize_by_revision_date(build_manifest(corpus)).set_index("revision_date")
    assert s.loc["2026-08-10", "n_matches"] == 2
    assert s.loc["2026-08-10", "n_complete"] == 1
    assert s.loc["2026-08-10", "n_v42"] == 2
    assert s.loc["2026-08-10", "n_index_broken"] == 0
    assert s.loc["2026-07-20", "ppp_versions"] == "8.4.0"
    assert "match_id" not in s.columns


def test_attach_revisions_and_sample(corpus):
    from cscoach.data.manifest import attach_revisions

    assets = pd.DataFrame(
        {
            "name": ["csds/2026/08/10/m1/header", "csds/2026/08/10/m1/csds", "csds/2026/08/10/m2/header"],
            "revision_id": ["r1", "r1", "r2"],
            "revision_date": ["2026-08-11", "2026-08-11", "2026-08-10"],
        }
    )
    cfg = {"sample_seed": 1, "full_channel_fraction": 1.0}
    m = attach_revisions(build_manifest(corpus), assets, cfg=cfg).set_index("match_id")
    assert m.loc["m1", "revision_id"] == "r1" and m.loc["m1", "adx_revision_date"] == "2026-08-11"
    assert m.loc["m2", "revision_id"] == "r2"
    assert pd.isna(m.loc["m3", "revision_id"])  # not in the asset index → null, never guessed
    assert m["in_seeded_sample"].all()
    s = summarize_by_revision_date(m).set_index("revision_date")
    assert s.loc["2026-08-10", "revision_ids"] == "r1;r2"


def test_attach_revisions_per_platform_inclusion(corpus):
    from cscoach.data.manifest import attach_revisions

    assets = pd.DataFrame({c: pd.Series([], dtype=str) for c in ("name", "revision_id", "revision_date")})
    cfg = {"sample_seed": 1, "full_channel_fraction": 0.0, "full_channel_fraction_by_platform": {"faceit": 1.0}}
    m = attach_revisions(build_manifest(corpus), assets, cfg=cfg).set_index("match_id")
    assert m.loc["m3", "in_seeded_sample"] and m.loc["m3", "inclusion_prob"] == 1.0  # faceit
    assert not m.loc["m1", "in_seeded_sample"] and m.loc["m1", "inclusion_prob"] == 0.0
