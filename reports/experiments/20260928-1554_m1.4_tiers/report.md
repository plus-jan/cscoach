# M1.4 — Rank decoding and match tiers

Data provided by PureSkill.gg. Derived data, CC BY-NC-SA 4.0 (ADR-0008).

## Reproduce
- code commit `eb4a10e` · config `configs/tiers.yaml` (sha256 `826aec6dd9f3…`) ·
  `uv run python -m cscoach.data.tiers --report-dir <dir>`, then `uv run python validate.py validation.json`
- CSDS: ADX dataset `f49be2ef387af522a7b6f000158113e0`, 363 live revisions 2025-09-01 … 2026-09-27; channel
  `player_info` of the 8,648 canonical matches with all channels (header-only matches have no per-player ranks;
  `header.*_starters_avg_rank` averages unranked players as 0 and is not used).
- Per-match output (not committed): `<root>/manifest/match_tiers.parquet`.

## Decoding (A-15, rank fields only)
| platform | `rank_type` | field | scale |
|---|---|---|---|
| steam 5v5 | 11 | `rank` | Premier rating (observed 1,206–30,763) |
| steam 5v5 | 12 | `rank` | Competitive skill group 1–18 |
| steam wingman | 7 | `rank` | Wingman skill group (no tier: out of scope) |
| faceit | −1 | `rank_platform` | FACEIT level 1–10 (`elo_platform` in v42 matches agrees) |
| any | – | 0 | unknown → null |

`rank_type` is null in v30 matches (91–97% of rows). Type-free rule: Premier iff any rank ≥ 19, else Competitive.
Check on v42 Steam 5v5 matches that carry `rank_type`: **2,079 / 2,079 agree** among matches with any known rank;
the 66 disagreements all have no known rank (tier null either way). Ranks are constant within a match for
99.96% of players; one scale per match in all checked matches.

## Coverage (canonical 5v5, **seeded sample** — the legacy download is 100% de_mirage, F-03)
| platform | source | low | mid | high | semipro | null | total |
|---|---|---|---|---|---|---|---|
| faceit | faceit | 18 | 84 | 84 | 46 | 13 | 245 |
| steam | competitive | 578 | 292 | 31 | 0 | 508 | 1,409 |
| steam | premier | 1,110 | 372 | 316 | 164 | 543 | 2,505 |
| unknown | – | 0 | 0 | 0 | 0 | 17 | 17 |
| **all** | | **1,706** | **748** | **431** | **210** | **1,081** | **4,176** |

All full-channel canonical matches (incl. legacy): `tier_coverage.csv`, `summary.json`.

## Validation (`validation.json`, seeded sample, match-level bootstrap 2,000, 95% CI)
- **A-12 missingness is not random:** tier null for competitive 0.361 [0.335, 0.385], premier 0.217 [0.200, 0.233],
  faceit 0.053 [0.025, 0.082]; by map 0.20–0.36 (de_anubis highest). Excluding untiered matches shifts the source mix.
- **A-12 spread:** 0.175 [0.162, 0.189] of labelled lobbies span ≥ 2 tiers (premier 0.181, faceit 0.207, competitive 0.155).
- **A-11 cut-offs:** competitive skill groups give no semipro and 64% low; premier 57% low → cut-offs are uneven
  across scales (MV.2 revises them).
- **A-40 by tier:** exclusion 0.039–0.056 across known tiers (overlapping CIs), 0.077 [0.062, 0.093] for untiered;
  incomplete low 0.051 [0.041, 0.062] vs high 0.026 [0.012, 0.042].
- **A-32:** semipro has 210 seeded matches (< 300 target); high 431.

## Gate verdicts
Not a model; no gates apply. Unknown ranks stay null; nothing is guessed.
