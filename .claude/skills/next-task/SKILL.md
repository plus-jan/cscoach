---
name: next-task
description: Pick up and complete the next open task from ROADMAP.md following the repo's accuracy rules. Use when asked to "continue the project", "do the next task", or work on a roadmap ID like M3.2.
---

1. Read `CLAUDE.md` (rules) and `ROADMAP.md`. If a task ID was given, use it; otherwise
   choose the first `[ ]`/`[~]` task whose dependencies are `[x]`.
2. Read the relevant spec sections in `docs/specs/` and the target modules/stubs
   (search for `NotImplementedError("<task-id>`). Read the *cscoach notes* of every paper
   cited as `[id]` in the task/spec (`docs/research/papers/<id>.md`); if a cited paper has no
   local full text, say so in your report.
3. Write or extend tests first (`tests/unit/...`; use `cscoach.synthetic` if no real data).
4. Implement. Keep public signatures unless an ADR in `docs/adr/` changes them.
5. Run `make check`. Fix everything until green.
6. For model tasks, run the `validate-model` skill and paste key numbers.
7. Tick the task in `ROADMAP.md`, append to `docs/PROGRESS.md`, update specs if the
   behaviour changed, commit as `<task-id>: <summary>`.
8. Report: what was done, numbers, what remains / needs real data.
