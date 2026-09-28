<!--
Vendored copy of the official CSDS Spec from https://github.com/pureskillgg/docs
(docs/datascience/adx/cs2/csds/spec.md, branch master, fetched 2026-09-28).
Copyright (c) FPS Critic, Inc. — MIT License. Documentation only; the DATA is CC BY-NC-SA 4.0 (DSA).
Do not edit; re-fetch to update. Relative links below point to the upstream site.
-->

# CSDS Spec

Documentation for CSDS channels built by FPS Critic, Inc.

One match is published as a JSON index object named `csds` plus one file per
channel, 42 in all, for 43 objects per match. The index lists the channels,
where each one sits, and what columns it declares. Every channel file is
[Apache Parquet], `header` included.

This document describes the channel set published since 2026-08-04. Revisions
through 2026-07-31 carry an older set of 30 channels, described in the
[archived spec](/datascience/old/cs2/csds/spec); the 2026-08-02 revision holds
a mix of the two. Reading each match's index object rather than assuming a
channel list will keep code working across the change.

## How to read this

Each section below is one channel. The heading gives the channel name and its
category, and multi-event channels list the game events that write rows into
them.

**Origin** says where a column comes from:

| Origin                | Meaning                                                                                             |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| `replay`              | Written by the demo parser, straight off the game's own event stream.                               |
| `replay_fixed`        | A parser value the pipeline recomputed. The uncorrected value stays in the matching `*_raw` column. |
| `replay-capped`       | A parser value clamped at the top, so an unusually high number cannot single a player out.          |
| `replay-redacted`     | A parser value overwritten by the PII scrubber.                                                     |
| `calculated`          | Derived by the pipeline from the columns named under Dependents.                                    |
| `calculated-redacted` | Derived, then overwritten by the PII scrubber.                                                      |
| `merged`              | Copied in from another channel by joining on the columns named under Merge Keys.                    |

Redaction is not one operation, and the redacted columns are still there. Names
and chat text become the literal string `redacted`, `player_personal.steam_id`
becomes a per-match alias (`A`, `B`, `C` and so on) that means nothing outside
its own match, and `player_status.ping` becomes `0`. The rows are untouched, so
`player_chat` still tells you that somebody typed in a given round, without
telling you what they typed. There is no voice data anywhere in the data set.
The [data dictionary](./assets/csds_dictionary.csv) says which treatment each
column got.

**Dependents** names the columns a calculated column is computed from. A
`channel:column` entry points at another channel, and a `meta:` or `metademo:`
entry at match metadata rather than a channel.

**Merge Keys** names the columns joined on to bring a merged column in. Most
position and velocity columns arrive by an as-of merge against the nearest tick
at or before the event, so they are null when no source row is close enough.

**Type** is the value type as published. Integers are written as Parquet
`int64` and floats as `double`, because the writer goes through pandas; a
column typed `int` here that can hold nulls therefore arrives as a double, and
the note in the [data dictionary](./assets/csds_dictionary.csv) says so.

**Nullable** is the value declared in the index object where there is one.
Merged columns are always nullable. It is left blank for calculated columns,
which the index does not declare either way.

Four columns that older versions of this document listed are no longer
published: `tick` and `second` on `player_info` and on `player_personal`. The
index still names them, marked as deleted, so a reader driven off the index
should skip any column whose origin ends in `-deleted`.

[apache parquet]: https://parquet.apache.org/

## bomb_action - multi_event

Events that trigger this channel: bomb_abort_plant, bomb_begin_plant, bomb_dropped, bomb_pickup, player_given_c4

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| event_type         | string  | False    | replay     |                 |                            |
| player_id          | int32   | True     | replay     |                 |                            |
| player_id_pawn     | int     | True     | replay     |                 |                            |
| site_code          | int32   | True     | replay     |                 |                            |
| entity_id          | int32   | True     | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## bomb_defuse - multi_event

Events that trigger this channel: bomb_abort_defuse, bomb_begin_defuse

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| event_type         | string  | False    | replay     |                 |                            |
| player_id          | int32   | False    | replay     |                 |                            |
| has_kit            | bool    | True     | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | int     | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## bomb_state - multi_event

Events that trigger this channel: bomb_defused, bomb_exploded, bomb_planted

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| event_type         | string  | False    | replay     |                 |                            |
| player_id          | int32   | False    | replay     |                 |                            |
| site_code          | int32   | True     | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | int     | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## bot_takeover - single_event

Event that triggers this channel: bot_takeover

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| player_id          | int32   | False    | replay     |                 |                            |
| player_index       | int32   | False    | replay     |                 |                            |
| bot_id             | int32   | True     | replay     |                 |                            |
| is_controlling     | bool    | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | int     | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## bullet_damage - single_event

Event that triggers this channel: bullet_damage

| Col Name             | Type    | Nullable | Origin     | Dependents      | Merge Keys                   |
| -------------------- | ------- | -------- | ---------- | --------------- | ---------------------------- |
| round                | int     | False    | replay     |                 |                              |
| tick                 | int     | False    | replay     |                 |                              |
| player_id            | int     | False    | replay     |                 |                              |
| attacker_id          | int     | False    | replay     |                 |                              |
| distance             | float32 | False    | replay     |                 |                              |
| damage_dir_x         | float32 | False    | replay     |                 |                              |
| damage_dir_y         | float32 | False    | replay     |                 |                              |
| damage_dir_z         | float32 | False    | replay     |                 |                              |
| num_penetrations     | int32   | False    | replay     |                 |                              |
| is_no_scope          | bool    | False    | replay     |                 |                              |
| is_attacker_in_air   | bool    | False    | replay     |                 |                              |
| second               | float64 |          | calculated | tick, tick_rate |                              |
| player_id_fixed      | float64 | True     | merged     |                 | player_id, round, steam_id   |
| attacker_id_fixed    | int     | True     | merged     |                 | attacker_id, round, steam_id |
| player_x_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_y_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_z_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_x_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_y_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_z_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_phi_ang       | float64 | True     | merged     |                 | player_id, tick              |
| player_theta_ang     | float64 | True     | merged     |                 | player_id, tick              |
| player_weapon_code   | int     | True     | merged     |                 | player_id, tick              |
| player_team_code     | int     | True     | merged     |                 | player_id, tick              |
| attacker_x_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_y_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_z_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_x_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_y_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_z_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_phi_ang     | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_theta_ang   | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_weapon_code | int     | True     | merged     |                 | attacker_id, tick            |
| attacker_team_code   | int     | True     | merged     |                 | attacker_id, tick            |

