# M3.3 — WP calibration layer: gated loop and final fit

- code: commit d372429 (branch `claude/m3.3`); `cscoach.models.calibration`, loop task `gbdt_wp_calibrated`, final fit
  `cscoach.models.wp_fit`; config `configs/wp_calibration.yaml` (gbdt block = M3.2 champion).
- data: `derived/wp_table_v1.parquet` (9,931 de_ matches, A-47), split `wp_v1` (sha256 47e2b1ba…), header tome
  `header.2025-09-01,2026-09-28.full`, channel sets v30/v42. Data provided by PureSkill.gg.

## Loop (training matches only; calibration cross-fitted over the 5 training folds)

Keep rule as in M3.2 (level 0.99667, 2,000 match resamples, seed 20260928; guard incl. ECE gates). Budget 15,
**5 variants tried, 1 kept**. Ledgers: `loop_results.tsv`, `verify_ledger.tsv` (rows for task gbdt_wp_calibrated).

| # | calibration | Δ log-loss | lower bound | OOF ECE | ECE per tier (max) | decision |
|---|---|---|---|---|---|---|
| 0 | none (champion) | — | — | 0.0061 | 0.0071 | — |
| 1 | global isotonic | +0.000077 | −0.000015 | 0.0004 | 0.0049 | discard |
| 2 | global Platt | +0.000073 | +0.000002 | 0.0031 | 0.0054 | **keep** |
| 3 | global + per tier, auto (A-28 design; isotonic everywhere) | −0.000222 | −0.000343 | 0.0006 | 0.0032 | discard |
| 4 | global + per platform, auto | −0.000026 | −0.000103 | 0.0004 | 0.0050 | discard |
| 5 | global + per tier × platform, auto | −0.000450 | −0.000621 | 0.0007 | 0.0031 | discard |

(Variants 3–5 are compared with the kept Platt champion.) Isotonic calibrators remove almost all ECE but do not
improve log-loss, and per-group isotonic makes it worse: with ~1–2 M clustered rows per group the step functions fit
noise. The keep rule uses log-loss (docs/specs/07 §2), so an ECE-only gain does not qualify.

## Final fit (reads training + calibration matches only; access.json)

GBDT on 6,293 training matches (13,626,911 rows), early stopping on a grouped 10% slice of them: 818 trees.
Global Platt on the GBDT's predictions for the calibration fold (897 matches, 1,949,468 rows, 18,507 rounds):
a = 0.9595, b = 0.0109 (slight shrinkage toward 0.5). Artefacts in `<root>/models/wp_v1/` (booster sha256
in card.json). No metric is reported on the calibration fold (in-sample for the calibrator); the test fold and the
temporal holdout stay sealed for the single M3.4 evaluation. Loop guard after the fit: GUARD OK.
