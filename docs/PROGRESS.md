# Progress log

Append one line per completed task: `YYYY-MM-DD · task-id · what changed · key numbers · evidence link`.

- 2026-09-28 · (superseded) · A Python prototype (validation core, synthetic generator, baseline/GBDT WP,
  demo parser) was built and then removed by ADR-0004. Its algorithms are preserved in
  docs/specs/04 §7. Synthetic-only results are not evidence (A-33) · git history before this entry
- 2026-09-28 · M0.2 (partial) · 5 papers converted and verified; corrections recorded in paper notes ·
  docs/research/papers/README.md
- 2026-09-28 · M0.3 · Assumptions register (40 entries) + parameter spec · docs/assumptions.yaml,
  docs/specs/06_parameters.md
- 2026-09-28 · M0.4 · CSDS made the sole data source; corpus, libraries and constraints documented
  (no cross-match identity, CC BY-NC-SA DSA, channel-set change) · docs/data/, ADR-0003/0005
- 2026-09-28 · M0.2 (partial) · Batch 2: TAR², Contextual xT, MLMove, X-Ego added; Same-Player updated to v2
  (headline AUC 0.926/0.956; domain-matched training matters). New cross-paper findings: outcome-level
  validation of spatial features, WPA telescoping test, CSDS capture-frequency caveat, and a
  re-identification ban · docs/research/papers/README.md
- 2026-09-28 · M0.2 (partial) · Batch 3: Xenopoulos (WPA 2020, economy/OSE 2021), Franks meta-analytics,
  Brill/Yurko/Wyner. Spec changes: two uncertainty kinds and a fractional bootstrap (specs/04), real Franks
  D/S/I adapted within-match, game-level WP + OSE for economy, damage events + victim-negative WPA credit;
  MV.4 now builds a CSDS-fitted round simulator · docs/research/papers/README.md
- 2026-09-28 · M0.2 (partial) · Batch 4: Play Like Champions (full text) and HLTV Rating 3.0 (owner's notes,
  `verified: notes`). Added counterfactual rules (actionable, on-manifold, minimum viable change), a
  round-end residual credit rule, eco-adjusted duel value via xK, and a build-versioned economy (Aug 2025
  change) · docs/research/papers/README.md
- 2026-09-28 · M0.2 (partial) · Xenopoulos, Freeman & Silva 2022 added (ACM HTML full text): a pro-trained WP
  model was miscalibrated on PureSkill amateur MM (ECE 0.023 vs 0.004 in-domain) → prior evidence for A-01
  (still open until MV.3). Added a rank-prior feature candidate, map-imbalance note, abandonment flag ·
  docs/research/papers/xenopoulos_pro_vs_amateur_wp.md
- 2026-09-28 · M0.5 · Research-driven planning (ADR-0006): the roadmap is split into a committed horizon,
  decision points D1–D5 with branches, and a provisional backlog; an exploration phase E.1–E.5 is added;
  docs/FINDINGS.md, the plan-next-step skill, benchmark-mode feedback (the D2-c fallback) and assumption
  A-41 (the planned modules cover the real loss causes) · ROADMAP.md
- 2026-09-28 · M0.6 (partial) · Adopted a fork of uditgoenka/autoresearch as the project base (ADR-0007,
  supersedes ADR-0004). Loop protocol docs/specs/07 (gated keep rule: budget-corrected CI lower bound of
  the improvement > 0, training matches only, sealed test once, persona commands = ideation), A-42 +
  `loop.*` parameters, tasks M2.5 and MV.14, `scripts/kbcheck.py` + CI (it also found 7 register
  `parameters` keys that did not match docs/specs/06; fixed). Migration dry run against upstream v2.2.2:
  both histories merged, kbcheck and the four upstream test suites green. The fork itself still has to be
  created by the user · docs/specs/07_autoresearch_protocol.md
