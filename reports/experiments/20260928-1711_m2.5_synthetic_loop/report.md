# M2.5 — Gated loop harness (synthetic end-to-end run)

Synthetic data (A-33): this run proves code correctness only, never anything about CS2.

## Reproduce
`uv run python -m cscoach.loops.run_local --repo <scratch dir> --out <dir>` (seed 20260928); code: the M2.5 commit that
adds this report (`cscoach.eval.*`, `cscoach.loops.*`).

## Harness (docs/specs/07 §2)
- `cscoach.eval.metrics` (Brier, log-loss, quantile reliability, ECE; docs/specs/04 §7) and `cscoach.eval.splits`
  (stratified match-grouped split, K folds over training matches).
- `cscoach.loops.sealed`: `split.json` (seed, fractions, folds, hash); `LoopData` hands out training matches only, logs
  every match it reads and raises on a sealed (calibration/test) match.
- `cscoach.loops.gated_verify --config <task.yaml>`: prints the lower bound of the one-sided cluster-bootstrap CI of
  Δlog-loss (champion − candidate) on pooled out-of-fold predictions, level 1 − α/budget; champion = config at HEAD~1;
  appends a ledger row.
- `cscoach.loops.guard --config <task.yaml> [--pytest]`: split hash and integrity, no sealed/unknown reads in the access
  log, ECE gates overall and per stratum on the candidate's out-of-fold predictions, leakage tests.
- Loops compare **config-driven** variants; model code changes must be exposed as config switches.

## Synthetic loop (3,000 matches × 12 rounds; split 70/10/20, K = 5; α 0.05, budget 15 → one-sided level 0.9967; B 2,000)
| # | variant | lower bound | guard | decision (expected) |
|---|---|---|---|---|
| 1 | add informative feature x2 | +0.0172 | ok | keep (keep) |
| 2 | add noise feature | −0.0002 | ok | revert (revert) |
| 3 | heavy regularisation | −0.0168 | ECE fails | revert (revert) |
| 4 | miscalibrated output (+0.12) | −0.0957 | ECE fails | revert (revert) |
| 5 | add two noise features | −0.0003 | ok | revert (revert) |

All decisions as expected. Ledgers: `loop_ledger.tsv` (decisions), `verify_ledger.tsv` (Verify rows); git history of the
scratch repo in `summary.json`. Unit tests: sealed read → SealedFoldError and guard failure; edited split → guard failure;
real improvement → lower bound > 0, noise/identical → ≤ 0; calibration gate passes a calibrated model and fails a
shifted one.

## Observation for MV.5 (method property, not a CS2 fact)
Per-stratum ECE is biased upward by estimation noise (≈ 0.8 · 0.5 / √(rows per bin) with 15 bins). A correctly specified
synthetic model showed ECE 0.032–0.037 per stratum with ~2,700 clustered rows per stratum, above the 0.03 gate; it needed
~8,000 independent rows per stratum to pass. The gate minimum of 500 rows per stratum (A-07) is far too small for ECE
gates to be meaningful; MV.5 must set the minimum (or use a bias-corrected/bootstrap ECE test).
