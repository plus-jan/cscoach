# ROADMAP (research-driven)

The **route** from CSDS data to coaching feedback is a *working hypothesis*
(docs/specs/01_architecture.md), not a fixed plan. The **invariants** do not change with results:
- the data policy (ADR-0003);
- the accuracy rules and evidence standard (CLAUDE.md);
- the release gate (docs/ASSUMPTIONS.md).

The roadmap therefore has three parts:

1. **Part A — Committed horizon:** tasks that are worth doing whatever later results show. Execute them
   in dependency order.
2. **Part B — Decision points (D1–D5):** where results choose the next branch. Each decision is recorded
   in `docs/FINDINGS.md`, plus an ADR if the architecture changes.
3. **Part C — Provisional backlog:** plausible later work from the current hypothesis. It is **not
   committed**. At each decision point the skill `plan-next-step` re-ranks the backlog, drops or
   rewrites items, and moves the next batch into Part A (with user approval).

Status: `[ ]` todo · `[~]` partial (see note) · `[x]` done · `[-]` dropped (a decision made it
unnecessary; keep the entry and cite the finding).
Each task: **ID — title** · deps · **DoD** · refs (`[paper]`, `[A-NN]`). Implementation happens in the
code repository; results are reported back here (CLAUDE.md, "How to work"). "Passes gates" means the
validation report shows all gates in `docs/specs/06_parameters.md` green.
IDs are stable. Tasks keep their ID when they move between parts.
Measurable implementation work may run in autoresearch loops only under
`docs/specs/07_autoresearch_protocol.md`; its §7 maps task types to commands. Exploration, verification
experiments and decisions never run as loops.

---

# Part A — Committed horizon

These tasks are needed under every branch: data access, trustworthy round/state tables, an honest
picture of the data, a calibrated WP backbone, and the experiments that decide D1–D4.

## M0 — Knowledge base (this repository)

- [x] **M0.1 — Specs, roadmap, agent manual, skills.**
- [~] **M0.2 — Research sources verified** (15 papers + HLTV notes + CSDS spec; only DxT missing; see
  `docs/research/papers/README.md`). The remaining PDF is requested from the user.
- [x] **M0.3 — Assumptions register** (`docs/assumptions.yaml`) + parameter spec (`docs/specs/06`).
- [x] **M0.4 — CSDS corpus documented** (`docs/data/`, ADR-0003/0005).
- [x] **M0.5 — Research-driven planning:** decision points, findings log, `plan-next-step` skill
  (ADR-0006).
- [~] **M0.6 — Migrate to the autoresearch fork** (ADR-0007). Done: loop protocol
  (docs/specs/07), `scripts/kbcheck.py` + CI, skills updated, migration script
  `scripts/migrate_to_autoresearch_fork.sh` and `scripts/sync_upstream.sh` (dry-run tested against
  upstream v2.2.2: both histories merged, kbcheck and all four upstream test suites green). Open: the user forks
  `uditgoenka/autoresearch` (e.g. as `plus-jan/cscoach`) and grants this project access; then run the
  script, open a PR on the fork, and point this repository's README to the fork.
  **DoD:** fork contains both histories; `scripts/kbcheck.py` and upstream CI green; hooks enabled.

## M1 — Data access (CSDS via official libraries)

- [ ] **M1.1 — Access & license.** The user subscribes to the ADX product and sets up AWS credentials.
  Confirm that the DSA terms fit the project [A-38] and record the decision in an ADR.
  **DoD:** one revision exported; license ADR.
- [ ] **M1.2 — Export & collection layout.** Export revisions in ≤ 1-month batches with
  `pureskillgg_dsdk` (telemetry channels only where needed, costs logged). Keep an export manifest
  (revision ids, dates, channel-set version, `ppp_version`).
  **DoD:** reproducible export script in the code repo; manifest.
- [ ] **M1.3 — Header tome, dedup, quality.** `create_header_tome`; dedup on header-derived keys
  [A-36]; quality flags (missing round_end, warmup leftovers, missing ticks, abandonment) [A-40];
  subheader tomes by platform / rank availability / channel set / date.
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
- [ ] **M2.5 — Gated loop harness** (docs/specs/07 §2). deps: M2.2 (leakage test). Loops on CSDS start only after MV.14.
  `cscoach.loops.gated_verify` (prints the budget-corrected CI lower bound of the improvement vs the
  champion on match-grouped out-of-fold predictions, training matches only) and `cscoach.loops.guard`
  (tests, leakage, split integrity, sealed folds untouched, per-stratum calibration gates) [A-42].
  **DoD:** unit tests incl. "sealed fold read → failure"; a synthetic end-to-end loop run (A-33).