## grenade_bounce - single_event

Event that triggers this channel: grenade_bounce

| Col Name        | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| --------------- | ------- | -------- | ---------- | --------------- | -------------------------- |
| round           | int     | False    | replay     |                 |                            |
| tick            | int     | False    | replay     |                 |                            |
| entity_id       | int32   | False    | replay     |                 |                            |
| player_id       | int     | False    | replay     |                 |                            |
| bounce_nr       | int32   | False    | replay     |                 |                            |
| x_pos           | float64 | False    | replay     |                 |                            |
| y_pos           | float64 | False    | replay     |                 |                            |
| z_pos           | float64 | False    | replay     |                 |                            |
| second          | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed | float64 | True     | merged     |                 | player_id, round, steam_id |

## grenade_state - multi_event

Events that trigger this channel: decoy_detonate, decoy_firing, decoy_started, flashbang_detonate, hegrenade_detonate, smokegrenade_detonate, smokegrenade_expired

| Col Name           | Type    | Nullable | Origin     | Dependents                          | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | ----------------------------------- | -------------------------- |
| round              | int     | False    | replay     |                                     |                            |
| tick               | int     | False    | replay     |                                     |                            |
| event_type         | string  | False    | replay     |                                     |                            |
| entity_id          | int32   | False    | replay     |                                     |                            |
| player_id          | int32   | False    | replay     |                                     |                            |
| x_pos              | float32 | False    | replay     |                                     |                            |
| y_pos              | float32 | False    | replay     |                                     |                            |
| z_pos              | float32 | False    | replay     |                                     |                            |
| second             | float64 |          | calculated | tick, tick_rate                     |                            |
| player_id_fixed    | float64 | True     | merged     |                                     | player_id, round, steam_id |
| entity_id_fixed    | int     |          | calculated | round, entity_id, event_type, tick  |                            |
| tick_throw         | int     |          | calculated | round, player_id, weapon_name, tick |                            |
| player_x_pos       | float64 | True     | merged     |                                     | tick_throw, player_id      |
| player_y_pos       | float64 | True     | merged     |                                     | tick_throw, player_id      |
| player_z_pos       | float64 | True     | merged     |                                     | tick_throw, player_id      |
| player_x_vel       | float64 | True     | merged     |                                     | tick_throw, player_id      |
| player_y_vel       | float64 | True     | merged     |                                     | tick_throw, player_id      |
| player_z_vel       | float64 | True     | merged     |                                     | tick_throw, player_id      |
| player_phi_ang     | float64 | True     | merged     |                                     | tick_throw, player_id      |
| player_theta_ang   | float64 | True     | merged     |                                     | tick_throw, player_id      |
| player_weapon_code | int     | True     | merged     |                                     | tick_throw, player_id      |
| player_team_code   | int     | True     | merged     |                                     | tick_throw, player_id      |

## grenade_vector - telemetry

Event that triggers this channel: tick_end

| Col Name          | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ----------------- | ------- | -------- | ---------- | --------------- | -------------------------- |
| round             | int     | False    | replay     |                 |                            |
| tick              | int     | False    | replay     |                 |                            |
| entity_id         | int32   | False    | replay     |                 |                            |
| player_id         | int     | False    | replay     |                 |                            |
| grenade_type_code | int32   | False    | replay     |                 |                            |
| grenade_type      | string  | False    | replay     |                 |                            |
| x_pos             | float64 | False    | replay     |                 |                            |
| y_pos             | float64 | False    | replay     |                 |                            |
| z_pos             | float64 | False    | replay     |                 |                            |
| second            | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed   | float64 | True     | merged     |                 | player_id, round, steam_id |

## header - header

| Col Name                   | Type    | Nullable | Origin              | Dependents                               | Merge Keys |
| -------------------------- | ------- | -------- | ------------------- | ---------------------------------------- | ---------- |
| magic                      | string  | False    | replay              |                                          |            |
| network_protocol           | int32   | False    | replay              |                                          |            |
| server_name                | string  | False    | replay              |                                          |            |
| client_name                | string  | False    | replay              |                                          |            |
| map_name                   | string  | False    | replay              |                                          |            |
| game_directory             | string  | False    | replay              |                                          |            |
| fullpackets_version        | int     | False    | replay              |                                          |            |
| allow_clientside_entities  | bool    | False    | replay              |                                          |            |
| allow_clientside_particles | bool    | False    | replay              |                                          |            |
| addons                     | string  | False    | replay              |                                          |            |
| demo_version_name          | string  | False    | replay              |                                          |            |
| demo_version_guid          | string  | False    | replay              |                                          |            |
| build_num                  | int32   | False    | replay              |                                          |            |
| game                       | string  | False    | calculated          | meta:game                                |            |
| is_gotv_recording          | bool    | False    | replay              |                                          |            |
| is_wingman                 | bool    | False    | replay              |                                          |            |
| max_unique_players         | int     | False    | replay              |                                          |            |
| tick_rate                  | int     |          | calculated          |                                          |            |
| tick_save_rate             | int     |          | calculated          |                                          |            |
| rushb_version              | string  |          | calculated          | meta:metadata.rushbVersion               |            |
| ppp_version                | string  |          | calculated          | meta:context.version                     |            |
| match_date                 | string  |          | calculated          | meta:matchDate                           |            |
| demo_id                    | string  |          | calculated-redacted | meta:demoId                              |            |
| sharecode                  | string  |          | calculated-redacted | meta:sharecode                           |            |
| platform                   | string  |          | calculated          | meta:platform                            |            |
| match_type                 | string  |          | calculated          | meta:matchType                           |            |
| t_starters_avg_rank        | float64 |          | calculated          | is_bot, round, rank, steam_id, team_code |            |
| t_starters_avg_wins        | float64 |          | calculated          | is_bot, round, wins, steam_id, team_code |            |
| ct_starters_avg_rank       | float64 |          | calculated          | is_bot, round, rank, steam_id, team_code |            |
| ct_starters_avg_wins       | float64 |          | calculated          | is_bot, round, wins, steam_id, team_code |            |
| ct_starters_score_final    | int     |          | calculated          | round_state:ct_score                     |            |
| t_starters_score_final     | int     |          | calculated          | round_state:t_score                      |            |
| unique_steamids            | int     |          | calculated          | player_personal:steam_id                 |            |
| providence                 | string  |          | calculated          | metademo:providence                      |            |
| number_of_points           | int     |          | calculated          | shape of all data frames                 |            |

