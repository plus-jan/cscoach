"""WP modelling table and the sealed WP split (M3).

- ``build_table``: one row per snapshot of the eligible matches (clean, seeded, reconciled rounds) with the state
  features and the label ``y_ct_win`` (attached only here, docs/specs/02); written once to
  ``<root>/derived/wp_table_v1.parquet``.
- ``build_split``: the one-time WP split in ``<root>/splits/wp_v1/split.json`` (docs/specs/04 §1): matches of the newest
  builds (≥ ``temporal_from_build``) form the sealed ``temporal`` holdout (A-29); the rest is split 70/10/20 by match,
  stratified by platform × tier × map. Calibration, test and temporal are sealed (docs/specs/07).
Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

COLUMNS = ["match_id", "round_uid", "round", "tick", "second_in_round", "ct_alive", "t_alive", "ct_hp_sum", "t_hp_sum",
           "ct_armor_sum", "t_armor_sum", "ct_helmets", "t_helmets", "ct_kits", "ct_equip_value", "t_equip_value",
           "ct_money_sum", "t_money_sum", "ct_primaries", "t_primaries", "ct_flashes", "t_flashes", "ct_smokes",
           "t_smokes", "ct_molotovs", "t_molotovs", "ct_hes", "t_hes", "man_advantage", "bomb_planted", "bomb_site",
           "time_remaining_s", "map_name", "platform", "tier", "channel_set", "build_num"]
_STRINGS = {"match_id", "round_uid", "bomb_site", "map_name", "platform", "tier", "channel_set"}
_INTS = {"round", "tick", "build_num"}
# one schema for all matches: per-match files differ (int vs double counts, all-null tier/bomb_site)
SCHEMA = pa.schema([(c, pa.string() if c in _STRINGS else pa.int64() if c in _INTS
                     else pa.bool_() if c == "bomb_planted" else pa.float32()) for c in COLUMNS]
                   + [("y_ct_win", pa.int8())])


def _one(args):
    root, m = args
    f = pd.read_parquet(Path(root) / "derived" / "state_features" / f"{m}.parquet", columns=COLUMNS)
    r = pd.read_parquet(Path(root) / "derived" / "rounds" / f"{m}.parquet", columns=["round", "winner_side"])
    f = f.merge(r, on="round")
    f["y_ct_win"] = (f.pop("winner_side") == "CT").astype("int8")
    return pa.Table.from_pandas(f[SCHEMA.names], preserve_index=False).cast(SCHEMA)


def eligible(root: Path) -> pd.DataFrame:
    chk = pd.read_parquet(root / "manifest" / "rounds_check.parquet")
    e = chk[chk["ok"] & chk["clean"] & chk["in_seeded_sample"].fillna(False).astype(bool)]
    have = {p.stem for p in (root / "derived" / "state_features").glob("*.parquet")}
    return e[e["match_id"].isin(have)]


def build_table(root: Path, workers: int = 12, batch_rows: int = 1_000_000) -> Path:
    """Streams the per-match parts into row groups of ~``batch_rows`` (the full table does not fit in memory as
    pandas); written to a temporary file and renamed, so an interrupted build leaves no partial table."""
    ids = list(eligible(root)["match_id"])
    out = root / "derived" / "wp_table_v1.parquet"
    tmp = out.with_suffix(".parquet.tmp")
    buf, n = [], 0
    with ProcessPoolExecutor(workers) as pool, pq.ParquetWriter(tmp, SCHEMA) as w:
        for part in pool.map(_one, [(str(root), m) for m in ids], chunksize=32):
            buf.append(part)
            n += part.num_rows
            if n >= batch_rows:
                w.write_table(pa.concat_tables(buf))
                buf, n = [], 0
        if buf:
            w.write_table(pa.concat_tables(buf))
    tmp.replace(out)
    return out


def build_split(root: Path, cfg: dict) -> dict:
    from cscoach.eval.splits import grouped_split, kfold_groups
    from cscoach.loops.sealed import _hash

    work = root / "splits" / cfg["split_name"]
    if (work / "split.json").exists():
        raise FileExistsError(f"{work}/split.json exists: the WP split is made once (sealed folds)")
    q = pd.read_parquet(root / "manifest" / "match_quality.parquet")[["match_id", "platform", "map_name"]]
    t = pd.read_parquet(root / "manifest" / "match_tiers.parquet")[["match_id", "tier"]]
    from cscoach.data.quality import curator

    h = curator(cfg).get_dataframe(cfg["header_tome"])[["match_id", "build_num"]]
    g = eligible(root)[["match_id"]].merge(q, on="match_id").merge(t, on="match_id", how="left").merge(h, on="match_id")
    g["tier"] = g["tier"].fillna("null")
    temporal = set(g.loc[g["build_num"] >= cfg["temporal_from_build"], "match_id"])
    rest = g[~g["match_id"].isin(temporal)].copy()
    rest["stratum"] = rest["platform"] + "|" + rest["tier"] + "|" + rest["map_name"]
    split = grouped_split(rest[["match_id", "stratum"]], fractions=cfg["fractions"], seed=cfg["seed"])
    split.update({m: "temporal" for m in temporal})
    train = sorted(m for m, s in split.items() if s == "train")
    body = {"seed": cfg["seed"], "fractions": cfg["fractions"], "k": cfg["k"], "split": split,
            "folds": kfold_groups(train, k=cfg["k"], seed=cfg["seed"])}
    body["sha256"] = _hash({key: body[key] for key in ("seed", "fractions", "k", "split", "folds")})
    work.mkdir(parents=True, exist_ok=True)
    (work / "split.json").write_text(json.dumps(body, sort_keys=True))
    return body


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", choices=["table", "split"])
    ap.add_argument("--config", type=Path, default=Path("configs/wp_split.yaml"))
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    root = Path(cfg["root"])
    if args.step == "table":
        print(build_table(root))
    else:
        body = build_split(root, cfg)
        print(json.dumps(pd.Series(body["split"]).value_counts().to_dict()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
