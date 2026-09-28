# 04 — Validation protocol

This protocol decides whether a model or metric may be used. The gate values are in docs/specs/06, and
every gate is itself an assumption (A-06…A-10) until MV.5 decides it.

## 1. Data splitting

- **Train / calibration / test** by `match_id` (initial 70/10/20, A-28). Stratify so that each tier,
  platform and map appears in every split: assign whole matches per stratum, using the match's modal
  stratum value.
- **Grouped K-fold** by match for hyperparameter search. The early-stopping slice is taken from
  training *matches*.
- **Temporal holdout:** the most recent revisions / newest `build_num` are held out (drift, A-29).
- **No player holdout:** there is no cross-match identity (ADR-0005). Within a match, player-level
  reliability uses odd/even rounds.
- **Duplicates** are removed before splitting (docs/data/README.md), otherwise one match can sit in
  train and test.
- Every training entry point asserts that no `match_id` appears in two splits.

## 2. Probabilistic metrics (WP, xK)

Brier, log-loss, Brier skill score vs baseline, ECE + MCE (quantile bins), reliability curves, and ROC
AUC (secondary). All are stratified by tier, platform, map, round phase (early / mid / late /
post-plant) and alive state (5v5, 4v5, …, clutches).

**Two kinds of uncertainty; don't mix them up** [brill_yurko_wp_difficulty]:
- **(a) Test-metric CIs** (Brier, ECE, log-loss difference, … on held-out matches, **no refit**): use a
  match-level cluster bootstrap. Every metric and every model difference gets one, plus the ESS.
- **(b) Model-uncertainty CIs** (WP(x) itself, WPA, counterfactual ΔWP, feedback items; the model is
  **refit** on each resample): standard and cluster bootstraps under-cover (0.60 / 0.71 at nominal 0.90
  in simulation). Use the **fractional randomized cluster bootstrap**, with φ tuned in MV.4 on a
  CS simulator fitted to CSDS (A-24).

Reference benchmark (pro CS:GO, not comparable 1:1): XGBoost WP log-loss 0.5353 vs a map-only baseline
of 0.6917 [xenopoulos_valuing_actions_csgo].

## 3. Promotion rule (challenger vs champion)

Promote iff:
- the log-loss improvement CI excludes 0;
- no stratum's ECE worsens beyond its gate;
- the latency budget is met.

Record the promotion in an ADR.

## 4. Player metrics (within match)

Follow the meta-metrics of [franks_meta_analytics], adapted to CSDS (no cross-match identity, ADR-0005):
"player" = player-in-match, "season" = a segment of the match, "games resampled" = rounds resampled.

- **Discrimination (Franks D):** 1 − mean over players of the within-match sampling variance, divided
  by the between-player variance. The sampling variance comes from bootstrapping the player's rounds.
  Computed per match, then averaged over matches within a tier.
- **Stability (Franks S, adapted):** "seasons" = the two match halves (the side switch changes the
  context). S = 1 − E[V_between-halves − sampling var] / (V_total − E[sampling var]), in [0, 1].
- **Reliability (supplementary, not Franks):** odd/even-round split-half correlation with the
  Spearman–Brown correction, i.e. how repeatable the metric is in the same context.
- **Independence (Franks I):** a latent Gaussian-copula correlation of the metrics (rank likelihood).
  I = 1 − R² of the metric's latent variable on the reference set (K/D, ADR, KAST, HLTV-style rating).
  Plain OLS on raw values is only a quick approximation.
- **Population stability:** the metric's distribution per tier is stable across revision months
  (e.g. via the Wasserstein distance).
- **Purpose:** say whether a metric serves *attribution* (chance and context count as signal) or
  *prediction/habit* (they count as noise), and apply the gates accordingly.

Metrics below the gates stay internal (A-08). Whether this adaptation behaves sensibly is A-25 (MV.9).

## 5. Coaching validity

Counterfactual ΔWP always comes with a CI; items whose CI contains 0 are not called "mistakes".
Validation happens in three stages: the counterfactual checks (MV.10), an expert review (M9.5) and a
prospective study (M11).

## 6. Reporting

Every run writes `metrics.json`, which contains:
- code commit, config hash, CSDS revision ids + date range, channel-set version;
- n_matches, n_rounds, n_rows, ESS;
- all metrics with CIs, the per-stratum tables, and the gate verdicts.

## 7. Reference algorithms (implement exactly; tests must cover the listed properties)

**Metrics.**
- Brier = mean((p − y)²).
- Log-loss with p clipped to [1e−12, 1 − 1e−12].
- BSS = 1 − Brier(p)/Brier(p_ref).
- Reliability curve: bin by p; quantile edges are made unique, with the first/last edge set to 0 and 1;
  per bin, record mean p, mean y and count (drop empty bins).
- ECE = Σ (count_b/N)·|mean_y_b − mean_p_b|; MCE = max_b |·|.
- Tests: ECE < 0.01 on 50k perfectly calibrated samples; ECE > 0.1 when p is shifted by +0.15.

