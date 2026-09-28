# M1.3 — Header tome, dedup, quality flags

Data provided by PureSkill.gg. Derived data, CC BY-NC-SA 4.0 (ADR-0008).

## Reproduce
- code commit `fbf274f` · config `configs/quality.yaml` (sha256 `429cd3110eb0…`) · `uv run python -m cscoach.data.quality --report-dir <dir>`, then `uv run python validate.py validation.json`
- CSDS: ADX dataset `f49be2ef387af522a7b6f000158113e0`, 363 live revisions 2025-09-01 … 2026-09-27; header tome
  `header.2025-09-01,2026-09-28.full` (rebuilt 2026-09-28, 32,498 rows); channel sets v30 + v42.
- Outputs outside the repo (per-match, not committed): `<root>/manifest/match_quality.parquet`; subheader tomes
  under `<root>/tomes/tome/csds/subheader.2025-09-01,2026-09-28.*`. Raw `csds/` was only read.

## Counts
| | matches |
|---|---|
| all header rows | 32,498 |
| duplicate groups (≥ 2 copies) / non-canonical copies | 647 / 719 |
| canonical | 31,779 (5v5 27,655 · wingman 4,124) |
| final state, canonical | regulation 27,142 · incomplete 1,987 · draw 1,692 · overtime 958 |
| final state source | round_state 8,648 · header 23,131 |
| channel-checked (all channels) | 8,676 |
| **clean** (canonical 5v5, no data defect) | **25,434** (steam 24,056 · faceit 1,378; v30 20,984 · v42 4,450) |
| clean ∩ seeded full-channel sample | 3,930 |

Flags (all rows): platform unknown 131 · upload date (providence=user) 279 · player count 420 · incomplete
2,033 · no round_end 0 · round_end count ≠ round_state score 4 · warmup after start 0 · tick gap > 1 s 0
(max observed 0.109 s) · abandonment 1,344 (+ 624 matches with a disconnect whose player id is unknown,
not flagged) · header loser score ≠ round_state 4,200 of 8,676.

Per platform × map × month × channel set: `counts_platform_map_month_channelset.csv` (350 cells, 118 with
≥ 30 clean matches).

## Validation (`validation.json`)
- **A-36 (dedup precision):** 28 of 28 duplicate groups with ≥ 2 full-channel copies have identical
  `round_end` sequences (round, tick, win reason). Recall (same match, different `number_of_points`) is not measured.
- **A-40 (exclusion bias), canonical 5v5, match-level bootstrap (2,000), 95% CI:** excluded overall 0.080
  [0.077, 0.083]; by map 0.073–0.087 with overlapping CIs; by platform **faceit 0.156 [0.139, 0.175] vs
  steam 0.071 [0.068, 0.074]** (unknown 1.0 by definition). Excluding flagged matches changes the platform
  mix; it does not change the map mix. Tiers: not yet available (M1.4).
- Abandonment flag precision: in 40 sampled flagged v42 matches, 11 involved a disconnect with unknown
  player id (now not flagged) and 10 had a later human connect under another id → the flag is an upper
  bound; MV.1 validates it.

## Gate verdicts
Not a model; no gates apply. Data-quality verdicts: no tick gaps, no missing round_end, no warmup
leftovers after the first round end; header final scores are **not** usable for the losing side.
