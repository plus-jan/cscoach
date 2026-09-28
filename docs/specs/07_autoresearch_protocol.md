# 07 — Autoresearch protocol (how improvement loops may be used)

The project repository is a fork of `uditgoenka/autoresearch` (MIT, ADR-0007). Its loop is: modify one
thing → run `Verify` (a shell command that prints one number) → keep the commit if the number improved,
otherwise `git revert` → log a TSV row → repeat.

That loop is useful for mechanical work. It is also a **selection machine**: across many iterations on
the same validation data, some variant always "improves" a noisy metric by chance. This spec wraps the
loop in the rules of docs/specs/04 so that a kept change is a real improvement. Where this spec and the
upstream autoresearch docs (`guide/`, `.claude/skills/autoresearch/`) disagree, **this spec wins**.

## 1. Which mode for which work

| Work | Mode | Allowed? |
|---|---|---|
| Model/feature/metric changes (WP, xK, calibration, economy …) | Classic `/autoresearch` with the gated `Verify` (§2) | yes, only as specified here |
| Broken pipeline, failing tests, lint/type errors | `/autoresearch:fix`, Guard = tests | yes |
| Bug hunting | `/autoresearch:debug` | yes |
| Challenger vs champion before promotion | `/autoresearch:regression`, then skill `validate-model` | yes (§4) |
| Engineering chores (docs, refactors, performance) | Classic or Orchestrator | yes, with the test suite as Guard |
| Exploration E.x, decision points D1–D5, assumption status changes | — | **no loops**: skill `plan-next-step` / `resolve-assumption` |
| `predict`, `reason`, `probe`, `improve`, `scenario`, `learn` | persona/ideation commands | ideation only (§5) |

The free-form Orchestrator must not make modelling decisions: it may only route to the modes above.

## 2. Gated metric for modelling loops

- **Data:** the loop sees **training matches only**, split into match-grouped K folds (docs/specs/04 §1).
  The calibration fold, the test fold and the temporal holdout are **sealed**: no loop command, script or
  log may read them. The harness asserts this (M2.5).
- **Champion:** the model state at the start of the loop, updated whenever a change is kept.
- **Verify** prints **one number**: the lower bound of the one-sided cluster-bootstrap CI (clusters =
  matches, docs/specs/04 §7) of the **improvement** of the candidate over the champion on the pooled
  out-of-fold predictions, with the primary metric of the task (log-loss for WP and xK unless the task
  says otherwise). Direction: higher is better.
- **Keep rule:** keep iff the printed value is **> 0**. The CI level is corrected for the loop budget:
  one-sided level 1 − `loop.alpha` / `loop.budget` (parameters in docs/specs/06, assumption A-42). The
  raw metric delta is logged but is never the keep criterion.
- **Guard** (a failing guard means revert, whatever the metric says):
  - the unit tests;
  - the leakage denylist test and the "future rows removed" test (docs/specs/02);
  - the split-integrity assertion (no `match_id` in two splits, sealed folds untouched);
  - the calibration gates on out-of-fold predictions per stratum (docs/specs/06, A-06): a change that
    improves log-loss but breaks a stratum's ECE gate is reverted.
- **Seeds:** the fold assignment and the bootstrap seed are fixed for the whole loop and recorded in the
  loop header, so every iteration is compared on identical resamples.

A loop configuration therefore looks like:

```
/autoresearch
Goal: <task id> — <what should improve>
Scope: src/cscoach/<module>/**, configs/<model>.yaml
Metric: lower CI bound of Δlog-loss vs champion (higher is better)
Verify: uv run python -m cscoach.loops.gated_verify --config configs/<model>.yaml
Guard: uv run python -m pytest -q && uv run python -m cscoach.loops.guard --config configs/<model>.yaml --pytest
Iterations: 15
```

(`cscoach.loops.*` was built in M2.5. The task config has a `loop` block — task, data, work_dir, alpha, budget,
n_resamples, seed, gates — and a `model` block; the champion is the `model` block at `HEAD~1`, so loops compare
config-driven variants only. The split is written once with `cscoach.loops.sealed.make_split`. MV.14 confirmed the keep
rule: false-keep rate ≈ 5 % per 15-variant loop and 94 % power for Δlog-loss 0.002 at ~6,900 training matches; loops
need ≥ `loop.min_train_matches` (5,000) training matches.)

## 3. Budget, ledger and the sealed test

- **Budget:** at most `loop.budget` iterations per loop (docs/specs/06). Unbounded runs are not allowed
  for modelling work. Starting a second loop on the same task and data counts against the same budget
  (the variant count accumulates); record it.
- **Ledger:** the autoresearch TSV log (`autoresearch/<subcommand>-<date>/`) is kept and linked from the
  report. The report states the **number of variants tried**, the number kept, and the seeds.
- **Sealed test, once:** after the loop, the final champion gets **one** evaluation on the sealed test
  fold (and the temporal holdout) with skill `validate-model`. That evaluation, not the loop metric, is
  the evidence in `docs/PROGRESS.md` / `docs/FINDINGS.md`. A second sealed-test evaluation of a changed
  model is a new experiment and must be reported as such (with the total count of sealed-test looks).
- **Negative loops are results:** a loop that keeps nothing is a null result and gets a PROGRESS line
  (and a finding if it changes a plan).

## 4. Promotion

`/autoresearch:regression` may compare a challenger with the current production champion, but promotion
follows docs/specs/04 §3 on the sealed test (skill `validate-model`) and is recorded in an ADR. A loop
never promotes a model by itself.

## 5. Persona and ideation commands are not evidence

`predict`, `reason`, `probe`, `improve`, `scenario` and `learn` produce model opinions. Their output:
- is labelled **"ideation — not evidence"** wherever it is stored;
- may seed hypotheses (task E.5), candidate backlog items or ADR discussion;
- may **never** change an assumption status, a parameter value, a gate, a finding or a roadmap tick.

The same holds for any number the upstream tooling produces without a report that meets the CLAUDE.md
"Evidence" standard.

## 6. Evidence and reporting

Each modelling loop writes a report to `reports/experiments/<timestamp>_<name>/` containing the CLAUDE.md
"Evidence" fields (commit, config hash, CSDS revision ids and date range, channel-set version, counts,
ESS, metrics with CIs, gate verdicts) plus: the loop budget, the CI level used, the variant count, the
seeds, and a link to the TSV ledger. Results on synthetic data prove code correctness only (A-33).

## 7. Task → command map

| Roadmap work | Command |
|---|---|
| M2.x pipeline breaks, failing tests | `/autoresearch:fix` (Guard: tests) |
| M2.5 harness, M3.1 baseline code | normal implementation (test-first), `/autoresearch:fix` for red builds |
| M3.2 hyperparameters/features, M3.3 calibration choice, feature ablations (skill `add-model-feature`) | Classic `/autoresearch` with the gated Verify (§2) |
| Challenger vs champion | `/autoresearch:regression` → skill `validate-model` |
| Bugs | `/autoresearch:debug` |
| MV.x verification experiments | no loop: pre-registered experiment, one run, report |
| E.x exploration, D1–D5 | no loop: skill `plan-next-step` |

## 8. Upstream safety hooks

The upstream hooks stay enabled in the project settings: `privacy-block` (protects `.env`, `.aws/credentials`
and other secrets, which matters for the ADX/AWS credentials), `dangerous-cmd-block`, `scout-block` and
`iteration-context`. Do not disable them to make a loop pass.
