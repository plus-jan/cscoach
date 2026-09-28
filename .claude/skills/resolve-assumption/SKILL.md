---
name: resolve-assumption
description: Test, decide or update an entry in docs/assumptions.yaml (A-NN) with evidence. Use when a task touches an assumption, when new data/results bear on one, or when asked which assumptions are open or blocking a capability.
---

1. Read the entry in `docs/assumptions.yaml` and the rules in `docs/ASSUMPTIONS.md`. Identify its type,
   because the type decides how it gets resolved.
2. **Design the test** before looking at the results: the metric, the success criterion (make the
   statement falsifiable if it isn't), the data slice (CSDS revisions, tiers/platforms), and the
   uncertainty method.
3. Run it in the code repo and produce a reproducible report (CLAUDE.md "Evidence").
4. Update the entry:
   - `status`: supported / refuted / decided (policy only, with an ADR);
   - `evidence`: links to the report/ADR/paper;
   - the statement, only to record a refined criterion; never rewrite history, add a note instead.
5. Propagate the result:
   - parameter values in `docs/specs/06_parameters.md`;
   - affected specs and ADRs;
   - if **refuted**, stop dependent work and open or adjust roadmap tasks.
6. Log it in `docs/PROGRESS.md`.
7. For "what is blocking capability X?": list the entries whose `blocks` contains X and whose status is
   open/refuted, with their `test` tasks.
