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
