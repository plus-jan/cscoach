# Data: the PureSkill.gg CSDS corpus (sole data source)

**Decision (ADR-0003):** every model, feature, metric and evaluation in this project is derived from the
**PureSkill.gg Competitive CS2 Gameplay Data Set** ("CSDS"), accessed with the official PureSkill.gg
libraries. We do **not** parse demos, scrape, or add external data (no external nav meshes, no HLTV
data, no FACEIT API). Any new feature must be computable from CSDS channels.

- Product page (AWS Data Exchange): https://aws.amazon.com/marketplace/pp/prodview-v3o7zrt6okwmo
- Docs: https://docs.pureskill.gg/datascience/ (source: github.com/pureskillgg/docs)
- Channel spec (vendored, MIT): [`csds_spec.md`](csds_spec.md) · data dictionary: [`csds_dictionary.csv`](csds_dictionary.csv)

## Official libraries (the only sanctioned access path)

| Package (PyPI) | Version seen | Role in this project |
|---|---|---|
| `pureskillgg-dsdk` (`pureskillgg_dsdk`) | 3.2.1, Python ≥ 3.11 | `download_adx_dataset_revision` / `export_*_to_s3` (ADX export), `DsReaderFs` / `DsReaderS3` + `GameDsLoader` (read one match: `get_channels([{"channel": ..., "columns": [...]}])`), `TomeCuratorFs` (header tome, subheader tomes via selector, `make_tome` for cross-match datasets, `iterate_pages`) |
| `pureskillgg-csgo-dsdk` (`pureskillgg_csgo_dsdk`) | 3.1.1 | `pop_overtime(df, max_rounds_csgo=24)` (CS2 is MR12 → **24**, the default 30 is CS:GO), PII scrubbing (already applied to the public data) |
| `makenew-pyskill` (template/tutorial) | — | Reference workflow: ADX export (tutorial step 7), tome creation |

Tome env vars: `PURESKILLGG_TOME_DEFAULT_HEADER_NAME`, `PURESKILLGG_TOME_DS_TYPE` (= `csds`),
`PURESKILLGG_TOME_COLLECTION_PATH`, `PURESKILLGG_TOME_DS_COLLECTION_PATH`. Tome names follow
`name.YYYY-MM-DD,YYYY-MM-DD[.comment]`.

## What the corpus is

