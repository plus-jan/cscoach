# M2.2 — Snapshot sampler and as-of join

Data provided by PureSkill.gg. Derived data, CC BY-NC-SA 4.0 (ADR-0008).

## Reproduce
code commit `916a877` · config `configs/snapshots.yaml` (sha256 `297836dbef54…`) ·
`uv run python -m cscoach.data.snapshots --sample 300 --report-dir <dir>`. Scope: 300 random clean seeded
canonical 5v5 matches with reconciled rounds (M2.1), seed 20260928. Per-match output (not committed):
`<root>/derived/snapshots/<match_id>.parquet` (one row per snapshot × known player).

## Method
- Snapshot ticks per round: freeze-end tick (included) to round-end tick (excluded); a 1 s cadence (A-22) plus every
  tick of `player_death`, `player_hurt`, `bomb_state`, `bomb_action`, `bomb_defuse`, `grenade_state`; `source`
  lists why a tick was sampled.
- As-of join: per player, the latest `player_status` row with tick ≤ snapshot tick, same round only.
- **Dead players:** `player_status` has no rows for dead players (the victim's rows stop at the death tick and
  resume 19–20 ticks after the round end with health 100; 10 of 4,648 resumptions happened earlier). Without
  handling this, the last alive row is carried forward. `is_alive` = no `player_death` (same round, tick ≤ t) after
  the player's latest status row; dead players' state columns are masked.
- Players with no status row yet at the snapshot tick get no row (otherwise a future player would be revealed).
- Status columns are read from the per-match index; all 21 configured columns exist in all 300 matches.

## Results
| | |
|---|---|
| snapshots | 703,293 (per match mean 2,344, range 637–4,208); player rows 7,032,765 |
| snapshots sampled because of an event | 36.6 % |
| alive share of player rows | 0.68 (per match 0.59–0.81) |
| staleness of alive rows | median 0, p99 0 ticks; 144 of 4,773,997 alive rows (3.0e-5) > 1 s, 90 > 10 s |
| status from another round (masked) | 0.69 % of rows |
| tick rate | 64 in all matches (read from the header) |
| runtime | 0.39 s per match (load + sample + join), 12 workers |
| **leakage check (DoD)** | **300 / 300 matches**: at 5 random cut ticks per match, truncating every input at the cut leaves all snapshots ≤ cut identical |

Unit tests (synthetic, A-33) cover the window, cadence, event sources, as-of semantics, dead players,
late-joining players and the truncation property at 9 cut points.
