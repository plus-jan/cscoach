# 02 — Derived data contracts (built from CSDS)

Source channels and quirks: `docs/data/README.md` and `docs/data/csds_spec.md`. Every derived table
states its **CSDS source columns**. Anything not derivable from CSDS is out of scope (ADR-0003).

Conventions:
- keys `match_id` (from the tome/manifest `id`), `round` (CSDS numbering), `tick`;
- `round_uid = f"{match_id}:{round}"`;
- `side ∈ {CT, T}`, mapped from `team_code` (mapping verified in MV.1, A-15);
- `player_key = f"{match_id}:{player_id_fixed}"`, meaningful **within one match only** (ADR-0005);
- time in seconds from CSDS `second`.

## match_manifest (one row per match, from the header tome)
| column | source | notes |
|---|---|---|
| match_id | tome `id` | primary key |
| revision_date | ADX revision | export bookkeeping |
| map_name, build_num, tick_rate, match_date | `header` | `build_num` = game build for drift/rules |
| platform, match_type, providence, is_wingman | `header` | exclude wingman; `providence=user` ⇒ date = upload date |
| ct/t_starters_avg_rank | `header` | coarse match-level skill |
| tier, tier_source | derived (docs/specs/03 §Tiers) | null if unknown — never guessed |
| channel_set | index object | `v30` / `v42` |
| dedup_key, dup_n, is_canonical | hash of map, server, `number_of_points`, final scores (no date) | duplicates are **flagged**, one canonical copy per group; the raw collection is never modified (M1.3) |
| format, final_state, final_state_source | `is_wingman` / `unique_steamids`; last `round_state` scores (header scores only where channels are missing, F-02) | A-43 |
| clean | derived | canonical 5v5 without data defects (abandonment is a stratum, not a defect) |
| quality_flags | derived | missing ticks, missing round_end, warmup leftovers, **abandonment** (`player_disconnect` without reconnect → 4v5 phases with money compensation [xenopoulos_pro_vs_amateur_wp]), … |

## rounds
match_id, round, start_tick (`round_start`; round 1: first `round_state` tick), freeze_end_tick
(`round_state` `round_freeze_end`), end_tick (`round_end.tick`), winner_side (`round_end.winner_team_code`,
2 = T / 3 = CT, with the v30 half-start fix, F-05), winner_team (`start_ct`/`start_t`), win_reason_code (full
only in v42; mapping in MV.1), side_start_ct and side_swap_before (from `player_info.team_code`), is_overtime
(`pop_overtime`, round > 24), is_warmup (`round_state`), ct_score_before / t_score_before and
start_ct_score_before / start_t_score_before (reconstructed from winners; `round_state` scores are only a
check because their convention differs by parser). Built by `cscoach.data.rounds`.

## snapshots → state_features
One row per (match_id, round, tick). Ticks are chosen by the sampler (docs/specs/03, cadence A-22):
event ticks (`player_death`, `player_hurt`, `bomb_*`, `grenade_state`) plus a fixed cadence between
freeze end and round end (end tick excluded).

Built by `cscoach.data.snapshots` (M2.2): one row per snapshot × known player with the latest `player_status`
row ≤ tick (same round) and `is_alive` from `player_death` — `player_status` has no rows for dead players, so a
plain as-of join would keep them alive (F-06); dead players' state columns are masked. Players without a status
row in the current round (not yet seen, or gone after a disconnect) get no row. Sides: `player_info.team_code`,
filled from `player_spawn` only where `player_info` lacks the player (F-06 addendum). Built by
`cscoach.data.features` (v1: `primaries` instead of weapon classes; `bomb_site` A/B from the planter's `place_name`
at the plant, since `site_code` is not a stable site id — MV.1).

Features are aggregated per side from `player_status` at the latest tick ≤ snapshot tick:
- `alive` (health > 0), `hp_sum` (`health`), `armor_sum` (`armor`), `helmets` (`has_helmet`),
  `kits` (`has_defuser`, CT);
- `equip_value` (`current_equipment_cost` / `equipment_value_calc`);
- weapon class counts (`inv_primary`, `inv_secondary`) and utility counts (`inv_*grenade`, `inv_flashbang`, `inv_molotov`, `inv_incgrenade`);
- `money` (post-buy float);
- bomb: `bomb_planted`, `bomb_site` (planter's `place_name` at the plant), and the plant time (`bomb_state` `bomb_planted`);
- time: `time_remaining_s` (round clock pre-plant, bomb clock post-plant; timers from `tick` phases, A-14);
- context: `man_advantage`, `tier`, `platform`, `map_name`, `build_num`.
- rank prior (M3.2, A-48): `ct_rank_alive`, `t_rank_alive` = mean tier-unit rank of the side's alive players from
  `player_info` of the snapshot's round (`rank` for Premier/skill groups, `rank_platform` for FACEIT levels; 0 =
  unknown) on the match's rank scale (M1.4 `tier_source`); missing unless ≥ `rank_min_known_share` of the alive
  players are ranked; `rank_diff_alive` = CT − T.

The label `y_ct_win` (from `rounds.winner_side`) is attached only in the modelling table.
Groups: `match_id` (split) and `round_uid` (cluster).

## duels
duel_id, match_id, round, tick_start, p1, p2 (p1 = peeker if determinable), outcome `y_p1_wins`, resolved_tick.
The definition is in docs/specs/03#xk (A-19). Pre-duel features come from `player_vector`
(positions, `phi_ang`/`theta_ang`, `ang_vel`, `speed_2d`, `movement_angle`, `inaccuracy`,
`recoil_index`, `weapon_code`, `is_ducked`), `player_inputs` (button timeline → counter-strafe),
`player_status` (`health`, `armor`, `flash_duration`, `is_scoped`, `is_walking`, `is_spotted`),
`player_blind`, `grenade_state` (smokes).

## buys (per player-round, at freeze end)
money_start, `freezetime_end_equipment_cost`, `round_start_equipment_cost`, item purchases/refunds/drops
(`item_pickup`, `item_refund`, `item_dropped`), buy_class (A-21), team buy_class, deviation flag.

## utility_events
Grenade throw/detonate/expire (`grenade_state`, `molotov_state`), trajectories (`grenade_vector`,
`grenade_bounce`), fire area (`molotov_fire`), flashed players (`player_blind`), damage (`player_hurt`
with grenade weapons). Placement area via `place_name` of the nearest player position, or position binning.

## area_graph (per map, empirical — no external nav mesh)
Nodes are areas (`player_status.place_name`, optionally refined by position clustering). Edges are
observed transitions between consecutive ticks of alive players (`player_vector`). Weights: median
transit time. Built from training matches only (A-37).

## event_values
event_id, match_id, round, tick, event_type, actor (`player_key`), team_side, wp_before, wp_after, wpa,
credit {player_key: value}.

## feedback_items
item_id, match_id, player_key, round, tick, category, evidence (json with CSDS row references),
wpa_at_stake, ci_low, ci_high, confidence, priority, text, build_num.

## Leakage denylist (never features)
`round_end.*`, `winner_side`, `end_reason`, `end_tick`, final/after-round scores
(`header.*_score_final`, `round_state` scores after the round), `rank_update` rows at or after the
snapshot, any row with tick > snapshot tick, `y_*` labels, `wp_after`, `wpa`.