## item_dropped - single_event

Event that triggers this channel: item_dropped

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| player_id          | int     | False    | replay     |                 |                            |
| entity_id          | int32   | False    | replay     |                 |                            |
| item               | string  | False    | replay     |                 |                            |
| def_index          | int32   | False    | replay     |                 |                            |
| x_pos              | float64 | False    | replay     |                 |                            |
| y_pos              | float64 | False    | replay     |                 |                            |
| z_pos              | float64 | False    | replay     |                 |                            |
| reason             | string  | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## item_equip - single_event

Event that triggers this channel: item_equip

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| player_id          | int32   | False    | replay     |                 |                            |
| item               | string  | False    | replay     |                 |                            |
| def_index          | int32   | False    | replay     |                 |                            |
| can_zoom           | bool    | False    | replay     |                 |                            |
| has_silencer       | bool    | False    | replay     |                 |                            |
| is_silenced        | bool    | False    | replay     |                 |                            |
| has_tracers        | bool    | False    | replay     |                 |                            |
| weapon_type_code   | int32   | False    | replay     |                 |                            |
| is_painted         | bool    | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## item_pickup - single_event

Event that triggers this channel: item_pickup

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| player_id          | int32   | False    | replay     |                 |                            |
| item               | string  | False    | replay     |                 |                            |
| def_index          | int32   | False    | replay     |                 |                            |
| is_silent          | bool    | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## item_refund - single_event

Event that triggers this channel: item_refund

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| player_id          | int     | False    | replay     |                 |                            |
| item               | string  | False    | replay     |                 |                            |
| def_index          | int32   | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## molotov_fire - telemetry

Event that triggers this channel: tick_end

| Col Name        | Type    | Nullable | Origin     | Dependents             | Merge Keys                 |
| --------------- | ------- | -------- | ---------- | ---------------------- | -------------------------- |
| round           | int     | False    | replay     |                        |                            |
| tick            | int     | False    | replay     |                        |                            |
| entity_id       | int32   | False    | replay     |                        |                            |
| player_id       | int     | False    | replay     |                        |                            |
| fire_index      | int32   | False    | replay     |                        |                            |
| x_pos           | float64 | False    | replay     |                        |                            |
| y_pos           | float64 | False    | replay     |                        |                            |
| z_pos           | float64 | False    | replay     |                        |                            |
| is_burning      | bool    | False    | replay     |                        |                            |
| second          | float64 |          | calculated | tick, tick_rate        |                            |
| player_id_fixed | float64 | True     | merged     |                        | player_id, round, steam_id |
| entity_id_fixed | int     |          | calculated | round, entity_id, tick |                            |

## molotov_state - multi_event

Events that trigger this channel: inferno_detonate, inferno_expire, inferno_extinguish, inferno_startburn

| Col Name                         | Type    | Nullable | Origin     | Dependents                                                                           | Merge Keys            |
| -------------------------------- | ------- | -------- | ---------- | ------------------------------------------------------------------------------------ | --------------------- |
| round                            | int     | False    | replay     |                                                                                      |                       |
| tick                             | int     | False    | replay     |                                                                                      |                       |
| event_type                       | string  | False    | replay     |                                                                                      |                       |
| entity_id                        | int32   | False    | replay     |                                                                                      |                       |
| x_pos                            | float32 | False    | replay     |                                                                                      |                       |
| y_pos                            | float32 | False    | replay     |                                                                                      |                       |
| z_pos                            | float32 | False    | replay     |                                                                                      |                       |
| second                           | float64 |          | calculated | tick, tick_rate                                                                      |                       |
| entity_id_fixed                  | int     |          | calculated | round, entity_id, event_type, tick                                                   |                       |
| player_id                        | int     |          | calculated | event_type, second, round                                                            |                       |
| player_id_fixed                  | int     |          | calculated | event_type, second, round                                                            |                       |
| tick_throw                       | int     |          | calculated | event_type, second, round                                                            |                       |
| player_x_pos                     | float64 | True     | merged     |                                                                                      | tick_throw, player_id |
| player_y_pos                     | float64 | True     | merged     |                                                                                      | tick_throw, player_id |
| player_z_pos                     | float64 | True     | merged     |                                                                                      | tick_throw, player_id |
| player_x_vel                     | float64 | True     | merged     |                                                                                      | tick_throw, player_id |
| player_y_vel                     | float64 | True     | merged     |                                                                                      | tick_throw, player_id |
| player_z_vel                     | float64 | True     | merged     |                                                                                      | tick_throw, player_id |
| player_phi_ang                   | float64 | True     | merged     |                                                                                      | tick_throw, player_id |
| player_theta_ang                 | float64 | True     | merged     |                                                                                      | tick_throw, player_id |
| player_weapon_code               | int     | True     | merged     |                                                                                      | tick_throw, player_id |
| player_team_code                 | int     | True     | merged     |                                                                                      | tick_throw, player_id |
| burn_duration                    | float64 |          | calculated | second, entity_id_fixed, event_type                                                  |                       |
| was_extinguished_by_smoke        | int     |          | calculated | second, entity_id_fixed, event_type, burn_duration                                   |                       |
| extinguisher_id                  | int     |          | calculated | second, entity_id_fixed, event_type, x_pos, y_pos, z_pos, player_id                  |                       |
| extinguisher_id_fixed            | int     |          | calculated | second, entity_id, entity_id_fixed, event_type, x_pos, y_pos, z_pos, player_id_fixed |                       |
| smoke_entity_id                  | int     |          | calculated | second, entity_id, entity_id_fixed, event_type, x_pos, y_pos, z_pos                  |                       |
| smoke_entity_id_fixed            | int     |          | calculated | second, entity_id, entity_id_fixed, event_type, x_pos, y_pos, z_pos                  |                       |
| was_extinguished_by_thrown_smoke | float64 |          | calculated | second, entity_id, entity_id_fixed, event_type, x_pos, y_pos, z_pos                  |                       |
| fraction_extinguished            | float64 |          | calculated | second, entity_id_fixed, event_type, x_pos, y_pos, z_pos                             |                       |
| was_thrown_into_smoke            | int     |          | calculated | second, entity_id_fixed, event_type, x_pos, y_pos, z_pos                             |                       |

