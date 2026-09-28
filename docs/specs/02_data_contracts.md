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
| dedup_key | hash of header values | used to drop duplicates |
| quality_flags | derived | missing ticks, missing round_end, warmup leftovers, … |

## rounds
match_id, round, start_tick (`round_start`/`round_state`), freeze_end_tick (phase change in
`round_state`/`tick`), end_tick (`round_end.tick`), winner_side (`round_end.winner_team_code`),
end_reason (`win_reason_code`, mapped in MV.1), is_overtime (round > 24), is_warmup (`round_state`),
ct_score_before / t_score_before (`round_state`, fixed values).

## snapshots → state_features
One row per (match_id, round, tick). Ticks are chosen by the sampler (docs/specs/03, cadence A-22):
event ticks (`player_death`, `player_hurt`, `bomb_*`, `grenade_state`) plus a fixed cadence between
freeze end and round end (end tick excluded).

Features are aggregated per side from `player_status` at the latest tick ≤ snapshot tick:
- `alive` (health > 0), `hp_sum` (`health`), `armor_sum` (`armor`), `helmets` (`has_helmet`),
  `kits` (`has_defuser`, CT);
- `equip_value` (`current_equipment_cost` / `equipment_value_calc`);
- weapon class counts (`inv_primary`, `inv_secondary`) and utility counts (`inv_*grenade`, `inv_flashbang`, `inv_molotov`, `inv_incgrenade`);
- `money` (post-buy float);
- bomb: `bomb_planted`, `bomb_site`, and the plant time (`bomb_state` `bomb_planted` + `site_code`);
- time: `time_remaining_s` (round clock pre-plant, bomb clock post-plant; timers from `tick` phases, A-14);
- context: `man_advantage`, `tier`, `platform`, `map_name`, `build_num`.

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
