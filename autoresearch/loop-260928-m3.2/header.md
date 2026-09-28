# M3.2 gated loop — header (written before iteration 1)

- task: M3.2 GBDT WP · config `configs/wp_gbdt.yaml` (model block) · task `gbdt_wp` (`cscoach.models.wp_gbdt`)
- data: `derived/wp_table_v1.parquet` (9,931 de_ matches, A-47); split `splits/wp_v1` (seed 20260928, 5 grouped
  folds over 6,293 training matches); sealed folds (calibration, test, temporal) are not read.
- keep rule (docs/specs/07 §2, A-42): lower bound of the one-sided cluster-bootstrap CI (clusters = matches) of
  Δlog-loss vs the champion at HEAD~1, level 1 − 0.05/15 = 0.99667, 2,000 resamples, bootstrap seed 20260928;
  keep iff > 0 and the guard passes (tests, leakage tests, split integrity, sealed reads, ECE ≤ 0.02 overall and
  ≤ 0.03 per tier on the candidate's out-of-fold predictions).
- budget: 15 variants. Model seed 20260928 (LightGBM, early-stopping slice, snapshot thinning).
- iteration 0 (champion = start values, A-29/A-27): OOF log-loss 0.4850, ECE 0.0063.

Planned variants (one change each, order may adapt to results; any change is logged):
hyperparameters (A-29): num_leaves 63 / 127, min_data_in_leaf 1000, learning_rate 0.05, lambda_l2 10,
feature_fraction 1.0, train_row_fraction 0.5; features: + money (ct/t_money_sum), + second_in_round,
− tier/platform (ablation), − map_name (ablation); rank-prior features (docs/specs/03) after a table extension.