- 2026-09-28 · M0.6 (partial) · Migration run on the fork `plus-jan/cscoach` (branch
  `claude/cscoach-migration`): upstream autoresearch v2.2.2 (050e30d) + knowledge base with history
  (c3d8f62); upstream README → guide/AUTORESEARCH.md; cscoach skills tracked; safety hooks enabled in
  .claude/settings.json. Local checks: kbcheck OK; upstream tests hooks/orchestrator/regression/maintenance
  all pass. Tick after the PR is merged with CI green · docs/adr/0007-autoresearch-fork.md
- 2026-09-28 · M0.6 (partial) · PR #1 merged into master (af86286). Local: kbcheck OK; upstream suites
  hooks 228/228, maintenance 50/50, orchestrator 195/195, regression 65/65. GitHub Actions jobs were not
  started (account locked due to a billing issue), so CI is not yet green · ROADMAP.md
- 2026-09-28 · M1.1 · CSDS access confirmed: revisions 2025-09-01 to 2026-09-28 exported to
  /media/jan/merged/cs2coach (32,379 match headers; ~4,510 matches with all channels; header tomes
  `header.2025-09-01,2026-09-28.full` and a pilot). License decided: non-commercial only, derived work
  public under CC BY-NC-SA 4.0 with "Data provided by PureSkill.gg.", PureSkill.gg notified before the
  first release; A-38 decided · docs/adr/0008-csds-license-use.md
- 2026-09-28 · M0.6 · Done. No remote CI: checks run locally via the new gate `scripts/check.sh` (kbcheck +
  the four upstream suites; ADR-0009, amends ADR-0007); work branches are merged into master locally ·
  docs/adr/0009-local-checks.md
