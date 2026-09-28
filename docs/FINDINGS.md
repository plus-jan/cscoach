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

### F-04 — Volume: Steam low–high suffice; Steam semipro and FACEIT need a top-up; some gaps are structural
- date: 2026-09-28 · task: M1.5 · decision: top-up size (user)
- question: Does the seeded full-channel sample (f = 0.15) meet the A-32/A-07 targets per stratum, and what
  would a top-up cost?
- result: clean seeded 5v5: 3,930 matches (2,932 tiered), 5 maps ≥ 300 → overall targets met. Tier × platform:
  steam low 1,596, mid 638, high 333 meet ≥ 300 matches and ≥ 2,500 rounds; steam semipro 157 (needs f ≈ 0.29);
  faceit low 14, mid 71, high 81, semipro 42 (need f ≈ 0.56–0.63 or all FACEIT; low and semipro stay < 300 even
  at f = 1). Competitive-scale high 31 (≈ 207 at f = 1), no competitive semipro. Maps anubis/overpass/cache need
  f ≈ 0.24–0.32. Exact extra download: f = 0.35 → 210 GB (≈ $19); f = 0.35 + all FACEIT → 248 GB (≈ $22);
  f = 1.0 → 888 GB (≈ $80).
- evidence: `reports/experiments/20260928-1559_m1.5_volume/` (report.md, summary.json, gap_*.csv); configs `configs/volume.yaml`, `configs/export.yaml`.
- confidence: medium (projections assume the seeded sample's composition; counts ± √n).
- changes: A-32 note (gap analysis). No status change.
- next step: user decision on the top-up (recommended: f = 0.35 + all FACEIT, platform-stratified); then the
  first open Part A tasks M2.1/MV.1 — rationale: E.x and M3 need rounds; the top-up can run in parallel.
  Decided 2026-09-28: f = 0.35 + all FACEIT (248 GB, ≈ $22).
- supersedes: —

### F-05 — Round winners need a parser-specific fix; v30 has no round end reasons
- date: 2026-09-28 · task: M2.1 · decision: —
- question: Can round winners be reconstructed so that they reproduce the final score (M2.1 DoD)?
- result: `team_code`/`winner_team_code` 2 = T, 3 = CT; sides per round from `player_info` (swaps at 13, 28, 34,
  40). The v30 parser reports a stale winner side in the first round of every half (after each swap and at each
  overtime-block start): round 13 wrong in 322/322 sampled v30 matches, rounds 14–24 right in 100 %. With the fix,
  final team scores match `round_state` and the header winner in 99.887 % of 7,984 matches (v30 99.921 %, v42
  99.757 %; overtime 100 %, draws 100 %). v30 `win_reason_code` only encodes the winner side (8/9); v42 has full
  reasons. `round_state` score conventions differ by parser.
- evidence: `reports/experiments/20260928-1613_m2.1_rounds/report.md`; config `configs/rounds.yaml`.
- confidence: high (exact reconciliation on all full-channel canonical 5v5 matches).
- changes: A-15 note (side/winner decoding); docs/specs/02 `rounds`; docs/data/README.md quirk 13;
  parameters `rounds.*`. E.1 must derive "how rounds end" from bomb events/time for v30 matches, or restrict
  that part to v42.
- next step: finish the M1.5 top-up, refresh manifest/quality/tiers/volume, rebuild rounds for the new matches;
  then M2.2 (snapshot sampler) and MV.1 (remaining code decoding) — rationale: both are Part A and unblock E.x/M3.
- supersedes: —

### F-06 — `player_status` has no rows for dead players; state must come from deaths
- date: 2026-09-28 · task: M2.2 · decision: —
- question: Does an as-of join of `player_status` give the current state of every player at a snapshot tick?
- result: No. A victim's rows stop at the death tick (last health > 0) and resume 19–20 ticks after the round end
  with health 100 (4,638 of 4,648 resumptions in 40 matches). A plain as-of join carries dead players forward as
  alive (alive rows looked up to ~2 min stale). With `is_alive` from `player_death`: alive rows p99 staleness
  0 ticks, 144 of 4.77 M alive rows > 1 s stale; alive share 0.68. The leakage check (truncate at T, snapshots ≤ T
  unchanged) passes in 300/300 real matches.
- evidence: `reports/experiments/20260928-1623_m2.2_snapshots/report.md`; config `configs/snapshots.yaml`.
- confidence: high.
- changes: docs/specs/02 snapshots (alive state from `player_death`); docs/data/README.md quirk 14.
- next step: M2.3 state features on the snapshots (after the top-up refresh) — rationale: next Part A task;
  alive counts and man advantage depend on this fix.
- addendum (M2.3, 2026-09-28): players absent from a round (e.g. after a disconnect; their latest status row is
  from an earlier round) were still listed with masked values and `is_alive = True`; snapshots now drop them
  (0.66% of player rows; leakage check 300/300 after the change). Side per player: `player_info.team_code` is
  right for 99.97% of 45,629 deaths (victim side at death), `player_spawn` for 99.24%; on 343 disagreements
  `player_info` was right 328 times → primary `player_info`, spawn only fills missing rows.
- supersedes: —

### F-07 — Codes decoded; v30 round ends are 6.7 s late; the economy differs from the recalled rules
- date: 2026-09-28 · task: MV.1 · decision: —
- question: Can the CSDS codes, timers and economy be verified on the corpus (A-13–A-16, A-39)?
- result: see docs/data/csds_decoding.md. Codes: sides 2/3, win reasons (v42), Source hit groups 0–8, item
  definition indices (identical in v30/v42); `site_code` is not a stable site id (use the planter's `place_name`).
  v30 `round_end.tick` lies ~6.7 s after the decision (v42 exact) → snapshots included post-decision states
  (7.6 % of all snapshot rows in the 300-match sample; v42 unaffected) until `decided_tick`. Timers: round 115 s, bomb 41 s, freeze 15 or 20 s per match.
  Economy (one rule set for builds 10521–10924): loss counter −2 per win (96.7 % vs 79.1 % for −1), T plant bonus
  600, CT +50 per T killed, OT start 10,000, Zeus 100, CZ75 300; money reconciles for 86–87 % of player-rounds
  exactly and 96.2–97.1 % with one personal credit. Ticks: 64 Hz, coverage ≥ 99.4 %, merges ≤ 1 tick stale.
- evidence: `reports/experiments/20260928-1657_mv1_decoding/` (report.md, analyze.py, summary.json); docs/data/csds_decoding.md.
- confidence: high for codes, ticks and timers; medium for the economy (97 %, per-player credits missing).
- changes: A-13, A-14 refuted → A-44 (supported), A-45 (open); A-15, A-16 supported; A-39 note; docs/specs/06
  (economy, timers); `rounds.decided_tick`; `bomb_timer_s` 41; M6.1 note (per-player credits).
- next step: after the top-up, refresh everything and finish M2.3 (distributions per tier/platform), then M2.4
  (leakage audit) — rationale: remaining Part A tasks before M3; the end-tick fix changes every snapshot table.
- supersedes: —

### F-08 — No single-feature leakage at freeze end
- date: 2026-09-28 · task: M2.4 · decision: —
- question: Does any state feature predict the round winner almost perfectly at freeze end (A-46: AUC > 0.99)?
- result: no. Best: ct_equip_value AUC 0.630 [0.615, 0.644] (6,215 freeze-end snapshots, 300 matches, cluster
  bootstrap); all CT buy features 0.60–0.63. Over the round the best single feature (man advantage) peaks at 0.874
  (60–80 s). Null result on the corrected tables (MV.1 `decided_tick`).
- evidence: `reports/experiments/20260928-1705_m2.4_leakage_audit/` (report.md, summary.json); config `configs/leakage_audit.yaml`.
- confidence: medium (pre-top-up sample of 300 matches; re-run on the refreshed data).
- changes: none (A-46 threshold unchanged).
- next step: refresh after the top-up, finish M2.3, re-run this audit; then plan M2.5/M3 — rationale: the state
  table is the input of the WP baseline.
- supersedes: —

### F-09 — The budget-corrected keep rule holds its 5 % false-keep rate; loops need ≥ 5,000 training matches
- date: 2026-09-28 · task: MV.14 · decision: —
- question: Does the gated keep rule (docs/specs/07 §2) keep ≤ 5 % of null loops and find a Δlog-loss 0.002
  improvement with ≥ 80 % power at our corpus size (A-42)? Pre-registered; simulation with known truth (A-33).
- result: 200 loops of 15 variants per cell. Corrected: FKR 0.030 / 0.075 / 0.045 at 2,000 / 4,000 / 6,900 training
  matches (pooled 0.050 [0.033, 0.067]); power 0.40 / 0.73 / 0.94. Uncorrected: FKR 0.31–0.37, power 0.62–0.99.
- evidence: `reports/experiments/20260928-1720_mv14_false_keep/` (report.md, summary.json, loops.jsonl); code `cscoach.verify.mv14`.
- confidence: medium (one error model; pooled FKR at the 5 % boundary).
- changes: A-42 → supported (at ~6,900 training matches); `loop.*` confirmed; new `loop.min_train_matches` 5,000;
  docs/specs/07 note.
- next step: after the top-up refresh, M2.3 and the M2.4 re-run, then M3.1 — rationale: the loop harness is ready and
  valid at the expected size, so M3.2 tuning can use it once the baseline exists.
- supersedes: —

### F-10 — No single-feature leakage at freeze end on the refreshed data
- date: 2026-09-28 · task: M2.4 · decision: —
- question: Does F-08 hold on the full refreshed state table (A-46: AUC > 0.99)?
- result: yes. Best: ct_equip_value AUC 0.626 [0.623, 0.628] (206,470 freeze-end snapshots, 10,038 matches, cluster
  bootstrap); CT buy features 0.61–0.63. Man advantage peaks at 0.877 (60–80 s).
- evidence: `reports/experiments/20260928-2001_m2.4_leakage_audit_refresh/summary.json`; commit c2c26db; config
  `configs/leakage_audit.yaml` (b736f104b99f).
- confidence: high (full refreshed sample, narrow CIs).
- changes: none.
- next step: M3.1 on the refreshed table — rationale: the state table is clean for the WP baseline.
- supersedes: F-08

### F-11 — A six-feature logistic WP already beats the pro CS:GO XGBoost log-loss; map alone carries nothing
- date: 2026-09-28 · task: M3.1 · decision: —
- question: What do the base-rate, map-only and logistic baselines reach on CSDS (reference for M3.2)?
- result: out-of-fold on 6,293 training matches on bomb-defusal maps (13.6 M rows, 129,527 rounds): logistic 0.516
  [0.514, 0.517] vs map-only 0.693 [0.693, 0.693] (Δ 0.177 [0.175, 0.179]); base rate 0.693. ECE 0.0086 overall,
  per tier 0.009–0.015, per platform 0.008–0.011, per map 0.008–0.026. Poor calibration where a linear model
  cannot fit: alive states with a side wiped out (1v0 0.18, 3v0 0.14), 5v4 0.056, late rounds 0.037, early 0.023.
  The pro benchmark (0.535) is on a different game, tier mix and sampling, so the comparison is context only.
  Including the 105 hostage-map matches (first run) changed log-loss by < 0.001.
- evidence: `reports/experiments/20260928-2014_m3.1_baseline_wp_de/` (summary.json, strata.csv; commit 5b3cd71);
  first run with hostage maps `reports/experiments/20260928-2007_m3.1_baseline_wp/`; config `configs/wp_baseline.yaml`;
  split `wp_v1` (sealed folds unread).
- confidence: medium (training folds only; no gates are applied at M3.1).
- changes: A-47 added (supported): WP on `de_` maps only (`wp.map_prefixes`); the hostage maps (cs_office 85,
  4 others 20 matches) are dropped from the WP table.
- next step: M3.2 GBDT WP (non-linear alive × time × bomb interactions) — rationale: the calibration misses sit in
  exactly the interactions a tree model captures.
- supersedes: —

### F-12 — A monotone GBDT cuts WP log-loss by 0.031 and fixes the linear baseline's calibration; tuning and rank priors add nothing
- date: 2026-09-28 · task: M3.2 · decision: —
- question: How far does a monotone GBDT improve on the M3.1 baseline, and do hyperparameters, extra state
  features, tier/platform/map or rank priors [xenopoulos_pro_vs_amateur_wp] change it (gated keep rule, A-42)?
- result: champion OOF log-loss 0.4849 [0.4830, 0.4869] vs logistic 0.5157 on identical rows, paired Δ 0.0308
  [0.0298, 0.0319]; ECE 0.0061 (baseline 0.0086), late rounds 0.006 (0.037), 1v0 0.034 (0.18); per tier ≤ 0.0071,
  per map ≤ 0.017. Loop: 11 variants, 1 kept (+ second_in_round, Δ 0.0001); all others within ±0.0005 — capacity,
  regularisation, snapshot thinning, money, dropping tier/platform (Δ −0.00006) or map (−0.0001), and the rank prior
  (all three features Δ −0.0002; rank difference alone +0.00016, lower bound −0.0001; freeze-end AUC 0.511). Weakest
  cells: alive states with a side wiped out (3v0 ECE 0.091, 2v0 0.044).
- evidence: `reports/experiments/20260928-2127_m3.2_gbdt_wp_loop/` (report.md, summary.json, strata.csv, ledgers);
  config `configs/wp_gbdt.yaml`; split `wp_v1`, training folds only.
- confidence: medium (out-of-fold on training matches; the sealed test is evaluated once in M3.4).
- changes: A-29 → supported (start values stand); A-48 open, rank features built but not used. Unlike the CS:GO MM
  result, rank priors carry no signal beyond state and tier here (CS2 matchmaking keeps teams balanced).
- next step: M3.3 calibration layer, then M3.4 with the single sealed-test look; look at the wiped-side states (post-
  plant with no T alive, save rounds) in M3.3/MV.7 — rationale: the model is well calibrated except in those cells,
  and further tuning does not pay.
- supersedes: —

