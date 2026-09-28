---
name: next-task
description: Pick up and complete the next open task from ROADMAP.md following the repo's accuracy rules. Use when asked to "continue the project", "do the next task", or work on a roadmap ID like M3.2 or MV.3.
---

This repository is a knowledge base (no code, ADR-0004). Implementation happens in the code repository.

1. Read `CLAUDE.md`, then `ROADMAP.md` and `docs/FINDINGS.md`. Use the given task ID, or take the first
   `[ ]`/`[~]` task **in Part A** whose deps are `[x]`. If the requested task is in Part C (provisional),
   or no Part A task is startable, stop and run `plan-next-step` instead.
2. Gather context before acting:
   - the spec sections the task names (`docs/specs/`);
   - every `[paper_id]` → the notes block of `docs/research/papers/<id>.md`. If a cited paper has no
     local full text, say so and suggest the `add-paper` skill;
   - every `[A-NN]` → `docs/assumptions.yaml` (status, criterion, what it blocks);
   - the relevant parameters in `docs/specs/06_parameters.md`;
   - data: `docs/data/README.md` + `docs/data/csds_spec.md` (CSDS only, official libraries only).
3. If code is needed and no code repository is available in the session, stop. Ask the user for it (or
   for approval to create one). Never add code to this repository.
4. In the code repo: write the tests first (the reference algorithms in docs/specs/04 §7 list the
   required properties), implement, run the checks, and produce a reproducible report (CLAUDE.md
   "Evidence").
5. Report back here, in one change set:
   - tick the task in `ROADMAP.md`;
   - add a line to `docs/PROGRESS.md` (date, task, key numbers, report link);
   - update the assumption statuses and evidence (skill `resolve-assumption`) and the parameter values;
   - add a finding (F-NN) to `docs/FINDINGS.md` if the result changes beliefs or plans (null results
     too). If the task completes the inputs of a decision point, say so and suggest `plan-next-step`;
   - update the specs/ADRs if behaviour or decisions changed.
6. Run the `check-knowledge-base` checklist, then commit as `<task-id>: <summary>`.
7. Summarise for the user: what was done, the numbers with CIs, which assumptions changed status, and
   what is still blocked.