## other_death - single_event

Event that triggers this channel: other_death

| Col Name             | Type    | Nullable | Origin     | Dependents      | Merge Keys                   |
| -------------------- | ------- | -------- | ---------- | --------------- | ---------------------------- |
| round                | int     | False    | replay     |                 |                              |
| tick                 | int     | False    | replay     |                 |                              |
| other_type           | string  | False    | replay     |                 |                              |
| attacker_id          | int32   | True     | replay     |                 |                              |
| weapon_name          | string  | False    | replay     |                 |                              |
| is_headshot          | bool    | False    | replay     |                 |                              |
| penetration_amount   | int32   | False    | replay     |                 |                              |
| is_through_smoke     | bool    | True     | replay     |                 |                              |
| is_attacker_blind    | bool    | True     | replay     |                 |                              |
| is_noscope           | bool    | True     | replay     |                 |                              |
| second               | float64 |          | calculated | tick, tick_rate |                              |
| attacker_id_fixed    | int     | True     | merged     |                 | attacker_id, round, steam_id |
| attacker_x_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_y_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_z_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_x_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_y_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_z_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_phi_ang     | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_theta_ang   | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_weapon_code | int     | True     | merged     |                 | attacker_id, tick            |
| attacker_team_code   | int     | True     | merged     |                 | attacker_id, tick            |

## player_blind - single_event

Event that triggers this channel: player_blind

| Col Name             | Type    | Nullable | Origin     | Dependents      | Merge Keys                   |
| -------------------- | ------- | -------- | ---------- | --------------- | ---------------------------- |
| round                | int     | False    | replay     |                 |                              |
| tick                 | int     | False    | replay     |                 |                              |
| player_id            | int32   | False    | replay     |                 |                              |
| entity_id            | int32   | False    | replay     |                 |                              |
| attacker_id          | int32   | False    | replay     |                 |                              |
| blind_duration       | float32 | False    | replay     |                 |                              |
| second               | float64 |          | calculated | tick, tick_rate |                              |
| player_id_fixed      | float64 | True     | merged     |                 | player_id, round, steam_id   |
| attacker_id_fixed    | int     | True     | merged     |                 | attacker_id, round, steam_id |
| player_x_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_y_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_z_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_x_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_y_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_z_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_phi_ang       | float64 | True     | merged     |                 | player_id, tick              |
| player_theta_ang     | float64 | True     | merged     |                 | player_id, tick              |
| player_weapon_code   | int     | True     | merged     |                 | player_id, tick              |
| player_team_code     | int     | True     | merged     |                 | player_id, tick              |
| attacker_x_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_y_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_z_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_x_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_y_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_z_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_phi_ang     | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_theta_ang   | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_weapon_code | int     | True     | merged     |                 | attacker_id, tick            |
| attacker_team_code   | int     | True     | merged     |                 | attacker_id, tick            |

## player_chat - single_event

Event that triggers this channel: player_chat

| Col Name           | Type    | Nullable | Origin          | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | --------------- | --------------- | -------------------------- |
| round              | int     | False    | replay          |                 |                            |
| tick               | int     | False    | replay          |                 |                            |
| player_id          | int     | False    | replay          |                 |                            |
| text               | string  | False    | replay-redacted |                 |                            |
| is_chat_all        | bool    | True     | replay          |                 |                            |
| second             | float64 |          | calculated      | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged          |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged          |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged          |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged          |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged          |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged          |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged          |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged          |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged          |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged          |                 | player_id, tick            |
| player_team_code   | int     | True     | merged          |                 | player_id, tick            |

## player_connect - single_event

Event that triggers this channel: player_connect

| Col Name        | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| --------------- | ------- | -------- | ---------- | --------------- | -------------------------- |
| round           | int     | False    | replay     |                 |                            |
| tick            | int     | False    | replay     |                 |                            |
| player_index    | int     | False    | replay     |                 |                            |
| player_id       | int     | False    | replay     |                 |                            |
| is_bot          | bool    | False    | replay     |                 |                            |
| second          | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed | float64 | True     | merged     |                 | player_id, round, steam_id |

## player_death - single_event

Event that triggers this channel: player_death

