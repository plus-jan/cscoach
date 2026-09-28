# CLAUDE.md — Operating manual for Claude Code

This repository builds **cscoach**: a data-driven coaching engine for amateur and
semi-pro Counter-Strike 2 players. It turns `.dem` files into calibrated
**Win Probability (WP)**, **Win Probability Added (WPA)**, **Expected Kills (xK)**,
economy and spatial-control metrics, and then into **counterfactual, actionable
coaching feedback**.

The overriding goal is **accuracy you can prove**. A metric that is not calibrated,
validated on held-out *matches*, and stable across samples must never reach a player.

## How to work in this repo

1. **Find the next task**: open `ROADMAP.md`, take the first unchecked task whose
   dependencies are done (or run the `/next-task` skill). Every task has an ID
   (e.g. `M4.2`), target modules, and a Definition of Done (DoD).
2. **Read the spec first**: `docs/specs/*` define data contracts, model math and
   acceptance gates. Code must match the spec; if the spec is wrong, update the spec
   *in the same commit* and add an ADR in `docs/adr/` for non-trivial decisions.
3. **Stubs are the contract**: functions raising `NotImplementedError("M<x>.<y>: ...")`
   are placeholders whose signatures and docstrings are the interface. Keep the
   signature unless the ADR says otherwise.
4. **Test-first**: write/extend tests in `tests/` before or with the implementation.
   Use the synthetic generator (`cscoach.synthetic`) when real demos are unavailable.
5. **Run the checks** before every commit: `make check` (ruff + mypy + pytest).
6. **Tick the box** in `ROADMAP.md` and append a line to `docs/PROGRESS.md`
   (date, task ID, what changed, key numbers).
7. Commit small, one task per commit: `M4.2: per-tier isotonic calibration`.

## Non-negotiable accuracy rules

These exist because the naive version of every metric here is silently wrong.

- **Split by match, never by row/tick/round.** Snapshots within a round share one
  outcome; rounds within a match share players/teams. Use
  `cscoach.validation.splits.grouped_split` / `assert_no_group_leakage`. For player
  metrics, additionally hold out *players*. For deployment realism, also run a
  *temporal* split (train on older patches, test on newer).
- **No future information in features.** A WP feature at tick *t* may only use data
  with tick ≤ *t*. Round outcome, final scores, `round_end` reason, post-*t* kills are
  forbidden. `tests/unit/test_leakage_guard.py` enforces a denylist; extend it.
- **Always compare to a baseline.** Every model reports its lift over
  `models.baseline_wp` (logistic on alive counts, HP, bomb, time) or the relevant
  baseline, with **cluster-bootstrap CIs** (clusters = matches).
- **Calibration is a first-class metric.** Report Brier, log-loss, ECE (quantile
  bins), and reliability curves *per skill tier and per map*. WP values that feed WPA
  must pass the gates in `configs/validation.yaml`.
- **Honest uncertainty.** Snapshots are autocorrelated: use effective sample size
  (`validation.ess`) and cluster bootstrap for every CI. Never use naive row-level
  standard errors.
- **Tier-specific models.** A pro-trained WP curve is invalid for amateurs. Either
  train per tier or condition on tier + recalibrate per tier; verify per-tier ECE.
- **Player metrics need shrinkage + meta-analytics.** Before a per-player metric is
  shown, it must pass stability/discrimination/independence checks
  (`validation.meta_analytics`) and be shrunk toward the tier prior
  (`coaching.shrinkage`). Show intervals, not point estimates, to players.
- **Every number in a report is reproducible**: gates and experiments write JSON to
  `reports/experiments/<timestamp>_<name>/` with config hash, git SHA, data manifest.
- **Game-rule constants live in `configs/`**, never hard-coded (economy values change
  with CS2 patches). Tag every match with its game build/patch.
- **Never invent numbers in coaching text.** Natural-language feedback may only
  reference values computed by the engine (see `docs/specs/05_coaching_feedback.md`).

## Layout

```
configs/            YAML configs: data sources, tiers, economy rules, models, validation gates
data/               raw/ (demos), interim/ (parsed parquet), processed/ (model tables) — git-ignored
docs/specs/         THE specs: architecture, data contracts, models, validation, coaching
docs/research/      Literature synthesis (German original) + source registry w/ verification status
docs/adr/           Architecture Decision Records
src/cscoach/
  schemas/          Data contracts (column specs + validators) for every table
  ingest/           demoparser2 wrapper, dataset loaders (PureSkill, FACEIT, local demos)
  preprocess/       Round segmentation, tick sampling, state snapshots
  features/         State (WP), duel (xK), economy, spatial features
  spatial/          Map geometry, nav graph, utility delay (shortest-path deltas)
  economy/          CS2 economy rules engine, buy classification, team sync
  models/           Baseline WP, GBDT WP, xK, tier calibration, model registry
  valuation/        WPA, credit assignment (Shapley), xK×WPA decision matrix
  validation/       Splits, metrics, calibration, ESS, cluster bootstrap, meta-analytics, gates
  coaching/         Shrinkage, counterfactuals, recommendations, narrative rendering
  api/              FastAPI service for dashboards
  pipeline/         CLI (`cscoach ...`) and end-to-end orchestration
tests/unit, tests/integration
```

## Commands

```
make install      # pip install -e ".[dev,parse,api]"
make check        # lint + typecheck + tests (must pass before commit)
make test         # pytest -q
cscoach --help    # CLI entry point
cscoach validate --model wp --run <dir>   # evaluate against configs/validation.yaml gates
```

## Conventions

- Python 3.11, type hints everywhere, `ruff` formatting, numpy-style docstrings.
- DataFrames: pandas at model boundaries; polars allowed in ingest (demoparser2 returns
  polars/pandas). Column names follow `docs/specs/02_data_contracts.md` (snake_case).
- Perspective convention: probabilities are **from the CT side** unless a column says
  `_t`. `wp_ct + wp_t == 1`. WPA is signed from the acting player's team perspective.
- Coordinates in game units; time in seconds since round freeze-time end
  (`round_time_s`); ticks as int (CS2 demos: 64 ticks/s — read from header, don't assume).
- Randomness: every function with randomness takes `seed` / `rng`.
- Don't commit data, demos, or model binaries. Model artefacts go to `models/`
  (git-ignored) with a JSON card.

## When blocked

- Missing real data → build/extend the synthetic generator and proceed; mark the task
  `[~]` (partially done) with a note on what needs real-data verification.
- Unverified research claim → check `docs/research/sources.yaml`; claims marked
  `unverified` must not be used as design justification without checking the source.
