#!/usr/bin/env bash
# Rebuild every derived table after new CSDS data arrived (e.g. a full-channel top-up), in dependency order.
# The raw collection (csds/) is only read; manifests, tomes and derived/ are rebuilt. Each step writes its report
# under reports/experiments/<timestamp>_<step>_refresh/ with the code commit and config hash.
#
#   scripts/refresh_data.sh            # all steps
#   STEPS="features audit" scripts/refresh_data.sh   # a subset (names below)
#
# Run from a clean working tree so the recorded commit describes the code that produced the reports.
set -euo pipefail
cd "$(dirname "$0")/.."

ROOT=$(python3 -c "import yaml;print(yaml.safe_load(open('configs/export.yaml'))['root'])")
TS=$(date +%Y%m%d-%H%M)
COMMIT=$(git rev-parse --short HEAD)
[[ -z "$(git status --porcelain)" ]] || echo "WARNING: working tree not clean; reports will cite $COMMIT" >&2
STEPS=${STEPS:-"plan manifest quality tiers volume rounds snapshots features audit"}

meta() {  # $1 = config path
  local h; h=$(sha256sum "$1" | cut -c1-12)
  printf '{"commit": "%s", "config": "%s", "config_sha256_12": "%s", "refresh": "%s"}' "$COMMIT" "$1" "$h" "$TS"
}
run() { echo "== $1 ($(date +%T))"; }

for step in $STEPS; do
  case $step in
    plan)       run plan;      uv run python -m cscoach.data.export plan ;;  # must report 0 assets left
    manifest)   run manifest;  uv run python -m cscoach.data.manifest --root "$ROOT" \
                  --matches-out "$ROOT/manifest/matches.parquet" \
                  --summary-out reports/data/export_manifest_by_revision_date.csv ;;
    quality)    run quality;   uv run python -m cscoach.data.quality \
                  --report-dir "reports/experiments/${TS}_m1.3_header_quality_refresh" --meta "$(meta configs/quality.yaml)" ;;
    tiers)      run tiers;     uv run python -m cscoach.data.tiers \
                  --report-dir "reports/experiments/${TS}_m1.4_tiers_refresh" --meta "$(meta configs/tiers.yaml)" ;;
    volume)     run volume;    uv run python -m cscoach.data.volume \
                  --report-dir "reports/experiments/${TS}_m1.5_volume_refresh" --meta "$(meta configs/volume.yaml)" ;;
    rounds)     run rounds;    uv run python -m cscoach.data.rounds \
                  --report-dir "reports/experiments/${TS}_m2.1_rounds_refresh" --meta "$(meta configs/rounds.yaml)" ;;
    snapshots)  run snapshots; uv run python -m cscoach.data.snapshots --sample 0 \
                  --report-dir "reports/experiments/${TS}_m2.2_snapshots_refresh" --meta "$(meta configs/snapshots.yaml)" ;;
    features)   run features;  uv run python -m cscoach.data.features ;;
    audit)      run audit;     uv run python -m cscoach.verify.leakage_audit \
                  --report-dir "reports/experiments/${TS}_m2.4_leakage_audit_refresh" --meta "$(meta configs/leakage_audit.yaml)" ;;
    *) echo "unknown step: $step" >&2; exit 2 ;;
  esac
done
echo "== done ($(date +%T)); reports: reports/experiments/${TS}_*_refresh/"
