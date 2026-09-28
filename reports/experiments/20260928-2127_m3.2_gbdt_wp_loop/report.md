# M3.2 — GBDT WP, gated loop (training matches only)

- code: commit 685ff4d on branch `claude/m3.2`; config `configs/wp_gbdt.yaml` (champion
  = HEAD after iteration 11); task `gbdt_wp` (`cscoach.models.wp_gbdt`); report `cscoach.models.wp_gbdt_report`.
- data: `derived/wp_table_v1.parquet`, 9,931 bomb-defusal matches (A-47), header tome `header.2025-09-01,2026-09-28.full`,
  channel sets v30/v42; split `wp_v1` (seed 20260928), 5 grouped folds over 6,293 training matches (13,626,911 rows,
  129,527 rounds). Calibration, test and temporal folds were not read. Data provided by PureSkill.gg.
- loop (docs/specs/07 §2, A-42): budget 15, **11 variants tried, 1 kept**; keep iff the one-sided cluster-bootstrap
  lower bound (level 0.99667, 2,000 resamples, seed 20260928) of Δlog-loss vs HEAD~1 > 0 and the guard passes.
  Ledgers: `loop_results.tsv` (autoresearch), `verify_ledger.tsv` (raw Δ per Verify). Stopped at 11: every effect
  was < 0.0005 (the WP relevance threshold is 0.002).

| # | variant | Δ log-loss | lower bound | decision |
|---|---|---|---|---|
| 1 | num_leaves 31 → 63 | +0.000087 | −0.000001 | discard |
| 2 | + money (ct/t) | +0.000024 | −0.000153 | discard |
| 3 | + second_in_round | +0.000100 | +0.000017 | **keep** |
| 4 | min_data_in_leaf 200 → 1000 | +0.000003 | −0.000064 | discard |
| 5 | lambda_l2 1 → 10 | +0.000030 | −0.000026 | discard |
| 6 | train_row_fraction 0.25 → 0.5 | −0.000016 | −0.000111 | discard |
| 7 | − tier, platform | −0.000055 | −0.000210 | discard (they stay) |
| 8 | − map_name | −0.000095 | −0.000308 | discard (it stays) |
| 9 | feature_fraction 0.8 → 1.0 | −0.000459 | −0.000564 | discard |
| 10 | + rank prior (3 features, A-48) | −0.000196 | −0.000488 | discard |
| 11 | + rank_diff_alive only | +0.000161 | −0.000104 | discard |

Rank-prior table rebuild between iterations 9 and 10: all existing columns identical (checksums); rank_diff coverage
85–97% on tiered matches; freeze-end AUC of rank_diff 0.511.

Champion vs M3.1 logistic baseline, identical out-of-fold rows (summary.json, strata.csv; 500 match resamples):
log-loss 0.4849 [0.4830, 0.4869] vs 0.5157 [0.5138, 0.5174], paired Δ 0.0308 [0.0298, 0.0319]; Brier 0.1627 vs
0.1749; ECE 0.0061 vs 0.0086; residual ESS 148k rounds. ECE per tier ≤ 0.0071, per platform ≤ 0.0063, per map ≤ 0.017,
per phase ≤ 0.0066; alive states with a side wiped out stay the weakest (3v0 0.091, 2v0 0.044, 1v0 0.034).
The ECE gates pass on these out-of-fold predictions (information only). The sealed-test evaluation is deferred to
M3.4, after the calibration layer (M3.3), so the complete WP pipeline gets the single sealed look.
