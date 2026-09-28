# 04 — Validation protocol

This protocol decides whether a model or metric may be used. Gates are in
`configs/validation.yaml`; `cscoach validate` evaluates them and exits non-zero on failure.

## 1. Data splitting

- **Train / calibration / test** by `match_id` (default 70/10/20), stratified by tier
  and map where possible (`validation.splits.grouped_split`).
- **Grouped K-fold** (by match) for hyperparameter search.
- **Temporal holdout**: most recent game build(s) held out (drift check).
- **Player holdout** for player-level metrics (no player in both train and test).
- `assert_no_group_leakage` must be called in every training entry point.

## 2. Probabilistic metrics (WP, xK)

- Brier score, log-loss, **Brier skill score vs baseline**.
- ECE with quantile bins (15 bins default) + max calibration error; reliability curves.
- Discrimination: ROC AUC (secondary — calibration matters more for WPA).
- Stratified: per tier, per map, per round phase (early/mid/late/post-plant), per
  alive-state (5v5, 4v5, …, clutches).
- **Uncertainty**: cluster bootstrap over matches (≥ 500 resamples) for every metric
  and every model difference. Report ESS (design effect from ICC of residuals within
  rounds) next to raw n.

## 3. Promotion rule (challenger vs champion)

Promote iff: (a) log-loss improvement CI (95%, cluster bootstrap) excludes 0,
(b) no tier's ECE worsens beyond the gate, (c) latency budget met. Record in an ADR.

## 4. Player metrics (Franks et al. 2016 meta-analytics)

- **Discrimination**: share of variance between players vs within-player sampling
  variance (bootstrap over a player's rounds).
- **Stability**: split-half (odd/even matches or time halves) correlation with
  Spearman-Brown correction.
- **Independence**: 1 − R² of metric regressed on standard stats (K/D, ADR, KAST).
Metrics below gate thresholds are internal-only.

## 5. Coaching validity

- Counterfactual ΔWP must include CI; items whose CI contains 0 are not shown as
  "mistakes".
- Expert agreement study (M9.5) and prospective RCT (M11.1).

## 6. Reporting

Every run writes `reports/experiments/<ts>_<name>/metrics.json` containing: git SHA,
config hash, data manifest hash, n_matches, n_rounds, n_rows, ESS, all metrics with
CIs, per-stratum tables, gate verdicts. See `validation/report.py`.
