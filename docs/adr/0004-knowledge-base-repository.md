# ADR-0004 — This repository contains concepts only; code lives elsewhere

- Status: accepted
- Date: 2026-09-28

## Context
The project owner wants a repository that AI agents can act on: goals, specs, data description,
assumptions, research and roadmap. Implementation details should not accumulate here.

## Decision
- This repo holds **no code**: no packages, scripts, tests, CI or configs.
- Algorithms that were prototyped earlier are preserved as **reference algorithms** in
  `docs/specs/04_validation_protocol.md` §7. Parameter values live in `docs/specs/06_parameters.md`.
- Implementation happens in a separate code repository (to be created by the user). A `src/` may be
  added here only through a superseding ADR.
- Agents implementing tasks report back here (roadmap ticks, PROGRESS, assumption statuses, spec updates).
- Converting research PDFs to markdown is a documented procedure (skill `add-paper`), not a script.

## Consequences
Enforcement that used to live in tests (registry consistency, config tags, leakage denylist) is now:
(a) a checklist in the skills for this repo, and (b) a requirement on the code repo, which must
implement those tests.
