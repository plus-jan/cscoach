# 02 — Data contracts

Canonical tables. The machine-readable version is `src/cscoach/schemas/tables.py`
(`TableSchema` objects + `validate_frame`). Keep both in sync.

Conventions: snake_case; `match_id` = sha256 of demo bytes (first 16 hex chars);
`round_num` starts at 1; `side ∈ {"CT","T"}`; `steamid` as string; ticks int;
positions in game units; `round_time_s` = seconds since freeze-time end.

## manifest
| column | type | notes |
|---|---|---|
| match_id | str | PK |
| source | str | `local`, `pureskill`, `faceit`, `hltv`, ... |
| map_name | str | e.g. `de_mirage` |
| game_build | str | from demo header; required for economy rules & drift |
| tick_rate | float | from header |
| match_date | datetime | UTC, nullable |
| tier | str | canonical tier (configs/tiers.yaml), nullable |
| tier_source | str | how tier was derived |

## rounds
match_id, round_num, freeze_end_tick, end_tick, winner_side, end_reason
(`elimination`, `bomb_exploded`, `bomb_defused`, `time`, ...), ct_team_id, t_team_id,
ct_score_before, t_score_before, is_overtime.

## player_ticks (sampled)
match_id, round_num, tick, steamid, side, x, y, z, yaw, pitch, velocity_xy, health,
armor, has_helmet, has_defuser, is_alive, active_weapon, equipment_value, money,
flash_duration, utility (list/str counts: smoke, flash, he, molotov, decoy).

## events
- `kills`: tick, attacker, victim, assister, flash_assist, weapon, headshot, penetrated,
  thru_smoke, attacker_blind, noscope, trade_of (victim steamid traded, derived)
- `damages`: tick, attacker, victim, weapon, dmg_health, dmg_armor, hitgroup
- `grenades`: tick_thrown, tick_detonate, thrower, type, x, y, z (detonation)
- `bomb`: tick, event (`plant`, `defuse`, `explode`, `begin_defuse`...), site, player

## snapshots / state_features
One row per (match_id, round_num, tick). Label `y_ct_win` (int) attached **only**
in the modelling table, never computed from features. Feature list: see
`configs/model_wp.yaml` and `features/state.py`. Groups: `match_id` (split),
`round_uid = f"{match_id}:{round_num}"` (cluster).

## duels
duel_id, match_id, round_num, tick_start, p1, p2 (p1 = peeker if determinable),
pre-duel features (see 03_models.md#xk), outcome `y_p1_wins` ∈ {0,1}, resolved_tick.

## event_values
event_id, match_id, round_num, tick, event_type, actor, team_side, wp_before,
wp_after, wpa (team perspective), credit (dict steamid → float).

## feedback_items
item_id, match_id, steamid, round_num, tick, category, evidence (json), wpa_at_stake,
ci_low, ci_high, confidence, priority, text.
