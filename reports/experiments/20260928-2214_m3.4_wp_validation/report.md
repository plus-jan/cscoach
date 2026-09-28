# M3.4 — WP validation of models/wp_v1 (single sealed look)

- code: commit c5df013 (`cscoach.models.wp_validate`); pre-registered config `configs/wp_validate.yaml` committed
  before the run; model `models/wp_v1` (booster 9fbcd2522780; M3.3 fit at 22f1a6e: GBDT 818 trees + global Platt).
- look ledger `<root>/splits/wp_v1/sealed_looks.json`: **look 1 of 1** for this model (test + temporal). A code dry run
  on 300 training matches preceded it (no sealed read).
- data: `derived/wp_table_v1.parquet` (de_ maps, A-47), split `wp_v1` (sha256 47e2b1ba…); header tome
  `header.2025-09-01,2026-09-28.full`. Test: 1,804 matches, 37,306 rounds, 3,925,892 rows, builds 10499–10847
  (v30 33,849 / v42 3,457 rounds). Temporal: 937 matches, 18,942 rounds, 2,017,070 rows, builds 10896–10924 (v42).
  Baseline = M3.1 logistic refitted on all 6,293 training matches. 500 match-cluster resamples (A-10), seed 20260928.
  Data provided by PureSkill.gg.

## Metrics (95% match-cluster CIs)

| fold | model | log-loss | Brier | ECE | MCE | AUC | ESS (rounds) |
|---|---|---|---|---|---|---|---|
| test | **wp_v1** | 0.4868 [0.4830, 0.4908] | 0.1636 | 0.0044 [0.0034, 0.0073] | 0.010 | 0.838 | 42,392 |
| test | wp_v1 uncalibrated | 0.4870 [0.4830, 0.4912] | 0.1637 | 0.0087 [0.0065, 0.0117] | 0.014 | 0.838 | |
| test | baseline_wp | 0.5173 [0.5138, 0.5210] | 0.1756 | 0.0098 [0.0085, 0.0125] | 0.028 | 0.811 | |
| test | map_only | 0.6929 [0.6924, 0.6933] | 0.2499 | 0.0090 | 0.115 | 0.510 | |
| temporal | **wp_v1** | 0.4807 [0.4756, 0.4864] | 0.1612 | 0.0036 [0.0035, 0.0086] | 0.009 | 0.843 | 21,715 |
| temporal | wp_v1 uncalibrated | 0.4807 [0.4754, 0.4866] | 0.1612 | 0.0059 [0.0044, 0.0103] | 0.016 | 0.843 | |
| temporal | baseline_wp | 0.5125 [0.5078, 0.5174] | 0.1736 | 0.0111 [0.0079, 0.0164] | 0.028 | 0.815 | |
| temporal | map_only | 0.6925 [0.6920, 0.6930] | 0.2497 | 0.0126 | 0.044 | 0.512 | |

Paired vs baseline: Δlog-loss test 0.0305 [0.0286, 0.0322], temporal 0.0318 [0.0294, 0.0344]; Brier skill score test
0.068 [0.063, 0.072], temporal 0.072 [0.066, 0.077]. Pro CS:GO reference (not comparable 1:1): XGBoost 0.535.

## Gates (docs/specs/06; still assumptions A-06/A-07, not decided policy)

| gate | test | temporal |
|---|---|---|
| ECE overall ≤ 0.02 | 0.0044 ✔ | 0.0036 ✔ |
| ECE per tier ≤ 0.03 (≥ 500 rounds) | worst high 0.0131 ✔ | worst high 0.0195 ✔ |
| ECE per map ≤ 0.035 (≥ 500 rounds) | worst de_train 0.0304 ✔ (32 matches, CI 0.022–0.058) | worst de_ancient 0.0244 ✔ |
| BSS vs baseline, CI low > 0 | 0.063 ✔ | 0.066 ✔ |

**All gates pass on both folds** (point estimates, as the gates are defined). Reporting gap: strata under 30 matches were
dropped before the gate check in this run (fixed after the run: they are now kept and listed as skipped); here that
concerns semipro in the temporal fold (22 matches), which is ungated. Its reliability curve (reliability_temporal.csv)
shows CT under-prediction (+0.023 mean gap, max 0.14 in one bin).

## Reliability inspection (A-01)

Per tier × man-advantage sign (reliability_*.csv): on the test fold the weighted mean gap is within ±0.01 in every
cell; no systematic over-confidence in man-advantage states for low tiers. In the temporal fold high and semipro tiers
lean toward under-predicting CT (+0.017 / +0.023).

**Systematic bias found: post-plant states with the T side eliminated.** 1v0 ECE 0.047 (test) and 0.247 (temporal);
at 1v0 post-plant the model predicts 0.60 (temporal) where CT wins 0.85. Diagnosis on training matches only
(`diagnose_v30_defuse.py`, `diag_*.csv`, `diag_summary.json`): in v30 matches `rounds.decided_tick` is set at the death
that eliminated the T side even when the bomb is planted, so the snapshots of rounds that CT then wins by defusing
stop at the elimination (155 of 155 such v30 rounds have no T-wiped snapshot; v42 127 of 127 have them, decided at the
defuse, median 9.3 s later). The v30 T-wiped post-plant states that remain are almost only lost ones (CT win 2% vs
v42 91%; with a kit and 10–20 s left 2% (42 rounds) vs 98% (252 rounds)). This is a label-selection bug in the
M2.1/MV.1 decided-tick rule (CS2 does not end a round when the T side dies after the plant), not model error.
