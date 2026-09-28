"""Tests for the export planner (M1.2). Synthetic asset lists: they prove code behaviour only (A-33)."""
import pandas as pd

from cscoach.data.export import BASE_CHANNELS, in_sample, match_of, plan_export


def assets(matches, channels=("header", "csds", "player_vector", "round_end"), revision="r1", day="2026/08/10"):
    rows = []
    for m in matches:
        for c in channels:
            rows.append({"asset_id": f"{m}-{c}", "revision_id": revision, "name": f"csds/{day}/{m}/{c}", "size": 100})
    return pd.DataFrame(rows)


def test_in_sample_is_deterministic_and_seeded():
    ids = [f"{i:08x}-0000-4000-8000-000000000000" for i in range(4000)]
    a = [in_sample(m, seed=1, fraction=0.25) for m in ids]
    assert a == [in_sample(m, seed=1, fraction=0.25) for m in ids]
    assert a != [in_sample(m, seed=2, fraction=0.25) for m in ids]
    assert 0.22 < sum(a) / len(a) < 0.28


def test_in_sample_nested_in_fraction():
    ids = [f"m{i}" for i in range(2000)]
    small = {m for m in ids if in_sample(m, seed=7, fraction=0.1)}
    large = {m for m in ids if in_sample(m, seed=7, fraction=0.3)}
    assert small <= large  # raising the fraction only adds matches


def test_match_of():
    assert match_of("csds/2026/08/10/abc/header") == ("2026-08-10", "abc", "header")


def test_plan_takes_base_channels_for_all_and_all_channels_for_sample():
    ids = [f"m{i}" for i in range(300)]
    plan = plan_export(assets(ids), local_sizes={}, seed=3, fraction=0.2)
    sampled = {m for m in ids if in_sample(m, seed=3, fraction=0.2)}
    got = plan.groupby("match_id")["channel"].apply(set)
    for m in ids:
        want = {"header", "csds", "player_vector", "round_end"} if m in sampled else set(BASE_CHANNELS)
        assert got[m] == want


def test_plan_skips_assets_already_on_disk_with_same_size():
    a = assets(["m1"])
    local = {"csds/2026/08/10/m1/header": 100, "csds/2026/08/10/m1/csds": 99}
    plan = plan_export(a, local_sizes=local, seed=3, fraction=0.0)
    assert list(plan["name"]) == ["csds/2026/08/10/m1/csds"]  # size differs → re-export


def test_plan_keeps_revision_ids():
    plan = plan_export(assets(["m1"], revision="rev-9"), local_sizes={}, seed=3, fraction=1.0)
    assert set(plan["revision_id"]) == {"rev-9"}


def test_plan_exports_each_name_once():
    a = assets(["m1"])
    a = pd.concat([a, a.assign(asset_id=a["asset_id"] + "-dup")], ignore_index=True)
    plan = plan_export(a, local_sizes={}, seed=3, fraction=1.0)
    assert plan["name"].is_unique and len(plan) == 4
