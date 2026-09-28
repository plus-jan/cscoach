---
name: check-knowledge-base
description: Consistency checklist for this docs-only repository (replaces automated tests). Run before every commit that changes docs, roadmap, assumptions, parameters or research.
---

Check each item and fix any problem before committing. The quick checks can be done with `grep` / a
short Python one-off in the scratchpad (never commit scripts).

1. **Assumptions register** parses as YAML:
   - IDs are unique;
   - `type`/`status` values are valid (docs/ASSUMPTIONS.md);
   - every non-`open` entry has `evidence`;
   - every `test` task ID exists in `ROADMAP.md`;
   - every `blocks` value is a known capability.
2. **Parameters:** every row in `docs/specs/06_parameters.md` names an existing `A-NN`. Every
   `parameters:` key in the register matches a row.
3. **Citations:**
   - every `[id]` containing `_` in CLAUDE.md, ROADMAP.md and docs/ (excluding paper full texts) exists
     in `docs/research/sources.yaml`;
   - every `[A-NN]` exists in the register;
   - every `local:` path exists, and every `docs/research/papers/*.md` (except README) is registered and
     has a finished notes block (no TODO);
   - `verified: true` and `verified: notes` require `local`.
4. **Roadmap:** task IDs are unique, deps refer to existing tasks, and ticked tasks have a PROGRESS line.
5. **Data rule:** no spec or task introduces a data source other than CSDS, or demo parsing (ADR-0003).
6. **No code** in this repo: no source files, scripts, configs or CI (ADR-0004).
