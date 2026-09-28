# ROADMAP

Status: `[ ]` todo · `[~]` partial (see note) · `[x]` done.
Each task: **ID — title** · deps · **DoD** (Definition of Done) · refs (`[paper]`, `[A-NN]`).
A task is startable when its deps are `[x]`. Implementation happens in the code repository. Results
are reported back here (CLAUDE.md, "How to work"). The gate values are in `docs/specs/06_parameters.md`;
"passes gates" means that the validation report shows all gates green.

Order of milestones: **M0 → M1 → M2 → MV (early verification) → M3 → …** The MV tasks run as soon as
their deps exist. MV.3 and MV.10 decide whether the architecture holds; don't build M5+ on them while
they are open.

---

## M0 — Knowledge base (this repository)

- [x] **M0.1 — Specs, roadmap, agent manual, skills.**
- [~] **M0.2 — Research sources verified** (15 papers + HLTV notes + CSDS spec; only DxT missing; see `docs/research/papers/README.md`).
  Remaining PDFs are requested from the user.
- [x] **M0.3 — Assumptions register** (`docs/assumptions.yaml`) + parameter spec (`docs/specs/06`).
- [x] **M0.4 — CSDS corpus documented** (`docs/data/`, ADR-0003/0005).

## M1 — Data access (CSDS via official libraries)

- [ ] **M1.1 — Access & license.** The user subscribes to the ADX product and sets up AWS credentials.
  Confirm that the DSA terms fit the project [A-38] and record the decision in an ADR.
  **DoD:** one revision exported; license ADR.
- [ ] **M1.2 — Export & collection layout.** Export revisions in ≤ 1-month batches with
  `pureskillgg_dsdk` (telemetry channels only where needed, costs logged). Keep an export manifest
  (revision ids, dates, channel-set version, `ppp_version`).
  **DoD:** reproducible export script in the code repo; manifest.
- [ ] **M1.3 — Header tome, dedup, quality.** `create_header_tome`; dedup on header-derived keys
  [A-36]; quality flags (missing round_end, warmup leftovers, missing ticks) [A-40]; subheader tomes by
  platform / rank availability / channel set / date.
  **DoD:** counts per platform × map × month × channel set in PROGRESS.
- [ ] **M1.4 — Tier labels.** Decode `player_info` rank fields per platform (with MV.2) → match tier +
  spread [A-11, A-12, A-15]. **DoD:** tier coverage table; unknowns are null, never guessed.
- [ ] **M1.5 — Data volume check** against the target [A-32]. **DoD:** gap analysis per stratum.

## M2 — Round reconstruction & snapshots

- [ ] **M2.1 — Rounds** from `round_start/round_end/round_state/tick`: phases, warmup, overtime
  (`pop_overtime(max_rounds_csgo=24)`), side mapping [A-15].
  **DoD:** round winners match the final scores in `header` for ≥ 99.5% of matches.
- [ ] **M2.2 — Snapshot sampler** (event ticks + cadence [A-22]); as-of join of `player_status` ≤ tick.
  **DoD:** leakage test (removing future rows changes nothing).
- [ ] **M2.3 — State features v1** (docs/specs/02). **DoD:** leakage denylist test; feature
  distributions per tier/platform in PROGRESS.
- [ ] **M2.4 — Leakage audit:** no single feature reaches AUC > 0.99 for the label at freeze end.

## MV — Empirical verification of assumptions (run early; results update `docs/assumptions.yaml`)

- [ ] **MV.1 — Game rules & decoding on CSDS.**
  deps: M2.1. Refs: [A-13, A-14, A-15, A-16, A-39].
  Reconcile the economy engine against `player_status.money` per `build_num`/platform (target ≥ 99% of
  player-rounds). Locate the Aug 2025 economy change [hltv_rating_3] and version the rules by build. Measure round/bomb/freeze timers from phase durations. Decode `team_code`,
  `win_reason_code`, `weapon_code`, `hit_box_code` and `site_code`. Check the tick rate, the staleness of as-of merges, and **tick coverage and gaps per match** (independent
  report of possible drops: [learning_to_move_like_pros]). Compare the v30 and v42 channel sets.
  **DoD:** decoding tables committed to `docs/data/`; parameters and statuses updated.
- [ ] **MV.2 — Tier label validity & corpus composition.**
  deps: M1.4. Refs: [A-11, A-12, A-15, A-34].
  Rank scales per platform/`rank_type`, lobby spread, and coverage of rank data. Check that the tiers
  differ in play (e.g. K/D, ADR, duel win rates, man-advantage conversion). Describe how the corpus
  compares with the expected population.
  **DoD:** tier cut-offs revised or confirmed (ADR); corpus-bias note.
