# 06 — Parameters (initial values, all tied to assumptions)

Every threshold, constant and default the implementation needs, with its **initial value** and the
**assumption** that governs it. Values are proposals until the assumption is `supported`/`decided`
(docs/assumptions.yaml). The implementation puts these in config files (never in code) and records
the assumption ID next to each key. Changing a value = updating this table + the assumption's evidence.

## Validation gates and statistics

| Key | Initial value | Assumption |
|---|---|---|
| gates.wp.ece_max (overall) | 0.02 | A-06 |
| gates.wp.ece_max_per_tier | 0.03 | A-06 |
| gates.wp.ece_max_per_map | 0.035 | A-06 |
| gates.wp.brier_skill_vs_baseline (CI lower bound >) | 0.0 | A-06 |
| gates.wp.min_rounds_per_stratum | 500 | A-07 |
| gates.xk.ece_max | 0.03 | A-06 |
| gates.xk.auc_min | 0.62 | A-06 |
| gates.xk.min_duels_per_stratum | 1000 | A-07 |
| gates.player_metric.stability_min (Franks S, match halves) | 0.5 | A-08 |
| gates.player_metric.reliability_min (odd/even split-half, supplementary) | 0.5 | A-08 |
| gates.player_metric.discrimination_min | 0.3 | A-08 |
| gates.player_metric.independence_min | 0.2 | A-08 |
| gates.player_metric.min_ess | 30 | A-07 |
| ece.n_bins / strategy | 15 / quantile | A-09 |
| bootstrap.n_resamples / alpha (test metrics, cluster, no refit) | 500 / 0.05 | A-10 |
| model-uncertainty bootstrap: B / fraction φ (fractional randomized cluster, refit) | 101 / tuned in MV.4 (football reference 0.35) | A-24 |
| split train/calibration/test (by match) | 0.70 / 0.10 / 0.20 | A-28 |
| loop.budget / alpha / n_resamples (gated autoresearch loop, docs/specs/07 §2) | 15 iterations / 0.05 (one-sided level 1 − 0.05/15 per keep) / 2000 | A-42 |

## Tiers (canonical: low, mid, high, semipro)

| Key | Initial value | Assumption |
|---|---|---|
| FACEIT level → tier | 1–3 low, 4–6 mid, 7–9 high, 10 semipro | A-11 |
| Premier rating → tier | <10k low, 10–15k mid, 15–20k high, ≥20k semipro | A-11 |
| MM skill group → tier | 1–6 low, 7–12 mid, 13–16 high, 17–18 semipro | A-11 |
| rank field decoding (`rank`, `rank_type`, `rank_platform`) | Steam `rank_type` 11 = Premier, 12 = Competitive SG, 7 = Wingman SG; `rank` 0 = unknown; FACEIT level = `rank_platform` (0 = unknown); without `rank_type` (v30): Premier iff any rank ≥ premier_min_rating (M1.4) | A-15 |
| premier_min_rating (type-free scale inference) | 19 | A-15 |
| rounds.code_side (`team_code`, `winner_team_code`) | 2 = T, 3 = CT | A-15 |
| rounds.flip_winner_after_swap (channel sets) | v30 (first round after each side swap) | A-15 |
| match tier rule | median of known player tiers | A-12 |
| min players with known rank | 6 | A-12 |

## Data export (`configs/export.yaml`, M1.2)

| Key | Initial value | Assumption |
|---|---|---|
| export.window (revision dates) | 2025-09-01 to 2026-09-27 (all live ADX revisions from the start date) | A-32 |
| export.full_channel_fraction (seeded sample of matches exported with all channels; headers for all) | 0.35 (0.15 until the M1.5 top-up, F-04) | A-32 |
| export.full_channel_fraction_by_platform (stratified override; pooled stats weight by 1/inclusion_prob) | faceit 1.0 | A-32 |
| export.sample_seed | 20260928 | A-32 |

## Data quality (`configs/quality.yaml`, M1.3)

