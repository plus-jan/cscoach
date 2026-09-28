# M2.1 — Round reconstruction

Data provided by PureSkill.gg. Derived data, CC BY-NC-SA 4.0 (ADR-0008).

## Reproduce
code commit `70e5c05` · config `configs/rounds.yaml` (sha256 `12c64a686861…`) ·
`uv run python -m cscoach.data.rounds --report-dir <dir>`. Input: canonical 5v5 matches with all channels
(7,984; before the M1.5 top-up), channels `round_end`, `round_state`, `round_start`, `player_info` via
`GameDsLoader`; `is_overtime` via `pureskillgg_csgo_dsdk.pop_overtime(max_rounds_csgo=24)`.
Outputs (per match, not committed): `<root>/derived/rounds/<match_id>.parquet`; check table
`<root>/manifest/rounds_check.parquet`.

## Decoding (A-15)
- `team_code` and `winner_team_code`: 2 = T, 3 = CT (`win_reason_message` agrees in every row inspected).
- Sides per round from `player_info.team_code`; observed swaps at 13 and, in overtime, 28, 34, 40 (the first
  overtime half keeps the second-half sides). No schedule is hard-coded.
- **v30 parser defect:** the winner side is stale in the first round of every half — after each side swap and
  at each overtime-block start (25, 31, …). Round 13 disagreed with `round_state` in 322/322 sampled v30 matches,
  rounds 14–24 agreed 100 %. v42 is correct. Candidate rules were compared on all v30 overtime/draw matches and
  300 regulation matches: flipping at swaps only reconciled 0 % of overtime matches, flipping at swaps +
  overtime-block starts reconciled 100 % of overtime, draw and regulation matches.
- `round_state` score conventions differ by parser (v42: per side, swapped on display at halftime; v30: not a
  simple per-team or per-side count), so they are used only as the final-score check.
- `win_reason_code`: v30 carries only 8/9 (the winner side); v42 carries 1, 7, 8, 9, 11, 12, 13 (decoding in MV.1).
  Round end reasons (bomb vs. elimination vs. time) are therefore not available from `round_end` for v30.

## DoD check
Adjusted DoD (the header loser score is wrong in 48 % of matches, F-02): the reconstructed final team scores
must equal the last `round_state` scores **and** the header winner score.

| | matches | pass |
|---|---|---|
| all | 7,984 | **99.887 %** (≥ 99.5 % ✓) |
| seeded sample | – | 99.880 % |
| v30 / v42 | 6,335 / 1,649 | 99.921 % / 99.757 % |
| regulation / overtime / draw / incomplete | 7,087 / 410 / 296 / 191 | 99.90 % / 100 % / 100 % / 98.95 % |

Failures (9): 4 round-count mismatches (already `q_rounds_vs_score` in M1.3); 3 v42 13–0 matches with
abandonment (side detection in the last round); 2 others. 162,102 rounds, 2,822 in overtime.