## E — Exploration (let the data propose hypotheses)

Descriptive, pre-registered where possible, with cluster-bootstrap CIs. Each result goes into
`docs/FINDINGS.md`, and new hypotheses go into `docs/assumptions.yaml`.

- [ ] **E.1 — Anatomy of lost rounds per tier.** deps: M2.1, M1.4.
  How are rounds lost (elimination, bomb, time), after which state transitions (first death, man
  disadvantage, failed retake, eco loss), and how does this differ by tier, platform, map and side?
  **DoD:** a transition table per tier with CIs; finding(s).
- [ ] **E.2 — What separates tiers.** deps: M2.3, M1.4.
  Compare tiers on behaviours measurable in CSDS: trades and trade timing, first-contact timing, utility
  use per round, buy patterns and desync, positions (`place_name` occupancy), duel mechanics (speed at
  shot, crosshair offset), and conversion of man advantage. Use effect sizes with CIs and within-match
  variability. **DoD:** a ranked list of differences; finding(s); new assumptions where warranted.
- [ ] **E.3 — What separates won from lost rounds *within* a tier.** deps: M2.3.
  The same behaviour set, conditioned on round state (economy, side, map), so we know what matters at
  each level, independent of the tier comparison. **DoD:** ranked associations with CIs (explicitly
  not causal).
- [ ] **E.4 — Opportunity sizing.** deps: E.1–E.3.
  A rough estimate per candidate feedback area (economy, duels, trades/positioning, utility, rotations):
  how often it occurs × the typical round-outcome difference × how feasibly CSDS measures it. It is an
  input to D3. **DoD:** an opportunity table with uncertainty; finding.
- [ ] **E.5 — Hypothesis intake.** deps: E.1–E.4.
  Turn the exploration results into new or refined assumptions (A-NN) and candidate backlog items.
  **DoD:** register and backlog updated.

## M3 — Win Probability v1 (backbone; needed under every branch)

- [ ] **M3.1 — Baseline WP** on CSDS; reference metrics per tier/platform/map, reported next to the pro CS:GO
  benchmark in [xenopoulos_valuing_actions_csgo] (log-loss 0.535 XGBoost / 0.692 map-only).
- [ ] **M3.2 — GBDT WP** (monotone, tier/platform features, rank-prior features via ablation), with
  hyperparameters tuned by grouped CV [A-29]. Refs: [pandaskill], [xenopoulos_pro_vs_amateur_wp].
- [ ] **M3.3 — Calibration layer** per tier/platform [A-28].
- [ ] **M3.4 — WP validation report** (docs/specs/04 §2, incl. the temporal split by `build_num`).
  **DoD:** passes gates.

## MV — Verification experiments that feed decisions

- [ ] **MV.1 — Game rules & decoding on CSDS.**
  deps: M2.1. Refs: [A-13, A-14, A-15, A-16, A-39].
  Reconcile the economy engine against `player_status.money` per `build_num`/platform (target ≥ 99% of
  player-rounds). Locate the Aug 2025 economy change [hltv_rating_3] and version the rules by build.
  Measure round/bomb/freeze timers from phase durations. Decode `team_code`, `win_reason_code`,
  `weapon_code`, `hit_box_code` and `site_code`. Check the tick rate, the staleness of as-of merges, and
  **tick coverage and gaps per match** (independent report of possible drops:
  [learning_to_move_like_pros]). Compare the v30 and v42 channel sets.
  **DoD:** decoding tables committed to `docs/data/`; parameters and statuses updated.
- [ ] **MV.2 — Tier label validity & corpus composition.** → feeds **D1**.
  deps: M1.4. Refs: [A-11, A-12, A-15, A-34].
  Rank scales per platform/`rank_type`, lobby spread, and coverage of rank data. Check that the tiers
  differ in play (together with E.2). Describe how the corpus compares with the expected population.
  **DoD:** tier cut-offs revised or confirmed (ADR); corpus-bias note.
