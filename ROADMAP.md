# ROADMAP

Status: `[ ]` todo · `[~]` partial (see note) · `[x]` done.
Each task: **ID — title** · *modules* · deps · **DoD** (Definition of Done).
Work top-down; a task is startable when its deps are `[x]`.

Global acceptance thresholds live in `configs/validation.yaml` — the DoD "passes gates"
means `cscoach validate` exits 0 for that model.

---

## M0 — Foundation (template)

- [x] **M0.1 — Repo scaffold, CLAUDE.md, specs, configs, CI.**
- [x] **M0.2 — Validation core**: metrics (Brier, log-loss, ECE, reliability), grouped
  splits, leakage assertion, ICC/design effect/ESS, cluster bootstrap, meta-analytics
  approximations, gate evaluation. *validation/* · **DoD**: unit tests green.
- [x] **M0.3 — Synthetic round simulator** with tier-dependent "chaos" for tests.
  *synthetic.py*
- [x] **M0.4 — Baseline WP (logistic) + GBDT WP skeleton + per-tier calibration**,
  trained end-to-end on synthetic data in tests.
- [~] **M0.5 — Verify research sources** (5/21 full-text verified — see `docs/research/papers/README.md`; remaining PDFs requested from user): for each entry in
  `docs/research/sources.yaml` confirm existence, authors, numbers; set
  `verified: true|false` and fix/annotate claims in `docs/specs`. Several arXiv IDs and
  numbers in the original synthesis are unconfirmed. **DoD**: no `unverified` entry is
  cited as a design justification in `docs/specs`.

## M1 — Data acquisition & ingestion

- [ ] **M1.1 — demoparser2 wrapper verified on real CS2 demos.** *ingest/demo_parser.py*
  · deps M0 · Obtain ≥3 public demos (e.g. HLTV pro demo + PureSkill + a FACEIT demo),
  confirm field names per demoparser2 version, write parsed parquet to `data/interim/`.
  **DoD**: `tests/integration/test_parse_real_demo.py` (skipped when no demo present)
  passes locally; each output table validates against `schemas`.
- [ ] **M1.2 — PureSkill.gg dataset loader** (amateur, rank-labelled). *ingest/datasets.py*
  **DoD**: loader returns contract-conformant tables + tier label per player/match.
- [ ] **M1.3 — Tier mapping**: map Premier rating / FACEIT level / MM rank / dataset
  labels onto canonical tiers in `configs/tiers.yaml`; team-average + spread per match.
  *ingest/tiers.py* **DoD**: unit tests for every source mapping; unknown → `None`, never guessed.
- [ ] **M1.4 — Data manifest & dedup**: content hash per demo, game build/patch, map,
  source, tier; duplicate detection. *ingest/manifest.py* **DoD**: re-ingest is idempotent.
- [ ] **M1.5 — Data volume target**: ≥ 2,000 matches with ≥ 300 per tier bucket across
  ≥ 5 active-duty maps. Record counts in `docs/PROGRESS.md`. (Collection may be
  manual/user-supplied; write the tooling + document the process in `data/README.md`.)

## M2 — Round reconstruction & state snapshots

- [ ] **M2.1 — Round segmentation**: freeze-end, round-end, winner, reason; drop
  warmup/knife/aborted rounds; handle overtime & side swaps. *preprocess/rounds.py*
  **DoD**: round count and winners match scoreboard on all integration demos.
- [ ] **M2.2 — Snapshot sampler**: event-anchored snapshots (every kill/damage/plant/
  utility) + fixed cadence (e.g. 1 s). *preprocess/snapshots.py* **DoD**: snapshot tick
  ≤ label-free; unit test on synthetic ticks.
- [ ] **M2.3 — State features v1** (per snapshot): alive, HP, armor, helmet, kit,
  equipment value, weapon classes, bomb state/site, time remaining (incl. bomb timer),
  man-advantage, utility inventory. *features/state.py* **DoD**: contract
  `StateFeatures` validates; leakage guard test green.
- [ ] **M2.4 — Leakage audit**: automated check that no feature correlates
  suspiciously (AUC>0.99) with label at round start; denylist test extended.

## M3 — Win Probability v1 (the backbone)

- [ ] **M3.1 — Baseline WP on real data**; record metrics per tier/map as the reference.
- [ ] **M3.2 — GBDT WP** (LightGBM, monotone constraints on alive/HP/equipment,
  tier as feature). Hyperparameter search with *grouped* CV. *models/win_probability.py*
- [ ] **M3.3 — Per-tier calibration** (isotonic or Platt, on a dedicated calibration
  fold). *models/calibration.py* **DoD**: ECE ≤ gate for every tier with ≥ N rounds.
- [ ] **M3.4 — WP validation report**: Brier/log-loss/ECE + reliability diagrams per
  tier × map × round-phase, cluster-bootstrap CIs, lift over baseline, temporal split.
  **DoD**: `cscoach validate --model wp` passes gates; report in `reports/`.
- [ ] **M3.5 — Pro-vs-amateur transfer experiment**: quantify miscalibration of a
  pro-only model on amateur tiers (confirms/refutes research claim A). ADR with result.
  Refs: [champ_matchmaking] (naive pooling hurts), [same_player_verification_cs2] (pro data didn't help).
- [ ] **M3.6 — Sequence model challenger (optional)**: GRU/Transformer over snapshot
  sequence or GNN over positions; adopt only if it beats GBDT on log-loss with CI
  excluding 0 and meets latency budget.

## M4 — Expected Kills (duel model)

- [ ] **M4.1 — Duel extraction**: define an engagement (first damage/visibility between
  two players within window), outcome = who dies/first-kill within Δt. *features/duel.py*
  Spec: `docs/specs/03_models.md#xk`.
- [ ] **M4.2 — Pre-duel features only** (feature ideas: [same_player_verification_cs2] Table I): distance, weapons, armor/HP, movement speed
  (counter-strafe state), view-angle offset to opponent (crosshair placement),
  peeker/holder, flashed state, elevation, number of nearby teammates, tier.
- [ ] **M4.3 — xK model + calibration**, grouped by match. **DoD**: passes xK gates.
- [ ] **M4.4 — Mechanical vs decision decomposition**: kills − xK (execution) vs
  choice of duel (decision), per player with shrinkage.

## M5 — WPA & credit assignment

- [ ] **M5.1 — Event WPA**: ΔWP around each event with configurable pre/post windows.
  *valuation/wpa.py* (core implemented, wire to real events).
- [ ] **M5.2 — Attribution rules**: killer / assister / flash-assister / trade credit
  / damage share; economy adjustment (eco-farming penalty via equipment deltas).
- [ ] **M5.3 — Shapley credit** for multi-contributor sequences (sampling Shapley over
  contributors using the WP model as value function). *valuation/credit.py*
  **DoD**: efficiency axiom test (credits sum to ΔWP) passes.
- [ ] **M5.4 — xK × WPA decision matrix**: flag high-risk low-necessity duels
  (e.g. xK < 0.3 when survival WP > 0.9). *valuation/decisions.py*

## M6 — Economy

- [ ] **M6.1 — Rules engine verified** against real round-by-round money in demos
  (`economy/rules.py`, `configs/economy_cs2.yaml`). **DoD**: predicted start money
  matches demo money for ≥ 99% of player-rounds.
- [ ] **M6.2 — Buy classification** (eco/force/half/full/hero) per player & team.
- [ ] **M6.3 — Team economic synchronisation** metric + counterfactual buy
  evaluation: WP at freeze-end under alternative buy vectors (next-round money
  simulation). *economy/counterfactual.py*

## M7 — Spatial analytics

- [ ] **M7.1 — Map geometry & nav graph** per map (evaluate `awpy` nav meshes /
  map data; ADR on source & license). *spatial/navgraph.py*
- [ ] **M7.2 — Area control features** ([valorant_round_outcome_tactical]: tactical events add signal): team-controlled nav areas, distance-to-site
  shortest paths, add to WP features (ablation must show lift).
- [ ] **M7.3 — Utility delay**: shortest-path delta with smoke/molly edges removed;
  seconds of delay → WPA for thrower. *spatial/utility.py*
- [ ] **M7.4 — Off-ball/spatial credit** (DxT-style): value of holding space.

## M8 — Player-level metrics & statistical validity

- [ ] **M8.1 — Hierarchical shrinkage** (+ evaluate FFA OpenSkill / meta rating from [pandaskill]) (empirical Bayes / beta-binomial & normal-normal)
  toward tier prior. *coaching/shrinkage.py* (normal-normal implemented).
- [ ] **M8.2 — Meta-analytics report** for every player metric (stability,
  discrimination, independence vs K/D, ADR, HLTV-like rating). Metrics failing gates are
  hidden from players.
- [ ] **M8.3 — Minimum-sample rules**: show a metric only when ESS ≥ threshold.

## M9 — Coaching engine

- [ ] **M9.1 — Mistake detectors** (rule + model based): bad duel choice, untraded
  deaths, desynced buys, wasted utility, late rotations. Each outputs evidence rows.
- [ ] **M9.2 — Counterfactual recourse**: for a detected mistake, compute WP under the
  minimal feasible alternative action (hold position, save, delay utility) using the
  WP/economy/spatial models; report ΔWP with CI.
- [ ] **M9.3 — Prioritisation** (recurring patterns, tier benchmarks — [gig_economy_esports_coaching]): rank feedback by expected WPA gain × frequency ×
  confidence; max 3 focus points per match.
- [ ] **M9.4 — Narrative rendering** (templates; optional LLM with strict grounding:
  only engine-provided numbers). *coaching/narrative.py*
- [ ] **M9.5 — Expert review protocol**: coaches rate 50 feedback items; target ≥ 80%
  judged correct & useful. Document in `docs/specs/05_coaching_feedback.md`.

## M10 — Product surface

- [ ] **M10.1 — End-to-end pipeline** `cscoach analyze <demo.dem>` → JSON report.
- [ ] **M10.2 — FastAPI service** + report endpoints. *api/*
- [ ] **M10.3 — Dashboard** (coach-facing export + patch-tagged insights, [gig_economy_esports_coaching]) (WP timeline, duel map, economy chart, focus points).
- [ ] **M10.4 — Performance**: full match analysis < 30 s on 4 cores; WP inference
  < 10 ms per snapshot batch of 1k.

## M11 — Evaluation study

- [ ] **M11.1 — Prospective study design** (RCT: engine feedback vs control, outcome =
  rating change / targeted-metric change over N matches, pre-registered).
- [ ] **M11.2 — Monitoring**: data drift per patch, recalibration triggers.
