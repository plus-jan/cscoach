# 03 — Models

All inputs come from CSDS (docs/specs/02). Parameter values are in docs/specs/06 with assumption IDs.

## Tiers {#tiers}

Tier labels come only from CSDS:
- `player_info.rank` / `rank_type` / `rank_raw` / `rank_platform` (per player-round);
- `header.{ct,t}_starters_avg_rank`;
- `header.platform` / `match_type`.

The encoding of `rank_type` and the rank scales per platform are **undocumented**: derive them
empirically in MV.2 (A-11, A-15). Canonical tiers: `low`, `mid`, `high`, `semipro`. The initial cut-offs
are in docs/specs/06; revise them after MV.2. A match tier = aggregate of known player tiers (A-12). It is
null when too few players have ranks (e.g. old FACEIT matches). Always keep `platform` as a separate
conditioning variable, because MM and FACEIT scales are not comparable.

Refs: [champ_matchmaking] (condition on domain; naive pooling hurts), [same_player_verification_cs2]
(pro data didn't help an amateur model). [xenopoulos_pro_vs_amateur_wp] is the most direct evidence
(pro vs amateur WP; pro-trained WP was miscalibrated on PureSkill amateur MM: ECE 0.023 vs 0.004 in-domain,
CS:GO 2021, no CIs).

## WP — round win probability

**Target:** `y_ct_win` of the snapshot's round. **Unit:** a snapshot at tick *t*; features use data with
tick ≤ *t* only.

**Features v1** (from `player_status`, `bomb_*`): alive, HP, armor, helmets, kits, equipment value,
weapon-class and utility counts per side, `bomb_planted`, bomb site, `time_remaining_s`,
`man_advantage`, `tier`, `platform`, `map_name`.
**Skill-prior features (candidate, must win an ablation):** the mean rank of each side's alive
players and the rank difference (`player_info` at round start, known before the round). In
[xenopoulos_pro_vs_amateur_wp] these shifted WP much more in amateur MM (r = 0.59) than in near-pro
FPL (r = 0.13), especially when equipment/HP were balanced.
Implemented as `ct_rank_alive`, `t_rank_alive`, `rank_diff_alive` in tier units (docs/specs/02, A-48); no monotone
constraint (a direction conditional on equipment and tier is not established).

**Features v2** (spatial, M7, must win an ablation): area control share and distance to sites on
the empirical `area_graph`, spotted counts (`is_spotted`), active smokes/mollies on key edges,
defuser-to-bomb distance.

**Models**
1. `baseline_wp`: logistic regression on alive_ct, alive_t, hp_sum_ct, hp_sum_t, bomb_planted,
   time_remaining_s + interactions (alive diff × planted, time × planted). Reference only.
2. `gbdt_wp`: LightGBM with monotone constraints (A-27): +alive_ct, −alive_t, +hp_ct, −hp_t,
   +equipment_ct, −equipment_t. Early stopping on a grouped validation slice of training matches.
   Refs: [pandaskill] (monotone GBDT + ECE).
3. Calibration layer: global + per-tier (and/or per-platform) isotonic or Platt, fitted on a dedicated
   calibration fold of matches (A-28).
4. Challengers (optional, M3.5): sequence/set models over snapshots; promoted only by protocol.

**Symmetry:** `wp_t = 1 − wp_ct`. Sanity-check a side-swap on mirrored states (CS2 is not side-symmetric).

## xK — expected kills (duel model) {#xk}

**Duel definition (A-19):** a duel starts at the first damage (`player_hurt`/`bullet_damage`) or first
mutual `is_spotted` between two opponents. It resolves when one kills the other within the duel window
(`player_death`); otherwise it is censored.
**Pre-duel features** (at tick_start − ε):
- geometry: distance, height delta, and the view-angle offset of each player's crosshair from the
  opponent (from `phi_ang`/`theta_ang` + positions);
- movement: `speed_2d`, `ang_vel`, `movement_angle_diff`, and counter-strafe state from the
  `player_inputs` button timeline + speed (A-20);
- weapon: `weapon_code`, `inaccuracy`, `recoil_index`, `is_scoped`;
- state: HP/armor/helmet, flash (`flash_duration`, `player_blind`), smoke between the players (`grenade_state`);
- context: peeker vs holder (who moved into line of sight), nearby teammates (trade availability), tier/platform.

Refs: [same_player_verification_cs2] (pre-shot speed drop, crosshair corrections and firing rhythm carry
strong signal; LightGBM ≫ MLP at this scale).
**Output:** P(p1 wins). xK per player = Σ P(win). Execution = kills − xK; decision = the duel choice (see WPA).

## WPA {#wpa}

For an event at tick *t_e*: `wpa_team = WP_team(state after the event) − WP_team(state before)`, with the
pre/post offsets from A-18. Credit is split by fixed shares (A-23) or by Shapley values over
contributors, with value function *v(S)* = WP of the counterfactual state where only the contributors
in S acted. Efficiency: Σ credit = ΔWP. Validity of counterfactual states: A-04, tested in MV.10.
- **Actions:** kills *and* damage events (`player_hurt`), bomb plant/defuse, and utility effects.
- **Victim credit:** the damaged or killed player is credited with −V, as in
  [xenopoulos_valuing_actions_csgo]; the attacker gets +V.
- **Round-end residual:** when a round ends without a final kill (time, bomb explosion, defuse, saving
  survivors), the last ΔWP up to the outcome is shared among contributors (initial rule after HLTV:
  clutcher ×1, players with positive kill credit ×2, defuser ×1, alive at the end ×1; saving players
  take the loss) [hltv_rating_3]. This keeps the telescoping property (docs/specs/04 §7).
- **Economy-adjusted duel value:** a won duel is worth (1 − xK_p1) as execution credit, which replaces
  HLTV-style bucket win rates with our tier-calibrated xK [hltv_rating_3].
- **Uncertainty:** WPA and ΔWP intervals are model-uncertainty CIs (fractional bootstrap,
  docs/specs/04 §2(b)).

Refs: [xenopoulos_valuing_actions_csgo] (the original WPA for CS; notes that it assumes teams of similar
skill → A-01), [hltv_rating_3] (Round Swing), [tar2_credit_assignment] (WP as a potential; telescoping).

## Economy {#economy}

Rules engine from docs/specs/06 (A-13), **verified against `player_status.money`** round by round.

**Game-level WP** (`gwp`), after [xenopoulos_optimal_economy]:
- P(match win | state at round start);
- features: scores, score difference, each side's start equipment, money, buy type, map (one-hot),
  tier/platform, and overtime state;
- outcomes: 3 classes where draws are possible, otherwise binary.

**Buy types (A-21):**
- per player: from the freeze-end equipment value;
- per team: from team start equipment and spend (eco / low / half / hero / full, as defined in the
  source; thresholds re-estimated on CSDS).

**Counterfactual buys:**
- swap the team's buy type or equipment vector and re-evaluate gwp; the best alternative is the "optimal
  buy";
- **Optimal Spending Error** per team-match = mean over rounds of (gwp(chosen) − gwp(optimal))²;
- individual desync = a player's buy class differs from the team's, with the gwp cost of that
  deviation;
- fallback when gwp is not yet validated: the two-round horizon Σ_outcomes P(round outcome) ·
  WP_next-round-start.

Caveat: the buy type is confounded with money and team strength, so the counterfactual validity of
these values is A-04 (MV.10).

## Spatial {#spatial}

No external nav mesh (ADR-0003). The empirical `area_graph` (docs/specs/02) is built from
`place_name` + observed transitions (A-37). Utility delay = the shortest transit time with
smoke/molotov-covered areas removed, minus the time without. It is converted to WPA through the WP
model's sensitivity to time and position features. Refs: [contextual_xt_spatial] (a TAx-style "control above expected"; transition gains did not carry
over to the outcome), [learning_to_move_like_pros] (region-based positioning metrics),
[x_ego_cs] (named areas), [dynamic_xt] (pending).

## Player-level aggregation (within match) {#player}

CSDS has no cross-match identity (ADR-0005). Per-player values are computed **within a match**:
1. raw sums/means of per-round values (WPA, xK diff, buy deviation, …);
2. empirical-Bayes shrinkage toward the **tier prior** estimated across matches (A-26);
3. intervals at the display level (A-30).

Reliability (docs/specs/04 §4) uses odd/even rounds within a match. Discrimination and population-level
stability are measured across matches.
Refs: [pandaskill] (within-lobby "free-for-all" ranking by performance, independent of the team
result — applicable within a match), [franks_meta_analytics] (pending).
