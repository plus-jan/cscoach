# 03 — Models

## WP — round win probability

**Target**: `y_ct_win` for the round containing the snapshot.
**Unit of prediction**: snapshot at tick *t*; features use only data with tick ≤ *t*.

**Features v1** (`features/state.py`): alive_ct/t, hp_sum_ct/t, armor_sum, helmets, kit
count (CT), equipment value ct/t, primary weapon class counts (rifle, awp, smg,
shotgun, pistol-only), utility counts, bomb_planted, bomb_site, time_remaining_s
(round timer or bomb timer when planted), man_advantage (alive_ct − alive_t),
tier (categorical), map (categorical).
**Features v2** (M7): nav-distance of nearest T to each site, CT site coverage,
area-control share, defuser-to-bomb distance, smokes active on key edges.

**Models**
1. `baseline_wp`: logistic regression on alive_ct, alive_t, hp_sum_ct, hp_sum_t,
   bomb_planted, time_remaining_s (+ interactions alive×planted). Reference only.
2. `GBDTWinProbability`: LightGBM; monotone constraints: +alive_ct, −alive_t, +hp_ct,
   −hp_t, +equipment_ct, −equipment_t. Early stopping on grouped validation fold.
3. Per-tier calibration layer (`models/calibration.py`): isotonic (≥ 5k calibration
   rows per tier) else Platt; fit on a dedicated calibration fold of matches.

**Symmetry**: `wp_t = 1 − wp_ct`. Optionally augment/check by side-swap test on
symmetric states (sanity only; CS2 is not side-symmetric).

## xK — expected kills (duel model) {#xk}

**Duel definition** (M4.1): the first damage or first mutual visibility event between
two opposing players starts a duel; it resolves when one of them dies within
`duel_window_s` (config) or is censored (drop or model as third class — ADR).
**Pre-duel features** (computed at tick_start − ε): distance, height delta, weapons
(class + specific), HP/armor/helmet, own & opponent speed (counter-strafe: speed <
threshold at first shot), angular offset of crosshair from opponent head position,
peeker vs holder, flashed (remaining duration), smoke between, nearby teammates
(trade availability), tier.
**Output**: P(p1 wins duel). xK per player = Σ over duels of P(win).
**Uses**: execution = kills − xK (shrunk); decision quality = (xK, ΔWP-if-avoided).

## WPA

For event *e* at tick *t_e*: `wpa_team = WP_team(t_e + post) − WP_team(t_e − pre)`
(defaults pre = 1 tick before, post = state after event resolution). Credit is split per
`configs/valuation.yaml` rules (M5.2) or by Shapley over contributors (M5.3) with value
function *v(S)* = WP of the counterfactual state where only contributors in S acted.
Efficiency: Σ credits = ΔWP (tested).

## Economy

Rules engine (`economy/rules.py`) from `configs/economy_cs2.yaml` (values must be
verified against the current CS2 build, M6.1). Counterfactual buys: re-evaluate
freeze-end WP with alternative equipment vectors and simulate next-round money for both
outcomes; expected value over the two-round horizon = Σ_outcomes P(outcome) · WP_next.

## Spatial

Nav graph (nodes = nav areas, edges = walkable connections, weights = travel time).
Utility delay = shortest-path time with smoke/molotov-blocked edges removed − without.
Converted to WPA via WP model sensitivity to `time_remaining_s` and positional features.

## Player-level aggregation

Raw per-player sums/means → empirical-Bayes shrinkage toward tier prior
(`coaching/shrinkage.py`) → reported with 80% credible intervals. Only metrics passing
meta-analytics gates are displayed.