**Grouped split.** Shuffle the groups within each stratum with a seeded RNG, then cut them by
fractions. Assert that the groups are disjoint and complete. Test: every stratum appears in the test split.

**ICC(1) (one-way ANOVA).**
- k clusters of sizes n_i, N = Σn_i;
- MSB = Σ n_i (ȳ_i − ȳ)² / (k − 1), MSW = ΣΣ (y − ȳ_i)² / (N − k);
- n₀ = (N − Σn_i²/N)/(k − 1);
- ICC = (MSB − MSW)/(MSB + (n₀ − 1)·MSW), clipped to [0, 1].

**Design effect (Kish, unequal clusters)** = 1 + ((CV² + 1)·m̄ − 1)·ICC, where m̄ is the mean cluster size
and CV its coefficient of variation. **ESS** = N / DEFF.
- Apply to the labels or the calibration residuals (y − p), clustered by `round_uid` (and by match for
  match-level questions).
- Tests: ESS ≈ the number of clusters when values are constant within clusters; DEFF = 1 when ICC = 0.

**Cluster bootstrap (test metrics, no refit).** Resample whole clusters (matches) with replacement B
times, recompute the statistic, and take percentile CIs. For model comparisons, bootstrap the
*difference* on the same resample. Test: the CI is much wider than the naive iid CI when ICC is high.

**Fractional randomized cluster bootstrap (model uncertainty, refit)** [brill_yurko_wp_difficulty].
For b = 1..B:
1. sample ⌈φ·G⌉ matches with replacement;
2. within each sampled match, resample its snapshots (or rounds) with replacement;
3. refit the model;
4. predict at the query states.

Take the α/2 and 1 − α/2 quantiles. Clip the interval to [0, 1], widening it to 0 or 1 when the estimate
is < 0.025 or > 0.975. Tune φ so that the nominal coverage is reached **in the MV.4 simulator** (the
reference value from football is φ ≈ 0.35 for 90%). Test: coverage on synthetic data with known truth.

**Franks discrimination (within match).** For each player i: Var_boot(mean of i), with rounds resampled.
D = 1 − mean_i Var_boot / Var_between(player means), clipped to [0, 1].

**Franks stability (halves).** Per player, the two half means x̄_i1 and x̄_i2 and their bootstrap
sampling variances v_i1 and v_i2:
- numerator: mean_i[Var(x̄_i1, x̄_i2) − mean(v_i1, v_i2)];
- denominator: Var(all half means) − mean(all v).

S = 1 − numerator/denominator, clipped to [0, 1]. Test: S ≈ 1 for a constant per-player effect with
noise, and S ≈ 0 when the half means are independent.

**Split-half reliability (supplementary).** Order each player's rounds, split odd/even, correlate the
half-means across players (r), then apply Spearman–Brown: 2r/(1 + r).

**Franks independence.** Transform each metric to normal scores (ẑ = Φ⁻¹(F̂(x))). Estimate the latent
correlation matrix C (rank-likelihood Gaussian copula, e.g. Hoff's `sbgcop` or an equivalent). Then
I = 1 − R², with R² = C_mM C_MM⁻¹ C_Mm.

**Normal–normal shrinkage (per tier prior).**
- Per player: mean x̄_i, n_i; σ² = pooled within-player variance; se_i² = σ²/n_i;
- μ = n-weighted mean of the x̄_i;
- τ² = max(Var(x̄_i) − mean(se_i²), ε);
- w_i = τ²/(τ² + se_i²); posterior mean = w_i·x̄_i + (1 − w_i)·μ;
- posterior sd = (1/τ² + 1/se_i²)^(−1/2).

Test: a player with 2 rounds is shrunk more than one with 40. Heavy tails → A-26.

**Per-tier calibration.** A global calibrator plus one per tier with ≥ `min_rows_per_tier` calibration
rows. Use isotonic regression (clip to [1e−6, 1 − 1e−6]) if the rows ≥ `isotonic_min_rows`, else Platt
(logistic on logit(p)). Fit only on the calibration fold.

**Shapley credit.** Exact for ≤ 7 contributors, otherwise Monte-Carlo over permutations (seeded).
Tests: efficiency (Σφ = v(all) − v(∅)), symmetry, null player.

**WPA telescoping (potential property).** Over a round, Σ event WPA (CT perspective, with contiguous
before/after states) = outcome − WP at freeze end [tar2_credit_assignment]. A test fails if gaps between
events are not covered, e.g. by "drift" terms that account for time passing without events.

**Grounding check for text.** Extract all numbers from the text (regex `-?\d+(?:[.,]\d+)?`, with the
thousands separator removed). Every number must appear in the payload's allowed set, including round
numbers and ticks. This checks presence only (A-31).

**Synthetic generator (tests only, A-33).** Rounds are simulated as sequences of kills. Each kill goes
to CT with probability σ(skill + equipment edge + a·disc·(alive_ct − alive_t) − b·planted + noise),
where the tier "discipline" sets the conversion of a man advantage. A snapshot is taken before each
kill, so the snapshots are clustered like real data. Use it to test code paths and CI coverage (the
truth is known), never as evidence about CS2.