| Col Name             | Type    | Nullable | Origin     | Dependents      | Merge Keys                   |
| -------------------- | ------- | -------- | ---------- | --------------- | ---------------------------- |
| round                | int     | False    | replay     |                 |                              |
| tick                 | int     | False    | replay     |                 |                              |
| player_id            | int32   | False    | replay     |                 |                              |
| attacker_id          | int32   | True     | replay     |                 |                              |
| assister_id          | int32   | True     | replay     |                 |                              |
| weapon_name          | string  | False    | replay     |                 |                              |
| is_headshot          | bool    | False    | replay     |                 |                              |
| penetration_amount   | int32   | False    | replay     |                 |                              |
| has_replay           | bool    | False    | replay     |                 |                              |
| is_flash_assist      | bool    | True     | replay     |                 |                              |
| is_through_smoke     | bool    | True     | replay     |                 |                              |
| is_attacker_blind    | bool    | True     | replay     |                 |                              |
| is_noscope           | bool    | True     | replay     |                 |                              |
| second               | float64 |          | calculated | tick, tick_rate |                              |
| player_id_fixed      | float64 | True     | merged     |                 | player_id, round, steam_id   |
| attacker_id_fixed    | float64 | True     | merged     |                 | attacker_id, round, steam_id |
| assister_id_fixed    | float64 | True     | merged     |                 | assister_id, round, steam_id |
| player_x_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_y_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_z_pos         | float64 | True     | merged     |                 | player_id, tick              |
| player_x_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_y_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_z_vel         | float64 | True     | merged     |                 | player_id, tick              |
| player_phi_ang       | float64 | True     | merged     |                 | player_id, tick              |
| player_theta_ang     | float64 | True     | merged     |                 | player_id, tick              |
| player_weapon_code   | int     | True     | merged     |                 | player_id, tick              |
| player_team_code     | int     | True     | merged     |                 | player_id, tick              |
| attacker_x_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_y_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_z_pos       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_x_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_y_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_z_vel       | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_phi_ang     | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_theta_ang   | float64 | True     | merged     |                 | attacker_id, tick            |
| attacker_weapon_code | int     | True     | merged     |                 | attacker_id, tick            |
| attacker_team_code   | int     | True     | merged     |                 | attacker_id, tick            |
| assister_x_pos       | float64 | True     | merged     |                 | assister_id, tick            |
| assister_y_pos       | float64 | True     | merged     |                 | assister_id, tick            |
| assister_z_pos       | float64 | True     | merged     |                 | assister_id, tick            |
| assister_x_vel       | float64 | True     | merged     |                 | assister_id, tick            |
| assister_y_vel       | float64 | True     | merged     |                 | assister_id, tick            |
| assister_z_vel       | float64 | True     | merged     |                 | assister_id, tick            |
| assister_phi_ang     | float64 | True     | merged     |                 | assister_id, tick            |
| assister_theta_ang   | float64 | True     | merged     |                 | assister_id, tick            |
| assister_weapon_code | int     | True     | merged     |                 | assister_id, tick            |
| assister_team_code   | int     | True     | merged     |                 | assister_id, tick            |

## player_disconnect - single_event

Event that triggers this channel: player_disconnect

| Col Name          | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ----------------- | ------- | -------- | ---------- | --------------- | -------------------------- |
| round             | int     | False    | replay     |                 |                            |
| tick              | int     | False    | replay     |                 |                            |
| player_id         | int32   | False    | replay     |                 |                            |
| disconnect_reason | string  | False    | replay     |                 |                            |
| is_bot            | bool    | False    | replay     |                 |                            |
| second            | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed   | float64 | True     | merged     |                 | player_id, round, steam_id |

## player_footstep - single_event

Event that triggers this channel: player_footstep

| Col Name        | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| --------------- | ------- | -------- | ---------- | --------------- | -------------------------- |
| round           | int     | False    | replay     |                 |                            |
| tick            | int     | False    | replay     |                 |                            |
| player_id       | int32   | False    | replay     |                 |                            |
| second          | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed | float64 | True     | merged     |                 | player_id, round, steam_id |

## player_hurt - single_event

Event that triggers this channel: player_hurt

| Col Name                 | Type    | Nullable | Origin     | Dependents               | Merge Keys                   |
| ------------------------ | ------- | -------- | ---------- | ------------------------ | ---------------------------- |
| round                    | int     | False    | replay     |                          |                              |
| tick                     | int     | False    | replay     |                          |                              |
| player_id                | int32   | False    | replay     |                          |                              |
| attacker_id              | int32   | False    | replay     |                          |                              |
| health                   | int32   | False    | replay     |                          |                              |
| armor                    | int32   | False    | replay     |                          |                              |
| weapon_name              | string  | True     | replay     |                          |                              |
| health_removed           | int32   | False    | replay     |                          |                              |
| armor_removed            | int32   | False    | replay     |                          |                              |
| hit_box_code             | int32   | False    | replay     |                          |                              |
| second                   | float64 |          | calculated | tick, tick_rate          |                              |
| player_id_fixed          | float64 | True     | merged     |                          | player_id, round, steam_id   |
| attacker_id_fixed        | float64 | True     | merged     |                          | attacker_id, round, steam_id |
| player_x_pos             | float64 | True     | merged     |                          | player_id, tick              |
| player_y_pos             | float64 | True     | merged     |                          | player_id, tick              |
| player_z_pos             | float64 | True     | merged     |                          | player_id, tick              |
| player_x_vel             | float64 | True     | merged     |                          | player_id, tick              |
| player_y_vel             | float64 | True     | merged     |                          | player_id, tick              |
| player_z_vel             | float64 | True     | merged     |                          | player_id, tick              |
| player_phi_ang           | float64 | True     | merged     |                          | player_id, tick              |
| player_theta_ang         | float64 | True     | merged     |                          | player_id, tick              |
| player_weapon_code       | int     | True     | merged     |                          | player_id, tick              |
| player_team_code         | int     | True     | merged     |                          | player_id, tick              |
| attacker_x_pos           | float64 | True     | merged     |                          | attacker_id, tick            |
| attacker_y_pos           | float64 | True     | merged     |                          | attacker_id, tick            |
| attacker_z_pos           | float64 | True     | merged     |                          | attacker_id, tick            |
| attacker_x_vel           | float64 | True     | merged     |                          | attacker_id, tick            |
| attacker_y_vel           | float64 | True     | merged     |                          | attacker_id, tick            |
| attacker_z_vel           | float64 | True     | merged     |                          | attacker_id, tick            |
| attacker_phi_ang         | float64 | True     | merged     |                          | attacker_id, tick            |
| attacker_theta_ang       | float64 | True     | merged     |                          | attacker_id, tick            |
| attacker_weapon_code     | int     | True     | merged     |                          | attacker_id, tick            |
| attacker_team_code       | int     | True     | merged     |                          | attacker_id, tick            |
| effective_health_removed | int     |          | calculated | player_id, round, health |                              |

## player_info - player_info

Event that triggers this channel: round_freeze_end