- [ ] **MV.3 — Tier hypothesis.** → decides **D1**.
  deps: M3.1–M3.3. Refs: [A-01], [xenopoulos_pro_vs_amateur_wp] (prior result to replicate: ΔECE ≈ +0.02
  for a transfer across skill environments), [champ_matchmaking].
  Fit WP on one tier/platform and evaluate calibration on the others. Compare pooled, tier-conditioned
  and per-tier models, with cluster-bootstrap CIs.
  **DoD:** A-01 supported/refuted; D1 decided.
- [ ] **MV.4 — Uncertainty method coverage.** → feeds **D4**.
  deps: M2.3 (CSDS state tables), M3.1. Refs: [A-10, A-24], [brill_yurko_wp_difficulty].
  1. Build a **CS round simulator fitted to CSDS**: a state-space model of kill and plant transitions
     depending on alive counts, HP, equipment, time and bomb, per tier. Its true WP is known by
     simulation.
  2. Generate datasets shaped like CSDS.
  3. Measure the coverage and width of the model-uncertainty intervals: standard, cluster, randomized
     cluster and fractional (φ grid) bootstraps. Measure the coverage of the test-metric CIs.
  4. Estimate the accuracy-based ESS and compare it with the Kish ESS.
  **DoD:** φ and B chosen for nominal coverage (ADR); coverage per WP bin reported.
- [ ] **MV.5 — Derive gates and minimum sizes (policy).** → feeds **D4**.
  deps: MV.4, M3.1. Refs: [A-06, A-07, A-08, A-09, A-32].
  Error propagation: how much ECE shifts WPA/feedback rankings. Plot reliability vs. rounds per player
  within a match and stability vs. rounds per stratum.
  **DoD:** gate values decided in an ADR; `docs/specs/06` updated.
- [ ] **MV.7 — Model structure checks.**
  deps: M3.2–M3.3. Refs: [A-27, A-28].
  Constrained vs. unconstrained GBDT (partial dependence, log-loss, ECE); calibration-method comparison
  per fold size. **DoD:** ADR.
- [ ] **MV.10 — Counterfactual validity of WP.** → decides **D2**.
  deps: M3.4. Refs: [A-04, A-05], [play_like_champions].
  Test WP on "near-twin" states that differ by one decision (duel taken vs. avoided, save vs. buy,
  utility used vs. held; matched on the other features). Do observed outcome differences match the
  model's ΔWP, per decision type? Also check sensitivity to features that don't cause outcomes.
  **DoD:** A-04 status per decision type; D2 decided.

- [ ] **MV.14 — False-keep rate of the gated loop.**
  deps: M2.5. Refs: [A-42], [brill_yurko_wp_difficulty].
  Simulation with known truth (A-33 permits this: it tests a method property, not a CS2 fact): run the
  loop with (a) only no-effect variants and (b) variants with a planted improvement, at the match counts
  and cluster sizes of the CSDS training split. Measure the loop-level false-keep rate and the power;
  compare the budget-corrected level with the uncorrected one.
  **DoD:** A-42 supported/refuted; `loop.*` parameters confirmed or changed (docs/specs/06).

---

# Part B — Decision points

Each decision is taken with the `plan-next-step` skill:
1. read the inputs;
2. choose a branch;
3. record the finding (F-NN) and, if the architecture changes, an ADR;
4. update the specs and the register;
5. move the chosen backlog items into Part A, after user approval.

Branches are the currently foreseen options. A result may justify a new one.

### D1 — Tier structure
- **Trigger/inputs:** MV.2, MV.3, E.2.
- **Question:** do tiers (and platforms) need separate treatment, and in what form?
- **Branches:**
  - **D1-a** A-01 supported, conditioning suffices → keep one tier/platform-conditioned WP with
    per-tier calibration (ADR-0002 confirmed).
  - **D1-b** Strong interactions (conditioning fails the per-tier gates) → per-tier or
    hierarchical/partially pooled models; tier-specific xK and priors.
  - **D1-c** No meaningful difference → drop tier from the models (keep it only for reporting); the
    feedback baselines become corpus-wide.
  - **D1-d** Tier labels unusable (MV.2) → use a proxy skill measure from behaviour (E.2) or
    platform-only stratification; revisit A-11/A-12.

