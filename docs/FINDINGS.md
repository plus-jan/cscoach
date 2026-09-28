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