| Col Name         | Type    | Nullable | Origin        | Dependents           | Merge Keys                 |
| ---------------- | ------- | -------- | ------------- | -------------------- | -------------------------- |
| round            | int     | False    | replay        |                      |                            |
| player_id        | int     | False    | replay        |                      |                            |
| team_code        | int32   | False    | replay        |                      |                            |
| wins             | int     | False    | replay-capped |                      |                            |
| rank             | int     | False    | replay        |                      |                            |
| rank_type        | int     | False    | replay        |                      |                            |
| radar_color_code | int     | False    | replay        |                      |                            |
| player_id_fixed  | int     | True     | merged        |                      | player_id, round, steam_id |
| rank_raw         | int     |          | calculated    | player_info:rank     |                            |
| rank_platform    | float64 |          | calculated    | player_personal:rank |                            |

## player_inputs - telemetry

Event that triggers this channel: player_buttons_state_update

| Col Name               | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ---------------------- | ------- | -------- | ---------- | --------------- | -------------------------- |
| round                  | int     | False    | replay     |                 |                            |
| tick                   | int     | False    | replay     |                 |                            |
| player_id              | int     | False    | replay     |                 |                            |
| buttons_mask           | int64   | False    | replay     |                 |                            |
| button_attack          | bool    | False    | replay     |                 |                            |
| button_attack2         | bool    | False    | replay     |                 |                            |
| button_jump            | bool    | False    | replay     |                 |                            |
| button_duck            | bool    | False    | replay     |                 |                            |
| button_forward         | bool    | False    | replay     |                 |                            |
| button_back            | bool    | False    | replay     |                 |                            |
| button_move_left       | bool    | False    | replay     |                 |                            |
| button_move_right      | bool    | False    | replay     |                 |                            |
| button_turn_left       | bool    | False    | replay     |                 |                            |
| button_turn_right      | bool    | False    | replay     |                 |                            |
| button_use             | bool    | False    | replay     |                 |                            |
| button_reload          | bool    | False    | replay     |                 |                            |
| button_speed           | bool    | False    | replay     |                 |                            |
| button_score           | bool    | False    | replay     |                 |                            |
| button_look_at_weapon  | bool    | False    | replay     |                 |                            |
| button_zoom            | bool    | False    | replay     |                 |                            |
| button_use_or_reload   | bool    | False    | replay     |                 |                            |
| button_joy_auto_sprint | bool    | False    | replay     |                 |                            |
| second                 | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed        | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos           | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos           | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos           | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel           | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel           | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel           | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang         | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang       | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code     | int     | True     | merged     |                 | player_id, tick            |
| player_team_code       | int     | True     | merged     |                 | player_id, tick            |

## player_name - single_event

Event that triggers this channel: player_name

| Col Name        | Type    | Nullable | Origin          | Dependents      | Merge Keys                 |
| --------------- | ------- | -------- | --------------- | --------------- | -------------------------- |
| round           | int     | False    | replay          |                 |                            |
| tick            | int     | False    | replay          |                 |                            |
| player_id       | int32   | False    | replay          |                 |                            |
| name_new        | string  | False    | replay-redacted |                 |                            |
| name_old        | string  | False    | replay-redacted |                 |                            |
| second          | float64 |          | calculated      | tick, tick_rate |                            |
| player_id_fixed | int     | True     | merged          |                 | player_id, round, steam_id |

## player_personal - player_info

Event that triggers this channel: round_freeze_end

| Col Name             | Type   | Nullable | Origin          | Dependents       | Merge Keys |
| -------------------- | ------ | -------- | --------------- | ---------------- | ---------- |
| round                | int    | False    | replay          |                  |            |
| player_id            | int    | False    | replay          |                  |            |
| player_controller_id | int    | False    | replay          |                  |            |
| player_id_pawn       | int    | False    | replay          |                  |            |
| name                 | string | False    | replay-redacted |                  |            |
| clan_tag             | string | False    | replay-redacted |                  |            |
| steam_id             | string | False    | replay-redacted |                  |            |
| is_bot               | bool   |          | calculated      | steam_id         |            |
| player_id_fixed      | int    |          | calculated      | steam_id, is_bot |            |

## player_sound - single_event

Event that triggers this channel: player_sound

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| player_id          | int     | False    | replay     |                 |                            |
| radius             | int32   | False    | replay     |                 |                            |
| duration           | float32 | False    | replay     |                 |                            |
| is_step            | bool    | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## player_spawn - single_event

Event that triggers this channel: player_spawn

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| player_id          | int32   | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## player_status - telemetry

Event that triggers this channel: tick_end

| Col Name                      | Type    | Nullable | Origin          | Dependents                                                                                                                                                            | Merge Keys                 |
| ----------------------------- | ------- | -------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| tick                          | int     | False    | replay          |                                                                                                                                                                       |                            |
| round                         | int     | False    | replay          |                                                                                                                                                                       |                            |
| player_id                     | int     | False    | replay          |                                                                                                                                                                       |                            |
| player_controller_id          | int     | False    | replay          |                                                                                                                                                                       |                            |
| armor                         | int     | False    | replay          |                                                                                                                                                                       |                            |
| health                        | int     | False    | replay          |                                                                                                                                                                       |                            |
| place_name                    | string  | False    | replay          |                                                                                                                                                                       |                            |
| inv_primary                   | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_secondary                 | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_flashbang                 | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_taser                     | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_hegrenade                 | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_smokegrenade              | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_molotov                   | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_decoy                     | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_incgrenade                | int     | False    | replay          |                                                                                                                                                                       |                            |
| inv_c4                        | int     | False    | replay          |                                                                                                                                                                       |                            |
| current_equipment_cost        | int     | False    | replay          |                                                                                                                                                                       |                            |
| freezetime_end_equipment_cost | int     | False    | replay          |                                                                                                                                                                       |                            |
| money                         | int     | False    | replay          |                                                                                                                                                                       |                            |
| ping                          | int     | False    | replay-redacted |                                                                                                                                                                       |                            |
| round_start_equipment_cost    | int     | False    | replay          |                                                                                                                                                                       |                            |
| zoom_level                    | int     | True     | replay          |                                                                                                                                                                       |                            |
| iron_sight_mode               | int     | True     | replay          |                                                                                                                                                                       |                            |
| burst_mode                    | bool    | True     | replay          |                                                                                                                                                                       |                            |
| is_silenced                   | bool    | True     | replay          |                                                                                                                                                                       |                            |
| weapon_mode                   | int     | True     | replay          |                                                                                                                                                                       |                            |
| flash_duration                | float32 | False    | replay          |                                                                                                                                                                       |                            |
| flash_max_alpha               | float32 | False    | replay          |                                                                                                                                                                       |                            |
| has_c4                        | bool    | False    | replay          |                                                                                                                                                                       |                            |
| has_defuser                   | bool    | False    | replay          |                                                                                                                                                                       |                            |
| has_helmet                    | bool    | False    | replay          |                                                                                                                                                                       |                            |
| is_defusing                   | bool    | False    | replay          |                                                                                                                                                                       |                            |
| is_fake_player                | bool    | False    | replay          |                                                                                                                                                                       |                            |
| is_in_bomb_zone               | bool    | False    | replay          |                                                                                                                                                                       |                            |
| is_in_buy_zone                | bool    | False    | replay          |                                                                                                                                                                       |                            |
| is_reloading                  | bool    | False    | replay          |                                                                                                                                                                       |                            |
| is_scoped                     | bool    | False    | replay          |                                                                                                                                                                       |                            |
| is_spotted                    | bool    | False    | replay          |                                                                                                                                                                       |                            |
| is_walking                    | bool    | False    | replay          |                                                                                                                                                                       |                            |
| second                        | float64 |          | calculated      | tick, tick_rate                                                                                                                                                       |                            |
| player_id_fixed               | float64 | True     | merged          |                                                                                                                                                                       | player_id, round, steam_id |
| equipment_value_calc          | int     |          | calculated      | inv_flashbang, inv_taser, inv_hegrenade, inv_smokegrenade, inv_molotov, inv_decoy, inv_incgrenade, inv_c4, armor, has_defuser, has_helmet, inv_primary, inv_secondary |                            |