### D2 — What kind of feedback is valid
- **Trigger/inputs:** MV.10, M3.4.
- **Question:** can the WP model evaluate alternative decisions?
- **Branches:**
  - **D2-a** Valid for the tested decision types → counterfactual coaching as specified
    (docs/specs/05); activate M5 and M9.2 for those types.
  - **D2-b** Valid only for some decision types → restrict counterfactual feedback to them; the rest
    use benchmark mode.
  - **D2-c** Not valid → **benchmark mode only**: compare a player's decisions and outcomes with those
    of players of the same tier in similar situations (docs/specs/05, "Benchmark mode"), with no "what
    if" claims. WPA is still shown as a *descriptive* round-swing timeline, not as a causal value.
    Drop M9.2 and M5.4.

### D3 — What to build next
- **Trigger/inputs:** E.4, D1, D2, open assumptions.
- **Question:** which analysis module gives the most coaching value per unit of effort and risk?
- **Candidates:** economy (M6), duels (M4), trades/positioning and spatial (M7), action credit (M5),
  utility (M7.3).
- **Rule:** rank by opportunity (E.4) × measurability in CSDS × probability that the blocking
  assumptions hold, ÷ effort. Commit to at most two modules.
- **Output:** the next Part A batch.

### D4 — Granularity of player-level output
- **Trigger/inputs:** MV.4, MV.5, first MV.9 results.
- **Question:** are per-player, per-match estimates precise enough to show?
- **Branches:**
  - **D4-a** Yes → player metrics as specified (M8).
  - **D4-b** Only for high-volume quantities → show per-player values for those; everything else at
    team level or as "patterns over the match".
  - **D4-c** No → no per-player numbers; feedback cites situations and team-level metrics only. The
    `player_metrics` capability stays blocked.

### D5 — Ship, iterate or stop a feedback type
- **Trigger/inputs:** the first detectors (M9.1), expert review (M9.5).
- **Question:** is a feedback category correct and useful enough?
- **Branches:**
  - **D5-a** Meets the target → keep it; move to product surface (M10).
  - **D5-b** Fixable → iterate the detector or wording; re-review.
  - **D5-c** Not useful or not correct → drop the category and record why.

---

# Part C — Provisional backlog (not committed; re-planned at each decision)

Items carry the decision(s) that would activate, change or drop them. Details may change completely.

## M3 (extension)
- [ ] **M3.5 — Sequence/set-model challenger (optional)**; promoted only by protocol. *Activation:* if
  M3.4 misses the gates or D1-b applies.

## M4 — Expected Kills (duel model) · *activation: D3*
- [ ] **M4.1 — Duel extraction** from CSDS events [A-19]. Refs: [same_player_verification_cs2].
- [ ] **M4.2 — Pre-duel features** incl. counter-strafe from `player_inputs` [A-20, A-39].
- [ ] **M4.3 — xK model + calibration.** **DoD:** passes xK gates.
- [ ] **M4.4 — Execution vs decision decomposition** (within match, shrunk). *Needs D4-a/b.*

## M5 — WPA & credit assignment · *activation: D2-a/b (causal use) or D2-c (descriptive timeline only), and D3*
- [ ] **M5.1 — Event WPA** [A-18].
- [ ] **M5.2 — Attribution rules** incl. damage events, victim-negative credit, the round-end residual,
  trades [A-17] and eco adjustment via xK [A-23]. Refs: [xenopoulos_valuing_actions_csgo], [hltv_rating_3].
- [ ] **M5.3 — Shapley credit.** **DoD:** tests for efficiency, symmetry and the null player, plus the
  WPA telescoping test (docs/specs/04 §7). Refs: [tar2_credit_assignment].
- [ ] **M5.4 — xK × WPA decision matrix** [A-05]. *Dropped under D2-c.*

