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