- CS2 matches from **Valve Matchmaking, FACEIT and other third parties**, uploaded by PureSkill.gg users
  (the other 9 players per match are mostly not users). Daily revisions; ~90–150 matches/day recently,
  ~12/day in July 2025. **Only ~1 year retained** (365 revisions from 2025-07-18 as of 2026-08-27):
  download what you need, older revisions disappear. Checked 2026-09-28: 1,337 revisions exist, 941 of
  them (2021-12-01 to 2025-07-18) are `Revoked` ("Retention policy: data older than the retention window
  is archived to Amazon S3 Glacier Deep Archive and removed from AWS Data Exchange"); 396 are live
  (2025-07-19 to 2026-09-27), one per day.
- Asset names are `csds/YYYY/MM/DD/<match_id>/<channel>`. The folder date is **not always** the revision
  date (a revision can hold matches filed under other dates), so the match → revision map comes from
  the asset listing (`<root>/manifest/adx_assets.parquet`), not from the path. A revision holds at most
  10,000 assets (ADX quota).
- One match = JSON index object `csds` + **42 Parquet channels** (since 2026-08-04; 30 before, mixed on
  2026-08-02). **Always drive reading from the per-match index**, never a hard-coded channel list.
- ~35 MB/match, of which `player_vector` + `player_status` (per-tick telemetry) are ~30 MB.
- Channel categories: `header`, `player_info` (per round), `single_event`, `multi_event`, `telemetry`.

## Channels → what we use them for

| Need | Channels (key columns) |
|---|---|
| Match metadata, split keys, drift | `header`: `build_num` (game build), `tick_rate`, `map_name`, `match_date`, `platform` (steam/faceit/unknown), `match_type`, `providence` (user/auto), `is_wingman`, `{t,ct}_starters_avg_rank`, `ppp_version`, final scores |
| Rounds & outcome labels | `round_end` (`winner_team_code`, `win_reason_code`), `round_start`, `round_state` (`phase`, `is_warmup`, scores), `tick` (`previous_phase`, `second_since_previous_phase`) |
| Tier labels | `player_info` (`rank`, `rank_type`, `rank_raw`, `rank_platform`, `wins`), `rank_update`, `header.*_avg_rank` |
| WP state (per tick) | `player_status` (`health`, `armor`, `has_helmet`, `has_defuser`, `inv_*`, `current_equipment_cost`, `freezetime_end_equipment_cost`, `equipment_value_calc`, `money`, `place_name`, `is_spotted`, `flash_duration`, …), `bomb_state`, `bomb_action`, `bomb_defuse`, `player_death` |
| Duels / mechanics (xK) | `player_vector` (`x/y/z_pos`, `phi/theta_ang`, `ang_vel`, `speed_2d`, `movement_angle`, `inaccuracy`, `recoil_index`, `weapon_code`, `is_ducked`), `player_inputs` (movement/attack buttons → counter-strafe timing), `weapon_fire`, `player_hurt` (`hit_box_code`, `health_removed`), `bullet_damage`, `player_death`, `player_blind` |
| Economy | `player_status` (`money`, equipment costs, `inv_*`), `item_pickup`, `item_dropped`, `item_refund`, `item_equip` |
| Utility & spatial | `grenade_state`, `grenade_vector`, `grenade_bounce`, `molotov_state`, `molotov_fire`, `player_vector` positions, `player_status.place_name` (named map areas), `player_footstep`, `player_sound` |

Exact column types, origins (`replay`, `calculated`, `merged`, …) and nullability: see the spec.

## Hard constraints and quirks (design must respect these)

1. **No cross-match player identity.** `player_personal.steam_id` is replaced by a per-match alias
   (A, B, C…). The same person cannot be followed across matches. Consequences (ADR-0005):
   no longitudinal player ratings or "player holdout". Player-level reliability can only be measured
   **within a match** (e.g. odd/even rounds). Coaching output is **per match**. Population-level
   stability (across matches) is still measurable.
2. **License: CC BY-NC-SA 4.0 via the Data Subscriber Agreement.** Non-commercial use only; attribution
   "Data provided by PureSkill.gg." on anything published; derived works under the same license.
   Access needs an approved ADX subscription; export incurs AWS costs. Never try to re-identify players
   or obtain source demos.
3. **Sample bias:** matches come from PureSkill.gg users (self-selected, improvement-minded); platform
   mix MM/FACEIT. **Old FACEIT matches lack rank information.** Manually uploaded demos have
   upload date instead of play date (`providence = user`).
4. **Duplicates** can exist; deduplicate with values computed from the `header` channel.
5. **Missing ticks/events** occur (rare); skip problematic matches, but log and count them.
6. **Merged columns** (positions/velocities joined onto events) use an as-of merge to the nearest earlier
   tick: they can be null and are slightly stale. **Nullable ints arrive as doubles.**
7. Columns whose origin ends in `-deleted` must be skipped. Redacted columns contain `redacted`/`0`.
8. **Codes are undocumented** in the spec (`team_code`, `winner_team_code`, `win_reason_code`,
   `weapon_code`, `hit_box_code`, `rank_type`, `site_code`): derive and document mappings empirically
   (assumption A-15, task MV.1).
9. **Overtime:** CS2 regulation is 24 rounds; use `pop_overtime(..., max_rounds_csgo=24)` where overtime
   must be excluded; model overtime explicitly otherwise (economy differs).
10. **Header final scores (F-02):** `*_starters_score_final` gives the right winner score but the
   loser score is wrong in ~48% of matches. Use the last `round_state` scores (t_score/ct_score) where
   channels exist; `is_wingman` is null in older ppp versions (use `unique_steamids` ≤ 5).
11. **Duplicates and quality (M1.3):** `<root>/manifest/match_quality.parquet` holds `dedup_key`,
   `is_canonical`, `format`, `final_state`, `q_*` flags and `clean`; nothing is deleted from `csds/`.
   Use subheader tomes `subheader.2025-09-01,2026-09-28.clean*` or filter the flag table.
12. **Ranks (M1.4, F-03):** see the decoding table in the M1.4 report and docs/specs/06; per-match tiers in
   `<root>/manifest/match_tiers.parquet` (full-channel matches only; null when < 6 known ranks, never guessed).
   `header.*_starters_avg_rank` averages unranked players as 0; don't use it for tiers.
13. **Rounds (M2.1, F-05):** `winner_team_code` 2 = T / 3 = CT, but the v30 parser reports a stale side in
   the first round of every half (fixed in `cscoach.data.rounds`); v30 has no round end reasons (only 8/9).
   Per-match round tables: `<root>/derived/rounds/`; reconciliation flags: `<root>/manifest/rounds_check.parquet`.

## Access procedure (for the implementing agent)

**Current setup (M1.2):** ADX dataset `f49be2ef387af522a7b6f000158113e0` (`…-csds-0`, us-east-1; a
`…-csds-tome-0` dataset exists too), export bucket `cs2coach-csds-688474982708`, local collection
`/media/jan/merged/cs2coach`. Run `uv run python -m cscoach.data.export {index,plan,export,sync}` with
`configs/export.yaml`; then `uv run python -m cscoach.data.manifest` to refresh the manifest. boto3 needs
`botocore[crt]` for `aws login` credentials.

**Sampling rule (F-01):** every match has `header` + `csds`; all channels exist for a seeded sample
(`in_seeded_sample` in the manifest; `export.full_channel_fraction`, `export.sample_seed` in
docs/specs/06) plus a legacy test download of unknown selection. Analyses that need non-header channels
use `in_seeded_sample == True` only. To grow the sample, raise the fraction (nested: it only adds
matches) and rerun `index`/`plan`/`export`/`sync`.

1. The user subscribes to the ADX product (approval takes days) and provides AWS credentials.
2. Export revisions (≤ 1 month per batch) with `pureskillgg_dsdk.download_adx_dataset_revision` or to
   S3. Start with channels you need; skip `player_vector`/`player_status` unless the task needs telemetry.
3. Build a **header tome** (`TomeCuratorFs.create_header_tome`) → dedup → **subheader tomes** per
   platform/rank availability/date window → `make_tome` per derived table (rounds, snapshots, duels).
4. Record per export: revision ids, date range, channel set version (30 vs 42), `ppp_version`, counts.
