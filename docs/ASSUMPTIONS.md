# Assumptions — rules

Everything this project takes for granted but has **not yet verified with CSDS data** is registered with
an ID (`A-NN`) in [`assumptions.yaml`](assumptions.yaml) — the single source of truth (read it directly;
it is short and structured).

## Rules

1. **Every threshold, constant and default** in [`specs/06_parameters.md`](specs/06_parameters.md)
   names its assumption. A new parameter requires a register entry first.
2. **Release gate:** a player-facing capability (`wp_timeline`, `wpa`, `xk`, `economy_feedback`,
   `spatial_feedback`, `player_metrics`, `coaching_feedback`) must not ship while any assumption that
   lists it under `blocks` is `open` or `refuted`. The implementation must enforce this in code, e.g. an
   `assert_ready(capability)` check at every player-facing entry point. A development override may allow
   `open` (never `refuted`) for internal reports only.
3. **Status changes need evidence:** a reproducible experiment report (see CLAUDE.md "Evidence"), an
   ADR, a verified paper, or official CSDS documentation. `supported` and `refuted` come from data;
   `decided` is for policy choices justified in an ADR; `constraint` entries document facts of the
   corpus.
4. **Refuted ⇒ change the design** in the same change set (parameters, specs, ADR) or open a roadmap task.
5. **Synthetic results are never evidence** about CS2 (A-33).
6. Keep entries falsifiable: state the measurable criterion (e.g. "≥ 99% of player-rounds match").

## How each type gets resolved

| Type | Meaning | Resolution |
|---|---|---|
| research | hypothesis from literature/synthesis | experiment on CSDS (milestone MV) |
| data | value/decoding estimable from CSDS | estimate from data, update parameters, record result |
| game_rule | CS2 rule | reconcile against CSDS (`player_status.money`, phase timings) per `build_num`/platform |
| method | statistical/modelling choice | simulation with known truth + ablation on CSDS |
| policy | deliberate choice (gates, display, licensing) | derivation/simulation or user decision → ADR → `decided` |
| causal | counterfactual/effect claim | MV.10 checks, expert review (M9.5), prospective study (M11) |
| constraint | fact of the corpus | documented; design must respect it |
| synthetic | property of the test generator | documentation only |

## Workflow

Assumptions are tested inside the research-driven plan (ADR-0006): the decision points in ROADMAP Part B
consume their results, and each status change that affects the route gets a finding in
`docs/FINDINGS.md`.

Use the skill `resolve-assumption`: design the test → run it in the code repo → record the evidence →
update `status`, `evidence`, parameters and specs here → log it in `docs/PROGRESS.md`.
