# CLAUDE.md — Operating manual for AI agents

This repository is the **knowledge base** for **cscoach**: a data-driven coaching engine for amateur and
semi-pro Counter-Strike 2 players. It contains **no code**, only the concepts an agent needs to build,
validate and extend the system: goals, specs, data description, assumptions, roadmap, research.
Implementation happens in a separate code repository (or an explicitly approved `src/` later, see
ADR-0004). This repo stays the source of truth: agents that implement report results back here.

The engine turns **PureSkill.gg CSDS match data** into calibrated **Win Probability (WP)**, **Win
Probability Added (WPA)**, **Expected Kills (xK)**, economy and spatial metrics, and then into
**counterfactual, actionable coaching feedback**.

The overriding goal is **accuracy you can prove**. A metric that is not calibrated, validated on held-out
*matches*, and backed by verified assumptions must never reach a player.

## Map of this repository

| Path | What it is | Read when |
|---|---|---|
| `ROADMAP.md` | Part A committed tasks, Part B decision points (D1–D5), Part C provisional backlog | always, to pick work |
| `docs/FINDINGS.md` | Results from our data, the decisions they drove and the next step chosen | before planning or deciding |
| `docs/specs/01_architecture.md` | Pipeline and components (CSDS → tomes → features → models → feedback) | any design/implementation |
| `docs/specs/02_data_contracts.md` | Derived tables and how each column is built from CSDS channels | building data/features |
| `docs/specs/03_models.md` | WP, xK, WPA, economy, spatial, player-level math | modelling |
| `docs/specs/04_validation_protocol.md` | Splits, metrics, gates, **reference algorithms** | anything evaluated |
| `docs/specs/05_coaching_feedback.md` | Feedback lifecycle, tone, grounding | coaching output |
| `docs/specs/06_parameters.md` | Every threshold/constant with its initial value and assumption ID | configuring anything |
| `docs/data/` | CSDS corpus guide, vendored channel spec + data dictionary | any data work |
| `docs/assumptions.yaml` + `docs/ASSUMPTIONS.md` | Register of unverified premises (A-NN) + rules | before relying on any number |
| `docs/research/` | `sources.yaml` registry, `papers/` full texts with notes, German synthesis | design decisions |
| `docs/adr/` | Architecture Decision Records | before changing a decision |
| `docs/PROGRESS.md` | Log of completed work and key numbers | after every task |
| `.claude/skills/` | Workflows: next-task, plan-next-step, validate-model, add-model-feature, resolve-assumption, add-paper, check-knowledge-base | as named |

## How to work

0. **The route is a hypothesis; the rules are not** (ADR-0006). The pipeline in docs/specs/01 is the
   current best guess. Results decide the next step. Only tasks in ROADMAP **Part A** are committed.
1. **Pick a task** from ROADMAP Part A: the first open one whose dependencies are done (skill
   `next-task`). Never start Part C items directly. When a decision point's inputs are complete, or Part
   A runs out, run `plan-next-step` and get the user's approval for the next batch.
2. **Read before acting:** the spec sections the task names; the `[paper_id]` notes it cites
   (`docs/research/papers/<id>.md`); the assumptions `[A-NN]` it touches (`docs/assumptions.yaml`).
3. **Data only from CSDS** via `pureskillgg-dsdk` / `pureskillgg-csgo-dsdk` (`docs/data/README.md`).
   New features must be computable from CSDS channels. No demo parsing, no external datasets.
4. **Implement in the code repository**, test-first, following the specs and the reference algorithms in
   `docs/specs/04_validation_protocol.md`. Every run writes a reproducible report (see "Evidence").
5. **Report back here, in the same change set:** tick the task in `ROADMAP.md`, add a line to
   `docs/PROGRESS.md`, update `docs/assumptions.yaml` statuses with evidence, and update specs/ADRs if
   behaviour or decisions changed. Results that change beliefs or plans also get a **finding** in
   `docs/FINDINGS.md`, including null results.

## Non-negotiable accuracy rules

- **Split by match, never by row/tick/round.** Snapshots in a round share one outcome; rounds in a match
  share players. Add a **temporal split** by revision date / `header.build_num` for drift. (There is no
  cross-match player identity, so "player holdout" is replaced by match holdout. See ADR-0005.)
- **No future information in features.** A feature at tick *t* uses only data with tick ≤ *t*. Round
  outcome, final scores, `round_end` fields and later events are forbidden. Keep a denylist and test it.
- **Always compare to a baseline** with **cluster-bootstrap CIs over matches**.
- **Calibration is first-class:** Brier, log-loss, ECE (quantile bins), reliability curves *per tier,
  per map, per round phase, per platform*. Gates: `docs/specs/06_parameters.md`.
- **Honest uncertainty:** report effective sample size and use cluster-level resampling. Never use naive
  row-level standard errors.
- **Tier awareness:** don't apply a model fitted on one tier/platform to another without verified
  calibration (assumption A-01).
- **Player metrics are within-match:** shrink toward the tier prior, show intervals, and pass the
  within-match reliability checks before display.
- **Assumption gate:** no player-facing capability ships while an assumption that `blocks` it is `open`
  or `refuted` (`docs/ASSUMPTIONS.md`). Every threshold/constant must have an assumption ID in
  `docs/specs/06_parameters.md`. Add a register entry before introducing a new one.
- **Game constants are configuration**, never hard-coded, and are verified against CSDS
  (`player_status.money`, `tick`/`round_state` phases). Tag every match with `build_num`.
- **Never invent numbers in coaching text.** Only engine-computed values; never literature numbers.
- **Respect the data license** (CC BY-NC-SA 4.0 DSA): non-commercial, attribute "Data provided by
  PureSkill.gg.", share derived data alike, never attempt re-identification.

## Evidence

A claim counts as evidence only if it is reproducible. The report must contain the code-repo commit, the
config hash, the CSDS revision ids and date range, the channel-set version, the counts (matches, rounds,
rows), the ESS, metrics with CIs, and gate verdicts. Store reports in the code repo
(`reports/experiments/<timestamp>_<name>/`) and link them from `docs/PROGRESS.md` / `docs/assumptions.yaml`.
Results on synthetic data prove code correctness only, never facts about CS2 (A-33).

## Research references

Full-text papers: `docs/research/papers/<id>.md` (index and rules in its README). Consult them before
designing a model, feature, metric, validation step or feedback format. Cite by `sources.yaml` id as
`[id]`. Trust order: paper full text > its cscoach notes > `sources.yaml` > `research_synthesis_de.md`
(the synthesis has known errors). Only `verified: true` entries justify decisions; `verified: notes` (e.g. HLTV articles) may support conventions, not evidence. Missing full text →
list it in the papers README and ask the user for the PDF (skill `add-paper`).

## Conventions

- Perspective: probabilities are from the **CT side** unless suffixed `_t`; `wp_ct + wp_t = 1`; WPA is
  signed from the acting player's team perspective.
- Time: CSDS `second` (derived from `tick` and `header.tick_rate`); ticks as int; read the tick rate from
  the header, never assume it.
- Names: snake_case; derived-table columns as in `docs/specs/02_data_contracts.md`.
- Randomness: seeded. Every stochastic step records its seed.

## When blocked

- Missing CSDS access → ask the user (ADX subscription approval + AWS credentials). Meanwhile, build
  and test logic on synthetic data, and mark the task `[~]` with what still needs real data.
- An assumption turns out false → set it to `refuted` with evidence, stop dependent work, and propose the
  design change (ADR).
- Unverified research claim → don't use it as justification; request the paper.
