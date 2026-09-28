"""Reproducible CSDS export from AWS Data Exchange (M1.2).

Steps (each is a subcommand; all are resumable):

1. ``index``  list the assets of every live revision in a date range → ``<root>/manifest/adx_assets.parquet``
               (asset id, revision id, revision date, name, size). This is also the match → revision map.
2. ``plan``   choose assets: the base channels (``header`` + the ``csds`` index) for every match, and all
               channels for a seeded sample of matches (``in_sample``). Skips assets already on disk with
               the same size. Prints counts, GB and the estimated S3 egress cost.
3. ``export`` run ADX ``EXPORT_ASSETS_TO_S3`` jobs for the plan (≤ 100 assets per job, ≤ 10 concurrent,
               one revision per job) into the export bucket, keyed by asset name.
4. ``sync``   ``aws s3 sync`` the bucket's ``csds/`` prefix to ``<root>/csds/``.

Settings come from ``configs/export.yaml`` (parameters and assumptions: docs/specs/06, "Data export").
Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import yaml

BASE_CHANNELS = ("header", "csds")
ASSETS_PER_JOB = 100  # ADX quota "Asset per export job from Amazon S3"
CONCURRENT_JOBS = 10  # ADX quota "Concurrent in progress jobs to export assets to Amazon S3"


def in_sample(match_id: str, *, seed: int, fraction: float) -> bool:
    """Deterministic, order-free sample: hash(seed, match_id) < fraction. Nested in ``fraction``."""
    h = int.from_bytes(hashlib.sha256(f"{seed}:{match_id}".encode()).digest()[:8], "big")
    return h / 2**64 < fraction


def sample_fraction(platform, cfg: dict) -> float:
    """Inclusion probability of a match in the full-channel sample (platform-stratified, docs/specs/06)."""
    return float((cfg.get("full_channel_fraction_by_platform") or {}).get(platform, cfg["full_channel_fraction"]))


def match_of(name: str) -> tuple[str, str, str]:
    """``csds/YYYY/MM/DD/<match_id>/<channel>`` → (folder date, match id, channel)."""
    _, y, m, d, match_id, channel = name.split("/")
    return f"{y}-{m}-{d}", match_id, channel


def plan_export(
    assets: pd.DataFrame, *, local_sizes: dict[str, int], seed: int, fraction: float,
    match_fraction: dict[str, float] | None = None,
) -> pd.DataFrame:
    """``fraction`` applies to every match unless ``match_fraction`` gives a per-match value (strata)."""
    # a revision can list the same file under several asset ids; one export per name is enough
    assets = assets.drop_duplicates("name")
    parts = assets["name"].map(match_of)
    df = assets.assign(
        folder_date=[p[0] for p in parts], match_id=[p[1] for p in parts], channel=[p[2] for p in parts]
    )
    mf = match_fraction or {}
    sampled = {m: in_sample(m, seed=seed, fraction=mf.get(m, fraction)) for m in df["match_id"].unique()}
    wanted = df["channel"].isin(BASE_CHANNELS) | df["match_id"].map(sampled)
    have = df["name"].map(local_sizes)
    return df[wanted & (have != df["size"])].reset_index(drop=True)


# ---------------------------------------------------------------- AWS side (thin, not unit-tested)

def _client(region):
    import boto3

    return boto3.client("dataexchange", region_name=region)


def live_revisions(client, dataset_id, start, end):
    revs = []
    for page in client.get_paginator("list_data_set_revisions").paginate(DataSetId=dataset_id):
        revs += page["Revisions"]
    return [
        r for r in revs
        if not r.get("Revoked") and r.get("Finalized") and start <= r["Comment"][:10] < end
    ]


def _list_assets(client, dataset_id, rev):
    rows = []
    pages = client.get_paginator("list_revision_assets").paginate(DataSetId=dataset_id, RevisionId=rev["Id"])
    for page in pages:
        for a in page["Assets"]:
            rows.append({
                "asset_id": a["Id"],
                "revision_id": rev["Id"],
                "revision_date": rev["Comment"][:10],
                "name": a["Name"],
                "size": int(a["AssetDetails"]["S3SnapshotAsset"]["Size"]),
            })
    return pd.DataFrame(rows)


def cmd_index(cfg, root: Path):
    client = _client(cfg["region"])
    out_dir = root / "manifest" / "adx_assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    revs = live_revisions(client, cfg["dataset_id"], cfg["start_date"], cfg["end_date"])
    todo = [r for r in revs if not (out_dir / f"{r['Id']}.parquet").exists()]
    print(f"revisions in range: {len(revs)}, to index: {len(todo)}")

    def one(rev):
        df = _list_assets(client, cfg["dataset_id"], rev)
        tmp = out_dir / f"{rev['Id']}.parquet.tmp"
        df.to_parquet(tmp, index=False)
        tmp.rename(out_dir / f"{rev['Id']}.parquet")
        return len(df)

    with ThreadPoolExecutor(8) as pool:
        for i, n in enumerate(pool.map(one, todo), 1):
            if i % 25 == 0 or i == len(todo):
                print(f"  indexed {i}/{len(todo)} (last: {n} assets)", flush=True)
    frames = [pd.read_parquet(out_dir / f"{r['Id']}.parquet") for r in revs]
    index = pd.concat(frames, ignore_index=True)
    index.to_parquet(root / "manifest" / "adx_assets.parquet", index=False)
    print(f"assets: {len(index)}, revisions: {len(revs)}, GB: {index['size'].sum() / 1e9:.1f}")


def local_sizes(root: Path, names) -> dict[str, int]:
    sizes = {}
    for n in names:
        p = root / n
        if p.is_file():
            sizes[n] = p.stat().st_size
    return sizes


def cmd_plan(cfg, root: Path, write=True) -> pd.DataFrame:
    assets = pd.read_parquet(root / "manifest" / "adx_assets.parquet")
    platforms = pd.read_parquet(root / "manifest" / "matches.parquet", columns=["match_id", "platform"])
    match_fraction = {m: sample_fraction(p, cfg) for m, p in zip(platforms["match_id"], platforms["platform"])}
    plan = plan_export(
        assets, local_sizes=local_sizes(root, assets["name"]), seed=cfg["sample_seed"],
        fraction=cfg["full_channel_fraction"], match_fraction=match_fraction,
    )
    gb = plan["size"].sum() / 1e9
    print(
        f"plan: {len(plan)} assets, {plan['match_id'].nunique()} matches, "
        f"{plan.loc[~plan['channel'].isin(BASE_CHANNELS), 'match_id'].nunique()} with full channels, "
        f"{plan['revision_id'].nunique()} revisions, {gb:.1f} GB, "
        f"est. egress ${gb * cfg['egress_usd_per_gb']:.0f}"
    )
    if write:
        plan.to_parquet(root / "manifest" / "export_plan.parquet", index=False)
    return plan


def _run_job(client, cfg, revision_id, batch):
    job = client.create_job(
        Type="EXPORT_ASSETS_TO_S3",
        Details={"ExportAssetsToS3": {
            "DataSetId": cfg["dataset_id"],
            "RevisionId": revision_id,
            "AssetDestinations": [
                {"AssetId": a, "Bucket": cfg["bucket"], "Key": n} for a, n in zip(batch["asset_id"], batch["name"])
            ],
        }},
    )
    client.start_job(JobId=job["Id"])
    while True:
        time.sleep(3)
        state = client.get_job(JobId=job["Id"])
        if state["State"] == "COMPLETED":
            return len(batch)
        if state["State"] in ("ERROR", "CANCELLED", "TIMED_OUT"):
            raise RuntimeError(f"job {job['Id']} {state['State']}: {state.get('Errors')}")


def cmd_export(cfg, root: Path):
    plan = pd.read_parquet(root / "manifest" / "export_plan.parquet")
    client = _client(cfg["region"])
    batches = [
        (rev, grp.iloc[i:i + ASSETS_PER_JOB])
        for rev, grp in plan.groupby("revision_id")
        for i in range(0, len(grp), ASSETS_PER_JOB)
    ]
    print(f"export: {len(plan)} assets in {len(batches)} jobs → s3://{cfg['bucket']}/")
    done = 0
    with ThreadPoolExecutor(CONCURRENT_JOBS) as pool:
        for n in pool.map(lambda b: _run_job(client, cfg, *b), batches):
            done += n
            if done % 5000 < ASSETS_PER_JOB:
                print(f"  exported {done}/{len(plan)}", flush=True)
    print(f"export done: {done} assets")


def cmd_sync(cfg, root: Path):
    cmd = ["aws", "s3", "sync", f"s3://{cfg['bucket']}/csds/", str(root / "csds"), "--size-only", "--only-show-errors"]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", choices=["index", "plan", "export", "sync"])
    ap.add_argument("--config", type=Path, default=Path("configs/export.yaml"))
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    root = Path(cfg["root"])
    {"index": cmd_index, "plan": cmd_plan, "export": cmd_export, "sync": cmd_sync}[args.step](cfg, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