- 2026-09-28 · M1.2 · Reproducible export (`cscoach.data.export`: ADX asset index → plan → export to
  s3://cs2coach-csds-688474982708 → sync) and manifest (`cscoach.data.manifest`). 363 live revisions
  (2025-09-01 to 2026-09-27), 32,498 matches (steam 30,731 / faceit 1,636 / unknown 131; v30 26,516 /
  v42 5,982), 8,676 with all channels, of which 4,864 = seeded 15% sample; 351 GB; this run exported
  129,800 assets (153.8 GB, est. egress $14). F-01: legacy test download over-represents FACEIT (0.079
  vs 0.050) → use the seeded sample · reports/data/export_manifest_by_revision_date.csv
- 2026-09-28 · M1.3 · Header tome rebuilt (32,498); dedup 647 groups / 719 copies → 31,779 canonical
  (5v5 27,655, wingman 4,124); clean 5v5 25,434 (steam 24,056 / faceit 1,378; v30 20,984 / v42 4,450;
  seeded full-channel 3,930). Counts per platform × channel set (all / canonical / clean / full):
  faceit v30 1,284/1,284/1,099/439, faceit v42 352/352/279/109, steam v30 25,159/24,545/19,885/6,413,
  steam v42 5,572/5,469/4,171/1,669, unknown 131/129/0/46. Clean per month 2025-08…2026-09: 371, 1,340,
  712, 1,615, 1,764, 2,154, 2,410, 2,316, 2,031, 1,507, 2,225, 2,532, 2,493, 1,964. Full table
  (platform × map × month × channel set, 350 cells) in the report. F-02 · reports/experiments/20260928-1540_m1.3_header_quality/report.md
- 2026-09-28 · M1.4 · Rank decoding (Steam rank_type 11 Premier / 12 Competitive / 7 Wingman; FACEIT level in
  rank_platform; type-free v30 rule agrees 2,079/2,079). Tier coverage, seeded canonical 5v5 (n = 4,176):
  faceit low/mid/high/semipro/null 18/84/84/46/13; steam competitive 578/292/31/0/508; steam premier
  1,110/372/316/164/543; unknown 17 null. Spread ≥ 2 tiers 17.5%. F-03 (legacy download = 100% de_mirage) ·
  reports/experiments/20260928-1554_m1.4_tiers/report.md
- 2026-09-28 · M1.5 · Volume check (clean seeded 5v5, f = 0.15): 3,930 matches, 2,932 tiered, 5 maps ≥ 300 ✓;
  tier × platform ≥ 300: steam low/mid/high ✓ (1,596/638/333), steam semipro 157 ✗, faceit 14/71/81/42 ✗.
  Top-up: f = 0.35 → 210 GB ≈ $19; + all FACEIT → 248 GB ≈ $22; f = 1 → 888 GB ≈ $80. F-04 · reports/experiments/20260928-1559_m1.5_volume/report.md
- 2026-09-28 · M2.1 · Round reconstruction (7,984 canonical 5v5 full-channel matches, 162,102 rounds, 2,822 OT):
  final team scores = round_state + header winner in 99.887% (v30 99.921%, v42 99.757%; OT and draws 100%) after
  the v30 half-start winner fix. F-05 · reports/experiments/20260928-1613_m2.1_rounds/report.md
- 2026-09-28 · M2.2 · Snapshot sampler + as-of join (300 clean seeded matches): 703,293 snapshots (2,344/match,
  36.6% event-driven), 7.0 M player rows, alive share 0.68; leakage check 300/300; 0.39 s/match. Dead players
  from `player_death` (F-06) · reports/experiments/20260928-1623_m2.2_snapshots/report.md
- 2026-09-28 · M2.3 (partial) · State features v1 (`cscoach.data.features`, 39 columns): per-side alive, HP, armor,
  helmets, kits, equipment value, money, primaries, utility counts, man advantage, time remaining, bomb state,
  context; denylist + truncation tests. 300 matches: 703,293 rows, 0.5 s/match; freeze-end 5v5 in 93.4% of rounds;
  0.4% of snapshots with a player without side. Found: ghost rows of absent players (fixed in snapshots),
  `time_remaining_s` < 0 in 0.6% of rows (timers → MV.1). Distributions per tier/platform after the top-up.
- 2026-09-28 · MV.1 · Codes decoded (sides, win reasons v42, hit groups, weapon item indices; site from place_name),
  timers (round 115 s, bomb 41 s, freeze 15/20 s), ticks (64 Hz, gaps ≤ 7 ticks, merges ≤ 1 tick), economy rules
  (loss counter −2 per win, plant bonus 600, CT +50 per T kill, OT 10,000; money 96.2–97.1% with one credit).
  v30 round ends 6.7 s late → `decided_tick`. A-13/A-14 refuted → A-44/A-45; A-15/A-16 supported. F-07 ·
  docs/data/csds_decoding.md · reports/experiments/20260928-1657_mv1_decoding/report.md
- 2026-09-28 · M2.4 · Leakage audit (300 clean seeded matches, 6,215 freeze-end snapshots): max single-feature AUC
  0.630 [0.615, 0.644] (ct_equip_value) ≪ 0.99 → gate passes; best mid-round feature man_advantage 0.874. F-08 ·
  reports/experiments/20260928-1705_m2.4_leakage_audit/report.md
- 2026-09-28 · M2.5 · Gated loop harness: metrics/splits (docs/specs/04 §7), sealed data path with access log,
  gated_verify (one-sided cluster-bootstrap lower bound of Δlog-loss at 1 − α/budget), guard (split hash, sealed reads,
  ECE gates, leakage tests). Synthetic loop (A-33): 5 variants, 1 kept, all as expected. ECE small-sample bias noted
  for MV.5 (A-07) · reports/experiments/20260928-1711_m2.5_synthetic_loop/report.md
- 2026-09-28 · MV.14 · Gated loop false-keep simulation (A-33, known truth; 200 loops × 15 variants per cell):
  corrected FKR 0.045 [0.016, 0.074] and power 0.94 at 6,900 training matches (pooled FKR 0.050); uncorrected FKR
  ≈ 0.3; power < 80% below ~5,000 matches. A-42 supported; `loop.min_train_matches` 5,000. F-09 · reports/experiments/20260928-1720_mv14_false_keep/report.md
