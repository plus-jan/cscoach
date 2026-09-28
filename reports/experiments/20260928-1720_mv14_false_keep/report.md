# MV.14 — False-keep rate and power of the gated loop

Simulation with known truth (A-33 permits it: a method property, not a CS2 fact).

## Reproduce
code commit `2d97ab9` · `uv run python -m cscoach.verify.mv14 --out <dir> --loops 200` (defaults: sizes 2,000 / 4,000 /
6,900 training matches, 21 rounds, 6 snapshots per round, budget 15, α 0.05, B 2,000, σ_row 0.5, σ_match 0.2, target
Δlog-loss 0.002, seed 20260928). Per-loop results: `loops.jsonl`; aggregates: `summary.json`.

## Pre-registered criterion (A-42)
Loop-level false-keep rate (≥ 1 of the null variants kept in a 15-variant loop) ≤ 5 %; power to keep a planted
Δlog-loss = 0.002 improvement ≥ 80 % at the expected corpus size.

## Design
Truth: Brownian round (the round is won iff B₁ > 0; snapshot WP = Φ(B_t/√(1−t)), exactly calibrated; snapshots share
the round outcome). Models: logit error with row (σ 0.5) and per-match (σ 0.2) parts; null variants have the
champion's error; the planted variant's row error is lowered (bisection) to be 0.002 better in expected log-loss.
Each loop: 15 variants on the same data and the same bootstrap resamples, keep iff the lower bound of the one-sided
cluster-bootstrap CI (clusters = matches) of Δlog-loss > 0 at 1 − α/15 (corrected) or 1 − α (uncorrected); a kept
variant becomes the champion. 200 null loops and 200 planted loops per size.

## Results
| training matches | FKR corrected (95 % CI) | FKR uncorrected | power corrected (95 % CI) | power uncorrected |
|---|---|---|---|---|
| 2,000 | 0.030 [0.006, 0.054] | 0.315 | 0.395 [0.327, 0.463] | 0.620 |
| 4,000 | 0.075 [0.039, 0.112] | 0.370 | 0.730 [0.669, 0.792] | 0.930 |
| 6,900 | 0.045 [0.016, 0.074] | 0.305 | 0.940 [0.907, 0.973] | 0.990 |

Pooled corrected FKR (size-independent in theory): 30/600 = 0.050 [0.033, 0.067]; the Bonferroni-type bound is
1 − (1 − 0.05/15)^15 = 0.049. Without the budget correction 30–37 % of null loops keep a useless change.

## Verdict
- A-42 **supported at the expected training size** (~6,900 matches after the top-up): FKR 0.045, power 0.94.
- The corrected level is required (uncorrected FKR ≈ 0.3). `loop.*` parameters confirmed (budget 15, α 0.05, B 2,000).
- Condition: power for Δ = 0.002 falls below 80 % under ~5,000 training matches (0.73 at 4,000) → loops need
  ≥ 5,000 training matches (new parameter `loop.min_train_matches`).
- Limitations: one error model (σ_row 0.5, σ_match 0.2) and 6 snapshots per round; the pooled FKR sits at the 5 %
  boundary, so the tail quantile of B = 2,000 resamples (≈ 7 samples at 0.33 %) adds noise — revisit with B = 5,000 if a
  loop result is borderline.