| Key | Initial value | Assumption |
|---|---|---|
| quality.dedup_key (header columns) | map_name, server_name, number_of_points, final scores (no date) | A-36 |
| quality.wingman_max_unique_steamids (when `is_wingman` is null) | 5 | A-43 |
| quality.wins_needed (5v5 / wingman) | 13 / 9 | A-43 |
| quality.max_tick_gap_s | 1.0 | A-40 |

## Game rules (verify on CSDS: `player_status.money`, `tick`/`round_state` phases)

| Key | Initial value | Assumption |
|---|---|---|
| start money / max money / OT start money | 800 / 16000 / 12500 | A-13 |
| rounds per half (regulation 24) / OT half | 12 / 3 | A-13 |
| round win: elimination / time (CT) / defused / exploded | 3250 / 3250 / 3500 / 3500 | A-13 |
| loss bonus ladder | 1400, 1900, 2400, 2900, 3400 | A-13 |
| loss counter at half start / on win | 1 / decrement | A-13 |
| T loss after plant bonus / planter / defuser | 800 / 300 / 300 | A-13 |
| kill reward default / SMG / P90 / shotgun / XM1014 / AWP / knife / Zeus / CZ75 | 300 / 600 / 300 / 900 / 600 / 100 / 1500 / 0 / 100 | A-13 |
| round time / bomb timer / freeze time (s) | 115 / 40 / 15 | A-14 |
| tick rate | read `header.tick_rate` (expect 64) | A-16 |
| `pop_overtime` max rounds | 24 | A-13 |

## Features, windows, valuation

| Key | Initial value | Assumption |
|---|---|---|
| snapshot cadence (plus all event ticks) | 1.0 s | A-22 |
| WPA pre / post offset | 1 tick / 1 tick | A-18 |
| kill credit split killer / assister / flash-assister | 0.70 / 0.15 / 0.15 (missing → killer) | A-23 |
| trade window | 5.0 s | A-17 |
| Shapley permutations (when > 7 contributors) / seed | 200 / 7 | A-23 |
| risky duel: max xK / min WP-if-avoided | 0.30 / 0.85 | A-05 |
| duel window / censored handling | 3.0 s / drop | A-19 |
| counter-strafe "stopped" speed | 34 u/s (weapon-independent) | A-20 |
| buy classes eco / force / half / full (per player equipment) | < 1500 / < 3000 / < 4000 / ≥ 4000 | A-21 |
| team buy types (team start equipment E, team spend S; CS:GO pro reference) | eco: E<3k & S<2k; low: E<3k & 2k≤S<7.5k; half: E<3k & 7.5k≤S<20k; hero low: 3k≤E<20k & S<7.5k; hero half: 3k≤E<20k & 7.5k≤S<17k; full: E+S≥20k | A-21 |
| area graph: node definition / edge weight | `place_name` / median transit time | A-37 |

## Models

| Key | Initial value | Assumption |
|---|---|---|
| WP features (v1) | see docs/specs/03 | A-01 (tier/platform conditioning) |
| monotone constraints | +alive_ct, −alive_t, +hp_ct, −hp_t, +equip_ct, −equip_t, +man_advantage | A-27 |
| LightGBM start values | n_estimators 2000, lr 0.03, num_leaves 31, min_child_samples 200, subsample 0.8, colsample 0.8, λ 1.0, early stopping 100 | A-29 |
| calibration | auto: isotonic if ≥ 5000 rows else Platt; per tier if ≥ 1000 rows | A-28 |
| xK features | see docs/specs/03#xk | A-19, A-20 |

## Presentation and product

| Key | Initial value | Assumption |
|---|---|---|
| credible/confidence interval shown to players | 80% | A-30 |
| max focus points per match | 3 | A-30 |
| data volume target | ≥ 2,000 matches, ≥ 300 per tier×platform bucket, ≥ 5 maps | A-32 |
| runtime budget | < 30 s per match on 4 cores (excl. download) | A-32 |