- [ ] **MV.3 — Tier hypothesis (architecture-deciding).**
  deps: M3.1–M3.3. Refs: [A-01], [xenopoulos_pro_vs_amateur_wp] (prior result to replicate: ΔECE ≈ +0.02
  for a pro→amateur transfer), [champ_matchmaking].
  Fit WP on one tier/platform and evaluate calibration on the others. Compare against pooled,
  tier-conditioned and per-tier models, with cluster-bootstrap CIs.
  **DoD:** A-01 supported/refuted; ADR-0002 confirmed or replaced.
- [ ] **MV.4 — Uncertainty method coverage.**
  deps: M2.3 (CSDS state tables), M3.1. Refs: [A-10, A-24], [brill_yurko_wp_difficulty].
  1. Build a **CS round simulator fitted to CSDS**: a state-space model of kill and plant transitions
     depending on alive counts, HP, equipment, time and bomb, per tier. Its true WP is known by
     simulation.
  2. Generate datasets shaped like CSDS (same number of matches, rounds and snapshots).
  3. Measure the coverage and width of the model-uncertainty intervals: standard, cluster, randomized
     cluster and fractional (φ grid) bootstraps. Measure the coverage of the test-metric CIs.
  4. Estimate the accuracy-based ESS, and compare it with the Kish ESS.
  **DoD:** φ and B chosen for nominal coverage (ADR); coverage per WP bin reported (the paper found
  undercoverage near WP 0.3/0.7).
- [ ] **MV.5 — Derive gates and minimum sizes (policy).**
  deps: MV.4, M3.1. Refs: [A-06, A-07, A-08, A-09, A-32].
  Error propagation: how much ECE shifts WPA/feedback rankings. Plot reliability vs. rounds per player
  within a match and stability vs. rounds per stratum.
  **DoD:** gate values decided in an ADR; `docs/specs/06` updated.
- [ ] **MV.6 — Windows & thresholds from data.**
  deps: M2.3 (+ duels M4.1). Refs: [A-17, A-18, A-19, A-20, A-21, A-22].
  Empirical trade-time distribution; sensitivity of WPA to the pre/post offsets; duel resolution times
  and the censoring rate; per-weapon speed at the first accurate shot (`player_inputs`, `speed_2d`,
  `inaccuracy`); buy-value clusters; sensitivity of WP to the snapshot cadence.
  **DoD:** parameters estimated with CIs; statuses updated.
- [ ] **MV.7 — Model structure checks.**
  deps: M3.2–M3.3. Refs: [A-27, A-28].
  Constrained vs. unconstrained GBDT (partial dependence, log-loss, ECE); calibration-method comparison
  per fold size. **DoD:** ADR.
- [ ] **MV.8 — Shrinkage model fit.**
  deps: M8 inputs. Refs: [A-26].
  Distribution of per-round WPA; posterior predictive checks; alternatives (Student-t, beta-binomial).
  **DoD:** chosen model (ADR).
- [ ] **MV.9 — Meta-analytics fidelity.**
  deps: M8 inputs, MV.4 simulator. Refs: [A-25], [franks_meta_analytics] (full text available).
  Implement D, S (match halves) and I (Gaussian copula) as in docs/specs/04 §4/§7. Check them on
  simulated players with known effects, then compute them for the candidate metrics per tier.
  **DoD:** A-25 status; list of metrics passing the gates.
- [ ] **MV.10 — Counterfactual validity of WP (architecture-deciding).**
  deps: M3.4. Refs: [A-04, A-05].
  Test WP on "near-twin" states that differ by one action (e.g. duel taken vs. avoided, matched on the
  other features). Do the observed outcome differences match the model's ΔWP? Also check sensitivity to
  features that don't cause outcomes, and stability of the credit assignment.
  **DoD:** A-04 status with evidence; limits on which counterfactual types may be shown.
- [ ] **MV.11 — Credit split.** deps: M5.1. Refs: [A-23], [hltv_rating_3].
  Compare the fixed split with Shapley credit and a damage-share split: rank stability and within-match reliability.
- [ ] **MV.12 — Tier-specific drivers ("chaos factor").** deps: MV.3, M4.3. Refs: [A-02].
  Compare feature importance / SHAP per tier (counter-strafe, utility, positioning), with CIs.
- [ ] **MV.13 — Area graph adequacy.** deps: M7.1. Refs: [A-37].
  Predict observed rotation and trade times from the area graph; compare with held-out trajectories.

## M3 — Win Probability v1 (the backbone)