## M6 — Economy · *activation: D3*
- [ ] **M6.1 — Rules engine** (verified in MV.1) [A-13].
- [ ] **M6.2 — Buy classification**, player-level and team-level [A-21].
- [ ] **M6.3 — Game-level WP + Optimal Spending Error + team sync** (docs/specs/03#economy).
  Refs: [xenopoulos_optimal_economy]. **DoD:** gwp passes its calibration gate; OSE per team-match
  with CIs; desync cost per player. *Counterfactual use needs D2-a/b; otherwise benchmark mode.*

## M7 — Spatial analytics (CSDS-only) · *activation: D3*
- [ ] **M7.1 — Empirical area graph** per map from `place_name` + `player_vector` [A-37].
- [ ] **M7.2 — Area-control features** (must win an ablation on WP *outcome* log-loss). Refs:
  [valorant_round_outcome_tactical], [contextual_xt_spatial] (transition gains ≠ outcome gains).
- [ ] **M7.3 — Utility delay** from `grenade_*`/`molotov_*` on the area graph.
- [ ] **M7.4 — Off-ball/spatial credit.** Refs: [dynamic_xt].

## M8 — Player-level metrics (within match) · *activation: D4-a/b*
- [ ] **M8.1 — Shrinkage toward the tier prior** [A-26]. Refs: [pandaskill].
- [ ] **M8.2 — Reliability/discrimination/independence report** per metric [A-08, A-25].
- [ ] **M8.3 — Minimum-data rules** (ESS per player in a match) [A-07].

## MV — Later verification (activated with the modules they check)
- [ ] **MV.6 — Windows & thresholds from data.** deps: M2.3 (+ duels M4.1). Refs: [A-17, A-18, A-19,
  A-20, A-21, A-22]. Empirical trade-time distribution; sensitivity of WPA to the pre/post offsets; duel
  resolution times and the censoring rate; per-weapon speed at the first accurate shot; buy-value
  clusters; sensitivity of WP to the snapshot cadence. **DoD:** parameters with CIs; statuses updated.
- [ ] **MV.8 — Shrinkage model fit.** deps: M8 inputs. Refs: [A-26]. Distribution of per-round values;
  posterior predictive checks; alternatives (Student-t, beta-binomial). **DoD:** chosen model (ADR).
- [ ] **MV.9 — Meta-analytics fidelity.** deps: M8 inputs, MV.4 simulator. Refs: [A-25],
  [franks_meta_analytics]. Implement D, S (match halves) and I (Gaussian copula) as in
  docs/specs/04 §4/§7; check them on simulated players with known effects; compute them per candidate
  metric and tier. **DoD:** A-25 status; metrics passing the gates. → feeds **D4**.
- [ ] **MV.11 — Credit split.** deps: M5.1. Refs: [A-23], [hltv_rating_3]. Compare the fixed split,
  Shapley and a damage-share split: rank stability and within-match reliability.
- [ ] **MV.12 — Tier-specific drivers ("chaos factor").** deps: MV.3, M4.3. Refs: [A-02]. Feature
  importance / SHAP per tier, with CIs. (E.2/E.3 give an early descriptive answer.)
- [ ] **MV.13 — Area graph adequacy.** deps: M7.1. Refs: [A-37]. Predict observed rotation and trade
  times from the area graph; compare with held-out trajectories.

## M9 — Coaching engine · *activation: after D2 and D3; mode per D2*
- [ ] **M9.1 — Mistake detectors** for the modules chosen in D3 (docs/specs/05); region-based
  definitions as in [learning_to_move_like_pros]. → feeds **D5**.
- [ ] **M9.2 — Counterfactual recourse** (limited to the decision types D2 allows) [A-04]: only actionable
  decision variables, on-manifold, minimum viable change. Refs: [play_like_champions]. *Dropped under D2-c.*
- [ ] **M9.3 — Prioritisation** [A-30]. Refs: [gig_economy_esports_coaching].
- [ ] **M9.4 — Narrative rendering + grounding check** [A-31].
- [ ] **M9.5 — Expert review:** coaches rate ≥ 50 feedback items drawn from CSDS matches. The target is
  set in MV.5 [A-03, A-05, A-30, A-31]. → decides **D5**.

## M10 — Product surface · *activation: D5-a for at least one feedback category*
- [ ] **M10.1 — End-to-end per-match analysis** (CSDS match → JSON report) with the assumption gate.
- [ ] **M10.2 — Report/API service.**
- [ ] **M10.3 — UI:** WP timeline, duel map, economy, focus points, coach export, attribution notice.
- [ ] **M10.4 — Performance** [A-32].

## M11 — Evaluation study · *activation: after M10; needs an ADR on a consented data route*
- [ ] **M11.1 — Prospective study design** for the effect of feedback [A-03]. Needs a data route with
  consent and identity beyond CSDS → ADR first (ADR-0003 constrains this).
- [ ] **M11.2 — Monitoring:** drift per `build_num`/revision month, recalibration triggers.