## player_vector - telemetry

Event that triggers this channel: tick_end

| Col Name              | Type    | Nullable | Origin     | Dependents                                  | Merge Keys                 |
| --------------------- | ------- | -------- | ---------- | ------------------------------------------- | -------------------------- |
| tick                  | int     | False    | replay     |                                             |                            |
| round                 | int     | False    | replay     |                                             |                            |
| player_id             | int     | False    | replay     |                                             |                            |
| x_pos                 | float64 | False    | replay     |                                             |                            |
| y_pos                 | float64 | False    | replay     |                                             |                            |
| z_pos                 | float64 | False    | replay     |                                             |                            |
| current_ammo          | int     | True     | replay     |                                             |                            |
| weapon_code           | int     | True     | replay     |                                             |                            |
| inaccuracy            | float32 | True     | replay     |                                             |                            |
| last_shot_time        | float32 | True     | replay     |                                             |                            |
| recoil_index          | float32 | True     | replay     |                                             |                            |
| phi_ang               | float32 | False    | replay     |                                             |                            |
| theta_ang             | float32 | False    | replay     |                                             |                            |
| is_ducked             | bool    | False    | replay     |                                             |                            |
| is_ducking            | bool    | False    | replay     |                                             |                            |
| duck_amount           | float32 | False    | replay     |                                             |                            |
| duck_speed            | float32 | False    | replay     |                                             |                            |
| fall_velocity         | float32 | False    | replay     |                                             |                            |
| view_punch_angle_tick | int     | False    | replay     |                                             |                            |
| is_rescuing           | bool    | False    | replay     |                                             |                            |
| second                | float64 |          | calculated | tick, tick_rate                             |                            |
| player_id_fixed       | float64 | True     | merged     |                                             | player_id, round, steam_id |
| team_code             | int     | True     | merged     |                                             | round, player_id           |
| theta_vel             | float64 |          | calculated | second, player_id, theta                    |                            |
| phi_vel               | float64 |          | calculated | second, player_id, phi                      |                            |
| ang_vel               | float64 |          | calculated | phi_vel, theta_vel                          |                            |
| x_vel                 | float64 |          | calculated | second, x_pos                               |                            |
| y_vel                 | float64 |          | calculated | second, y_pos                               |                            |
| z_vel                 | float64 |          | calculated | second, z_pos                               |                            |
| speed_2d              | float64 |          | calculated | x_vel, y_vel                                |                            |
| movement_angle        | float64 |          | calculated | second, x_vel, y_vel                        |                            |
| movement_angle_diff   | float64 |          | calculated | second, speed_2d, theta_ang, movement_angle |                            |

## rank_update - single_event

Event that triggers this channel: rank_update

| Col Name           | Type    | Nullable | Origin        | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ------------- | --------------- | -------------------------- |
| round              | int     | False    | replay        |                 |                            |
| tick               | int     | False    | replay        |                 |                            |
| player_id          | int     | False    | replay        |                 |                            |
| rank_old           | int32   | False    | replay        |                 |                            |
| rank_new           | int32   | False    | replay        |                 |                            |
| rank_change        | float32 | False    | replay        |                 |                            |
| win_count          | int32   | False    | replay-capped |                 |                            |
| second             | float64 |          | calculated    | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged        |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged        |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged        |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged        |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged        |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged        |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged        |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged        |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged        |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged        |                 | player_id, tick            |
| player_team_code   | int     | True     | merged        |                 | player_id, tick            |

## round_end - single_event

Event that triggers this channel: round_end

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys |
| ------------------ | ------- | -------- | ---------- | --------------- | ---------- |
| round              | int     | False    | replay     |                 |            |
| tick               | int     | False    | replay     |                 |            |
| winner_team_code   | int32   | False    | replay     |                 |            |
| win_reason_code    | int32   | False    | replay     |                 |            |
| win_reason_message | string  | False    | replay     |                 |            |
| player_count       | int32   | False    | replay     |                 |            |
| second             | float64 |          | calculated | tick, tick_rate |            |

## round_mvp - single_event

Event that triggers this channel: round_mvp

| Col Name        | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| --------------- | ------- | -------- | ---------- | --------------- | -------------------------- |
| round           | int     | False    | replay     |                 |                            |
| tick            | int     | False    | replay     |                 |                            |
| player_id       | int32   | False    | replay     |                 |                            |
| mvp_count       | int     | False    | replay     |                 |                            |
| second          | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed | int     | True     | merged     |                 | player_id, round, steam_id |

