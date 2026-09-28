import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from cscoach.models.wp_data import COLUMNS, build_table


def _features(match_id: str, n: int, *, int_counts: bool, tier) -> pd.DataFrame:
    rng = np.random.default_rng(len(match_id) + n)
    f = pd.DataFrame({c: rng.random(n) for c in COLUMNS})
    f["match_id"], f["round_uid"] = match_id, [f"{match_id}_{i % 2 + 1}" for i in range(n)]
    f["round"], f["tick"], f["build_num"] = [i % 2 + 1 for i in range(n)], np.arange(n) * 64, 10900
    f["bomb_planted"] = [False] * n
    f["bomb_site"] = None
    for c in ("map_name", "platform", "channel_set"):
        f[c] = "x"
    f["tier"] = tier
    for c in ("ct_alive", "t_alive", "man_advantage"):
        f[c] = (np.arange(n) % 5).astype("int64" if int_counts else "float64")
    return f


def _root(tmp_path, matches):
    (tmp_path / "derived" / "state_features").mkdir(parents=True)
    (tmp_path / "derived" / "rounds").mkdir(parents=True)
    (tmp_path / "manifest").mkdir()
    for m, f in matches.items():
        f.to_parquet(tmp_path / "derived" / "state_features" / f"{m}.parquet", index=False)
        pd.DataFrame({"round": [1, 2], "winner_side": ["CT", "T"]}).to_parquet(
            tmp_path / "derived" / "rounds" / f"{m}.parquet", index=False)
    pd.DataFrame({"match_id": list(matches), "ok": True, "clean": True, "in_seeded_sample": True}).to_parquet(
        tmp_path / "manifest" / "rounds_check.parquet", index=False)
    return tmp_path


def test_build_table_streams_mixed_schemas(tmp_path):
    # per-match files differ in type (int vs double counts, all-null tier/bomb_site); the table has one schema
    root = _root(tmp_path, {"m1": _features("m1", 6, int_counts=True, tier=None),
                            "m2": _features("m2", 4, int_counts=False, tier="high")})
    out = build_table(root, workers=2, batch_rows=5)
    t = pd.read_parquet(out)
    assert len(t) == 10 and set(t["match_id"]) == {"m1", "m2"}
    assert (t["y_ct_win"] == (t["round"] == 1).astype("int8")).all()
    schema = pq.read_schema(out)
    assert str(schema.field("ct_alive").type) == "float"
    assert str(schema.field("tier").type) == "string" and str(schema.field("tick").type) == "int64"
    assert t.loc[t["match_id"] == "m2", "tier"].eq("high").all() and t.loc[t["match_id"] == "m1", "tier"].isna().all()
    assert not list(root.glob("derived/*.tmp"))
