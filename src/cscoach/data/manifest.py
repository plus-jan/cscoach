"""Export manifest for the local CSDS collection (M1.2).

Scans ``<root>/csds/YYYY/MM/DD/<match_id>/`` and records, per match, what the export contains: the
revision date (the folder date = the ADX revision comment), platform, ppp_version, the channel-set
version from the per-match ``csds`` index (never a hard-coded channel list), which indexed channels were
downloaded, and the bytes on disk.

Outputs:
- per-match manifest (contains match ids; stays next to the data, not in the repo);
- per-revision-date summary (counts only; committed as the export record).

Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import gzip
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

INDEX_FILE = "csds"
TELEMETRY_CHANNELS = ("player_vector", "player_status")


def channel_set_version(n_channels: int) -> str:
    """Channel-set label from the number of indexed channels (docs/data/README.md: 30 before, 42 since 2026-08-04)."""
    return {30: "v30", 42: "v42"}.get(n_channels, "other")


def scan_match(mdir: Path) -> dict:
    y, m, d = mdir.parts[-4:-1]
    files = {p.name: p.stat().st_size for p in mdir.iterdir() if p.is_file()}
    row = {
        "match_id": mdir.name,
        "revision_date": f"{y}-{m}-{d}",
        "index_ok": False,
        "index_bytes": files.get(INDEX_FILE, 0),
        "bytes": sum(files.values()),
        "platform": None,
        "match_date": None,
        "ppp_version": None,
        "n_channels_indexed": None,
        "channel_set": None,
    }
    present = set(files) - {INDEX_FILE}
    row["n_channels_present"] = len(present)
    row["has_telemetry"] = all(c in present for c in TELEMETRY_CHANNELS)
    row["complete"] = False
    try:
        index = json.loads(gzip.decompress((mdir / INDEX_FILE).read_bytes()))
    except (OSError, ValueError, EOFError):
        return row
    indexed = {c["channel"] for c in index.get("channels", [])}
    row.update(
        index_ok=True,
        platform=index.get("platform"),
        match_date=index.get("matchDate"),
        ppp_version=(index.get("context") or {}).get("version"),
        n_channels_indexed=len(indexed),
        channel_set=channel_set_version(len(indexed)),
        complete=bool(indexed) and indexed <= present,
    )
    return row


def match_dirs(root: Path) -> list[Path]:
    return sorted(p for p in (Path(root) / "csds").glob("*/*/*/*") if p.is_dir())


def build_manifest(root: Path, workers: int = 16) -> pd.DataFrame:
    dirs = match_dirs(root)
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(scan_match, dirs))
    df = pd.DataFrame(rows)
    for col in ("index_ok", "complete", "has_telemetry"):
        df[col] = df[col].astype(object)
    return df


def attach_revisions(manifest: pd.DataFrame, assets: pd.DataFrame, *, seed: int, fraction: float) -> pd.DataFrame:
    """Add the ADX revision of each match (from the asset index) and its seeded-sample membership.

    Matches missing from the asset index get null revision fields (never guessed from the folder date).
    """
    from cscoach.data.export import in_sample

    rev = (
        assets.assign(match_id=assets["name"].str.split("/").str[4])
        .drop_duplicates("match_id")
        .set_index("match_id")[["revision_id", "revision_date"]]
        .rename(columns={"revision_date": "adx_revision_date"})
    )
    out = manifest.join(rev, on="match_id")
    out["in_seeded_sample"] = [in_sample(m, seed=seed, fraction=fraction) for m in out["match_id"]]
    return out


def summarize_by_revision_date(manifest: pd.DataFrame) -> pd.DataFrame:
    g = manifest.groupby("revision_date")
    out = pd.DataFrame(
        {
            "n_matches": g.size(),
            "n_complete": g["complete"].sum().astype(int),
            "n_telemetry": g["has_telemetry"].sum().astype(int),
            "n_index_broken": g["index_ok"].apply(lambda s: int((~s.astype(bool)).sum())),
            "n_v30": g["channel_set"].apply(lambda s: int((s == "v30").sum())),
            "n_v42": g["channel_set"].apply(lambda s: int((s == "v42").sum())),
            "n_other_set": g["channel_set"].apply(lambda s: int((s == "other").sum())),
            "ppp_versions": g["ppp_version"].apply(lambda s: ";".join(sorted(s.dropna().unique()))),
            "gb": (g["bytes"].sum() / 1e9).round(3),
        }
    )
    if "revision_id" in manifest:
        out["revision_ids"] = g["revision_id"].apply(lambda s: ";".join(sorted(s.dropna().unique())))
        out["n_seeded_sample"] = g["in_seeded_sample"].sum().astype(int)
        out["n_seeded_complete"] = g.apply(
            lambda d: int((d["in_seeded_sample"] & d["complete"].astype(bool)).sum()), include_groups=False
        )
    return out.reset_index()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, required=True, help="collection root holding csds/YYYY/MM/DD/")
    ap.add_argument("--matches-out", type=Path, required=True, help="per-match parquet (keep next to the data)")
    ap.add_argument("--summary-out", type=Path, required=True, help="per-revision-date CSV (committed)")
    ap.add_argument("--config", type=Path, default=Path("configs/export.yaml"),
                    help="export config (seed/fraction); revisions come from <root>/manifest/adx_assets.parquet")
    args = ap.parse_args(argv)
    manifest = build_manifest(args.root)
    assets_path = args.root / "manifest" / "adx_assets.parquet"
    if assets_path.exists():
        import yaml

        cfg = yaml.safe_load(args.config.read_text())
        assets = pd.read_parquet(assets_path, columns=["name", "revision_id", "revision_date"])
        manifest = attach_revisions(
            manifest, assets, seed=cfg["sample_seed"], fraction=cfg["full_channel_fraction"]
        )
    args.matches_out.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_parquet(args.matches_out, index=False)
    summary = summarize_by_revision_date(manifest)
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary_out, index=False)
    print(
        f"matches={len(manifest)} complete={int(manifest['complete'].astype(bool).sum())} "
        f"revision_dates={len(summary)} gb={manifest['bytes'].sum() / 1e9:.1f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
