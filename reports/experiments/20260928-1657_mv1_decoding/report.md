# MV.1 — Game rules and decoding on CSDS

Data provided by PureSkill.gg. Derived data, CC BY-NC-SA 4.0 (ADR-0008). Verification experiment (no loop).

## Reproduce
- sample: 400 clean seeded canonical 5v5 matches with reconciled rounds, 200 per channel set (`configs/mv1.yaml`,
  seed 20260928); builds 10521–10924; ADX dataset `f49be2ef387af522a7b6f000158113e0`.
- `uv run python -m cscoach.data.rounds …` (decided_tick), then `uv run python -m cscoach.verify.mv1 --out <root>/derived/mv1`,
  `uv run python -m cscoach.verify.economy --mv1-dir <root>/derived/mv1`, `uv run python analyze.py <root>/derived/mv1 summary.json`.
- code: collectors at `49eb4c4` (+ this change set); every number below is in `summary.json`.

## Results
Decoding tables: `docs/data/csds_decoding.md`.

| topic | result |
|---|---|
| sides | `team_code`/`winner_team_code` 2 = T, 3 = CT; swaps at 13, 28, 34, 40 |
| win reasons (v42) | 1 bombed, 7 defused, 8 CT elimination, 9 T elimination, 11/13 hostages, 12 time, 17 surrender; v30 only 8/9 |
| round-end tick | v42 exact (`round_officially_ended` +448/544 ticks); **v30 +6.7 s late** (official − end = 19/20 ticks) → `decided_tick` |
| sites | `site_code` unstable (entity index); planter `place_name` resolves 3,961/3,962 plants |
| hit boxes | Source hit groups 0–8 (head: 12,462/12,465 v42 killing hits are headshots); v30 1.2 % garbage codes |
| weapons | item definition index; 64 codes, identical names in v30 and v42 |
| timers | round 115.0 s; **bomb 41.0 s** (585/585); **freeze 15 s (124 matches) or 20 s (275)** |
| economy | loss counter −2 per win (96.7 % of team-rounds vs 79.1 % for −1); T plant bonus **600**; **CT +50 per T killed**; OT start **10,000**; Zeus **100**, CZ75 **300** |
| money reconciliation | exact 86.4 % (v30) / 87.4 % (v42) of player-rounds; 96.2 % / 97.1 % with one personal credit |
| ticks | 64 Hz in 400/400; coverage ≥ 99.4 %; max gap 7 ticks; `second` exact; merged positions exact 99.6 %, ≤ 1 tick |

## Effect on the pipeline
- `rounds.decided_tick`; snapshots end there (300-match sample: 703,293 → 649,588 rows; negative `time_remaining_s`
  0.63 % → 0.07 %; leakage check 300/300; round reconciliation unchanged at 99.887 %).
- `bomb_timer_s` 41; bomb site from `place_name` (to be wired into the features).

## Assumptions
A-13 refuted → A-45 (corrected economy, open until ≥ 99 %); A-14 refuted → A-44 (measured timers, supported);
A-15 supported; A-16 supported; A-39 open (fixes documented; bias of v42-only features untested).
