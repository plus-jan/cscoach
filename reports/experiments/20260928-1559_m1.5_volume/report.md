# M1.5 — Data volume check (gap analysis per stratum)

Data provided by PureSkill.gg. Derived data, CC BY-NC-SA 4.0 (ADR-0008).

## Reproduce
code commit `a67a12a` · config `configs/volume.yaml` (sha256 `3806765b0027…`) + `configs/export.yaml` ·
`uv run python -m cscoach.data.volume --report-dir <dir>`. Inputs: `<root>/manifest/match_quality.parquet`
(M1.3), `match_tiers.parquet` (M1.4), `adx_assets.parquet` (M1.2). Scope: **clean canonical 5v5 matches of
the seeded full-channel sample** (fraction 0.15, seed 20260928; the legacy download is excluded, F-01/F-03).

## Targets (docs/specs/06)
≥ 2,000 matches; ≥ 300 matches per tier × platform bucket; ≥ 5 maps (A-32); ≥ 500 test rounds per stratum
(A-07) with a 20% test split (A-28) ⇒ ≥ 2,500 rounds per stratum.

## Now (fraction 0.15)
- 3,930 matches (2,932 with a tier) ✓ · 5 maps with ≥ 300 (ancient, dust2, inferno, mirage, nuke) ✓
- tier × platform (matches / rounds): steam low 1,596 / 32,668 ✓ · mid 638 / 13,267 ✓ · high 333 / 6,976 ✓ ·
  **semipro 157 / 3,386 ✗ (needs f ≈ 0.29)** · faceit low 14 ✗ · mid 71 ✗ (0.63) · high 81 ✗ (0.56) ·
  semipro 42 ✗ (unreachable at f = 1: ≈ 280) · untiered: steam 987, faceit 11.
- By scale: competitive high 31 (unreachable: ≈ 207 at f = 1; competitive has no semipro at all).
- Maps: anubis 186 (0.24), overpass 163 (0.28), cache 139 (0.32), vertigo 65 (0.69), train 63 (0.71).

Full tables: `gap_tier.csv`, `gap_tier_platform.csv`, `gap_tier_scale.csv`, `gap_map.csv`.

## Options (exact download size from the ADX asset index; egress $0.09/GB)
| option | new GB | egress | expected result (count × f'/0.15; FACEIT all = ÷0.15) |
|---|---|---|---|
| A: f = 0.35 | 210 | ≈ $19 | steam semipro ≈ 366 ✓; anubis/overpass/cache ✓ (8 maps); FACEIT ✗ |
| **B: f = 0.35 + all FACEIT** | 248 | ≈ $22 | A + faceit high ≈ 540 ✓, mid ≈ 473 ✓, semipro ≈ 280 (≈ target), low ≈ 93 ✗ |
| C: f = 0.5 + all FACEIT | 397 | ≈ $36 | B + vertigo/train ≈ 215/210 (still < 300) |
| D: f = 1.0 | 888 | ≈ $80 | everything available; FACEIT low, competitive high still < 300 |

Structural gaps no download can close: FACEIT low (≈ 93 in the whole corpus), competitive-scale high (≈ 207) and
semipro (0). These need a stratum/target change (A-32, A-11 → MV.2), not more data.

Option B changes the design from a simple random sample to a **platform-stratified** one (inclusion probability
0.35 for Steam/unknown, 1.0 for FACEIT). Models condition on platform anyway; pooled descriptive statistics must
weight by 1/inclusion probability.

Runtime budget (< 30 s per match, A-32) is not measurable yet (no engine); it moves to M3.

## Gate verdicts
Not a model. Volume verdict at f = 0.15: overall ✓, maps ✓, 4 of 10 tier × platform buckets ✓.