- [ ] **M3.1 — Baseline WP** on CSDS; reference metrics per tier/platform/map, reported next to the pro CS:GO
  benchmark in [xenopoulos_valuing_actions_csgo] (log-loss 0.535 XGBoost / 0.692 map-only).
- [ ] **M3.2 — GBDT WP** (monotone, tier/platform features, rank-prior features via ablation), with
  hyperparameters tuned by grouped CV [A-29]. Refs: [pandaskill].
- [ ] **M3.3 — Calibration layer** per tier/platform [A-28].
- [ ] **M3.4 — WP validation report** (docs/specs/04 §2, incl. the temporal split by `build_num`).
  **DoD:** passes gates.
- [ ] **M3.5 — Sequence/set-model challenger (optional)**; promoted only by protocol.

## M4 — Expected Kills (duel model)

- [ ] **M4.1 — Duel extraction** from CSDS events [A-19]. Refs: [same_player_verification_cs2].
- [ ] **M4.2 — Pre-duel features** incl. counter-strafe from `player_inputs` [A-20, A-39].
- [ ] **M4.3 — xK model + calibration.** **DoD:** passes xK gates.
- [ ] **M4.4 — Execution vs decision decomposition** (within match, shrunk).

## M5 — WPA & credit assignment (requires MV.10 not refuted)

- [ ] **M5.1 — Event WPA** [A-18].
- [ ] **M5.2 — Attribution rules** incl. damage events, victim-negative credit, the round-end residual,
  trades [A-17] and eco adjustment via xK [A-23]. Refs: [xenopoulos_valuing_actions_csgo], [hltv_rating_3].
- [ ] **M5.3 — Shapley credit.** **DoD:** tests for efficiency, symmetry and the null player, plus the
  WPA telescoping test (docs/specs/04 §7). Refs: [tar2_credit_assignment].
- [ ] **M5.4 — xK × WPA decision matrix** [A-05].

## M6 — Economy

- [ ] **M6.1 — Rules engine** (verified in MV.1) [A-13].
- [ ] **M6.2 — Buy classification**, player-level and team-level [A-21].
- [ ] **M6.3 — Game-level WP + Optimal Spending Error + team sync** (docs/specs/03#economy).
  Refs: [xenopoulos_optimal_economy]. **DoD:** gwp passes its calibration gate; OSE per team-match
  with CIs; desync cost per player.

## M7 — Spatial analytics (CSDS-only)

- [ ] **M7.1 — Empirical area graph** per map from `place_name` + `player_vector` [A-37].
- [ ] **M7.2 — Area-control features** (must win an ablation on WP *outcome* log-loss). Refs:
  [valorant_round_outcome_tactical], [contextual_xt_spatial] (transition gains ≠ outcome gains).
- [ ] **M7.3 — Utility delay** from `grenade_*`/`molotov_*` on the area graph.
- [ ] **M7.4 — Off-ball/spatial credit.** Refs: [dynamic_xt].

## M8 — Player-level metrics (within match)

- [ ] **M8.1 — Shrinkage toward the tier prior** [A-26]. Refs: [pandaskill].
- [ ] **M8.2 — Reliability/discrimination/independence report** per metric [A-08, A-25].
- [ ] **M8.3 — Minimum-data rules** (ESS per player in a match) [A-07].

## M9 — Coaching engine

- [ ] **M9.1 — Mistake detectors** (docs/specs/05); region-based definitions as in [learning_to_move_like_pros].
- [ ] **M9.2 — Counterfactual recourse** (limited to the types MV.10 allows) [A-04]: only actionable
  decision variables, on-manifold, minimum viable change (docs/specs/05). Refs: [play_like_champions].
- [ ] **M9.3 — Prioritisation** [A-30]. Refs: [gig_economy_esports_coaching].
- [ ] **M9.4 — Narrative rendering + grounding check** [A-31].
- [ ] **M9.5 — Expert review:** coaches rate ≥ 50 feedback items drawn from CSDS matches. The target
  is set in MV.5 [A-03, A-05, A-30, A-31].

## M10 — Product surface

- [ ] **M10.1 — End-to-end per-match analysis** (CSDS match → JSON report) with the assumption gate.
- [ ] **M10.2 — Report/API service.**
- [ ] **M10.3 — UI:** WP timeline, duel map, economy, focus points, coach export, attribution notice.
- [ ] **M10.4 — Performance** [A-32].

## M11 — Evaluation study

- [ ] **M11.1 — Prospective study design** for the effect of feedback [A-03]. Needs a data route with
  consent and identity beyond CSDS → ADR first (ADR-0003 constrains this).
- [ ] **M11.2 — Monitoring:** drift per `build_num`/revision month, recalibration triggers.