## round_start - single_event

Event that triggers this channel: round_start

| Col Name | Type    | Nullable | Origin     | Dependents      | Merge Keys |
| -------- | ------- | -------- | ---------- | --------------- | ---------- |
| round    | int     | False    | replay     |                 |            |
| tick     | int     | False    | replay     |                 |            |
| second   | float64 |          | calculated | tick, tick_rate |            |

## round_state - multi_event

Events that trigger this channel: begin_new_match, bomb_defused, bomb_exploded, bomb_planted, buytime_ended, round_announce_match_start, round_announce_warmup, round_end, round_freeze_end, round_officially_ended, round_start, start_halftime

| Col Name     | Type    | Nullable | Origin       | Dependents      | Merge Keys |
| ------------ | ------- | -------- | ------------ | --------------- | ---------- |
| round        | int     | False    | replay       |                 |            |
| tick         | int     | False    | replay       |                 |            |
| event_type   | string  | False    | replay       |                 |            |
| t_score      | int     | False    | replay_fixed |                 |            |
| ct_score     | int     | False    | replay_fixed |                 |            |
| t_score_raw  | int     | False    | replay       |                 |            |
| ct_score_raw | int     | False    | replay       |                 |            |
| phase        | string  | False    | replay       |                 |            |
| is_warmup    | bool    | False    | replay       |                 |            |
| second       | float64 |          | calculated   | tick, tick_rate |            |

## score_update - single_event

Event that triggers this channel: score_update

| Col Name  | Type    | Nullable | Origin     | Dependents      | Merge Keys |
| --------- | ------- | -------- | ---------- | --------------- | ---------- |
| round     | int     | False    | replay     |                 |            |
| tick      | int     | False    | replay     |                 |            |
| team_code | int32   | False    | replay     |                 |            |
| old_score | int32   | False    | replay     |                 |            |
| new_score | int32   | False    | replay     |                 |            |
| second    | float64 |          | calculated | tick, tick_rate |            |

## team_change - single_event

Event that triggers this channel: player_team

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| player_id          | int     | False    | replay     |                 |                            |
| old_team_code      | int32   | False    | replay     |                 |                            |
| new_team_code      | int32   | False    | replay     |                 |                            |
| is_bot             | bool    | False    | replay     |                 |                            |
| silent             | bool    | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## tick - telemetry

Event that triggers this channel: tick_end

| Col Name                    | Type    | Nullable | Origin     | Dependents         | Merge Keys |
| --------------------------- | ------- | -------- | ---------- | ------------------ | ---------- |
| round                       | int     | False    | replay     |                    |            |
| tick                        | int     | False    | replay     |                    |            |
| second                      | float64 |          | calculated | tick, tick_rate    |            |
| previous_phase              | string  |          | calculated | event_type, second |            |
| second_since_previous_phase | float64 |          | calculated | second             |            |

## weapon_action - multi_event

Events that trigger this channel: fire_on_empty, reload, zoom, zoom_rifle

| Col Name           | Type    | Nullable | Origin     | Dependents      | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | --------------- | -------------------------- |
| round              | int     | False    | replay     |                 |                            |
| tick               | int     | False    | replay     |                 |                            |
| event_type         | string  | False    | replay     |                 |                            |
| player_id          | int32   | False    | replay     |                 |                            |
| second             | float64 |          | calculated | tick, tick_rate |                            |
| player_id_fixed    | float64 | True     | merged     |                 | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                 | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                 | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                 | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                 | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                 | player_id, tick            |
| player_team_code   | int     | True     | merged     |                 | player_id, tick            |

## weapon_fire - single_event

Event that triggers this channel: weapon_fire

| Col Name           | Type    | Nullable | Origin     | Dependents                                     | Merge Keys                 |
| ------------------ | ------- | -------- | ---------- | ---------------------------------------------- | -------------------------- |
| round              | int     | False    | replay     |                                                |                            |
| tick               | int     | False    | replay     |                                                |                            |
| player_id          | int32   | False    | replay     |                                                |                            |
| player_id_pawn     | int32   | False    | replay     |                                                |                            |
| weapon_name        | string  | False    | replay     |                                                |                            |
| is_silenced        | bool    | False    | replay     |                                                |                            |
| second             | float64 |          | calculated | tick, tick_rate                                |                            |
| player_id_fixed    | float64 | True     | merged     |                                                | player_id, round, steam_id |
| player_x_pos       | float64 | True     | merged     |                                                | player_id, tick            |
| player_y_pos       | float64 | True     | merged     |                                                | player_id, tick            |
| player_z_pos       | float64 | True     | merged     |                                                | player_id, tick            |
| player_x_vel       | float64 | True     | merged     |                                                | player_id, tick            |
| player_y_vel       | float64 | True     | merged     |                                                | player_id, tick            |
| player_z_vel       | float64 | True     | merged     |                                                | player_id, tick            |
| player_phi_ang     | float64 | True     | merged     |                                                | player_id, tick            |
| player_theta_ang   | float64 | True     | merged     |                                                | player_id, tick            |
| player_weapon_code | int     | True     | merged     |                                                | player_id, tick            |
| player_team_code   | int     | True     | merged     |                                                | player_id, tick            |
| missed_molotov     | int     |          | calculated | event_type-molotov_state, second-molotov_state |                            |

## world_item_vector - telemetry

Event that triggers this channel: tick_end

| Col Name      | Type    | Nullable | Origin     | Dependents      | Merge Keys |
| ------------- | ------- | -------- | ---------- | --------------- | ---------- |
| round         | int     | False    | replay     |                 |            |
| tick          | int     | False    | replay     |                 |            |
| entity_id     | int32   | False    | replay     |                 |            |
| prev_owner_id | int     | False    | replay     |                 |            |
| item          | string  | False    | replay     |                 |            |
| def_index     | int32   | False    | replay     |                 |            |
| x_pos         | float64 | False    | replay     |                 |            |
| y_pos         | float64 | False    | replay     |                 |            |
| z_pos         | float64 | False    | replay     |                 |            |
| second        | float64 |          | calculated | tick, tick_rate |            |
