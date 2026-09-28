---
name: check-knowledge-base
description: Consistency check for the cscoach knowledge base (scripts/kbcheck.py + manual items). Run before every commit that changes docs, roadmap, assumptions, parameters or research.
---

Run `python3 scripts/kbcheck.py` first. It automates items 1–4 (except the PROGRESS/deps/F-NN field
checks) and the data-artefact part of 5, and it runs in CI (`.github/workflows/kb-check.yml`). Commit
only after it exits 0 (run it, read the result, then commit). Check the remaining items by hand.

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
4. **Roadmap:** task IDs (`M*.*`, `MV.*`, `E.*`) are unique, deps refer to existing tasks, and ticked
   tasks have a PROGRESS line. Decision points D1–D5 are referenced consistently. Dropped tasks `[-]`
   cite a finding. Findings use unique `F-NN` ids and their required fields.
   No task is ticked in Part C (it must move to Part A first).
5. **Data rule:** no spec or task introduces a data source other than CSDS, or demo parsing (ADR-0003).
6. **Code placement** (ADR-0007): implementation lives in `src/cscoach/`, tests in `tests/cscoach/`,
   configs in `configs/`, reports in `reports/experiments/`; never in `docs/` or in the upstream
   autoresearch paths. No data artefacts (`.pdf`, `.parquet`, `.dem`) anywhere.
7. **Loops** (docs/specs/07): no assumption status, parameter, gate, finding or tick is justified by a
   loop metric or a persona command; only by a report meeting the CLAUDE.md "Evidence" standard.
