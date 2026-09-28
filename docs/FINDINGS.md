# Findings log

Results **from our own data** (CSDS) that change what we believe or what we do next. It is the
backbone of research-driven planning (ADR-0006): every decision point (ROADMAP Part B) and every
exploration or verification task writes an entry here, and `plan-next-step` reads it.

Literature evidence stays in `docs/research/` and is not a finding; synthetic-data results never are
(A-33).

## Rules

- One entry per result, numbered `F-NN` and never reused. Newest at the bottom.
- An entry states the **result** (numbers with CIs), the **evidence** (report path in the code repo,
  CSDS revisions, config hash), what it **changes** (assumption statuses, parameters, specs, ADRs) and
  the **next step** chosen, with its rationale.
- Negative and null results are recorded too. "No difference" is a finding.
- A finding can be superseded by a later one, which must say `supersedes: F-NN`.

## Template

```
### F-NN — <short title>
- date: YYYY-MM-DD · task: <E.x | MV.x | M.x> · decision: <D1..D5 or —>
- question: <what we asked; pre-registered criterion if any>
- result: <numbers with CIs; strata>
- evidence: <code-repo report path, CSDS revision ids/dates, config hash>
- confidence: high | medium | low (why)
- changes: <A-NN status → …; parameters; specs; ADR-XXXX>
- next step: <chosen branch/tasks> — rationale: <why this beats the alternatives>
- supersedes: <F-NN or —>
```

## Log

### F-01 — The legacy full-channel download is not a random sample; use the seeded sample
- date: 2026-09-28 · task: M1.2 · decision: —
- question: Is the first full-channel download (4,510 matches, selection method unknown) representative
  of the corpus, or must full-channel analyses use a documented sample?
- result: FACEIT share (match-level bootstrap, 2,000 resamples, 95% CI): all 32,498 matches 0.050
  [0.048, 0.053]; seeded sample (seed 20260928, fraction 0.15, n = 4,864) 0.051 [0.045, 0.057];
  legacy-only full matches (n = 3,812) 0.079 [0.071, 0.088]. The legacy set over-represents FACEIT by
  ≈ 60%; the seeded sample matches the corpus. Also: 878 matches sit in a folder whose date differs from
  their ADX revision date; all 32,498 matches map to one of 363 live revisions (2025-09-01 to
  2026-09-27). Channel sets: v30 26,516 (ppp 6.11.x–7.2.1), v42 5,982 (ppp 8.2.2–8.5.0).
- evidence: `reports/data/export_manifest_by_revision_date.csv`; per-match manifest
  `<root>/manifest/matches.parquet` (not committed); code 8b36385 + this change set; config
  `configs/export.yaml` sha256 ed27b7181c6a; ADX dataset f49be2ef387af522a7b6f000158113e0.
- confidence: high (descriptive; exact counts; match is the resampling unit).
- changes: rule in docs/data/README.md: analyses that need non-header channels use
  `in_seeded_sample == True`; legacy-only matches are for code development only. No assumption status
  changes (A-34 corpus bias stays open for MV.2).
- next step: M1.3 on the header tome of all 32,498 matches — rationale: dedup and quality flags come
  before any analysis, and headers cover the full corpus.
- supersedes: —

### F-02 — Header loser scores are unreliable; 2% duplicates, 13% wingman, 6% incomplete
- date: 2026-09-28 · task: M1.3 · decision: —
- question: Which header fields can drive dedup and completeness, and does excluding flagged matches bias
  the corpus (A-36, A-40)?
- result: (1) Header `*_starters_score_final`: the winner score equals the last `round_state` score in
  100% of 8,676 full-channel matches, the loser score in only 51.6% (header too high by 1–8); `round_state`
  scores equal the `round_end` count in 99.92%. (2) 647 duplicate groups, 719 extra copies (2.2%;
  steam 4.4% of rows, faceit 0.1%); 28/28 groups with ≥ 2 full-channel copies have identical round_end
  sequences. (3) `is_wingman` is null for 88% of rows; `unique_steamids` ≤ 5 marks 4,124 canonical
  wingman matches (13%). (4) Canonical final states: regulation 27,142, incomplete 1,987, draw 1,692,
  overtime 958. (5) No tick gap > 1 s (max 0.109 s), no missing round_end, no warmup after start.
  (6) Exclusion of canonical 5v5 matches (bootstrap 95% CI): faceit 0.156 [0.139, 0.175] vs steam 0.071
  [0.068, 0.074]; maps 0.073–0.087, overlapping CIs.
- evidence: `reports/experiments/20260928-1540_m1.3_header_quality/` (report.md, summary.json, validation.json, counts CSV); header tome
  `header.2025-09-01,2026-09-28.full`; config `configs/quality.yaml`.
- confidence: high for (1)–(5) (exact counts); medium for the abandonment flag (upper bound, id gaps).
- changes: A-43 new (format/completion rule, open); A-36 note (precision checked, leakage untested);
  A-40 note (maps fine, platform differential → keep flagged matches stratifiable, never drop silently);
  docs/data/README.md quirks 10–11; final scores come from `round_state` wherever channels exist.
- next step: M1.4 (tier labels) — rationale: A-40 still needs the tier dimension, and D1 depends on tiers.
- supersedes: —

### F-03 — Ranks decode cleanly; tiers exist for 74% of seeded 5v5 matches, missingness is not random
- date: 2026-09-28 · task: M1.4 · decision: feeds D1 (via MV.2)
- question: Can `player_info` ranks be decoded per platform without guessing, and how complete and
  homogeneous are match tiers (A-11, A-12, A-15, A-40)?
- result: Steam `rank_type` 11 = Premier (1,206–30,763), 12 = Competitive SG, 7 = Wingman SG; FACEIT level in
  `rank_platform`; 0 = unknown. `rank_type` is missing in v30; the type-free rule (Premier iff any rank ≥ 19)
  agrees with `rank_type` in 2,079/2,079 v42 matches with known ranks. Seeded canonical 5v5 (n = 4,176):
  tier for 3,095 (74%): low 1,706, mid 748, high 431, semipro 210, null 1,081. Missing tier: competitive 0.361
  [0.335, 0.385], premier 0.217 [0.200, 0.233], faceit 0.053 [0.025, 0.082]. Lobby spread ≥ 2 tiers 0.175
  [0.162, 0.189]. Competitive skill groups never reach semipro (64% low). Exclusion by known tier 0.039–0.056
  (overlapping), untiered 0.077. **Extends F-01:** the legacy full-channel download is 100% de_mirage
  (n = 3,808); the seeded sample matches the corpus (mirage 0.263 vs 0.255).
- evidence: `reports/experiments/20260928-1554_m1.4_tiers/` (report.md, summary.json, validation.json, tier_coverage_seeded.csv); config
  `configs/tiers.yaml`.
- confidence: high for decoding and counts; medium for cut-off adequacy (A-11 untested until MV.2).
- changes: A-15 note (rank fields decoded; other codes open); A-12 note (missingness and spread measured);
  A-11 note (uneven across scales); A-40 note (tier dimension flat among tiered); docs/specs/06 rank decoding;
  docs/data/README.md quirk 12.
- next step: M1.5 (volume check per stratum) — rationale: semipro is below the A-32 target and tiers exist only
  for full-channel matches, so the top-up size must be decided before E.x/M3.
- supersedes: —
