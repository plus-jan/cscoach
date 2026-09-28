# ADR-0007 — The project repository is a fork of autoresearch; code lives next to the knowledge base

- Status: accepted (fork `plus-jan/cscoach` created 2026-09-28; migrated in M0.6)
- Date: 2026-09-28
- Roadmap task: M0.6
- Supersedes: ADR-0004

## Context
ADR-0004 kept this repository docs-only and deferred code to a separate repository that did not exist
yet. The project owner chose to build on `uditgoenka/autoresearch` (MIT, v2.2.2), a Claude Code /
OpenCode / Codex skill pack that runs goal-directed improvement loops (modify → one mechanical metric →
keep or `git revert` → TSV log) with 14 subcommands (plan, debug, fix, regression, …) and safety hooks.
The owner chose to **fork it as the new base** and to make that fork **the code repository**.

Risk: an unguarded keep/revert loop over a noisy validation metric is selection bias. It "finds"
improvements that are noise, and it can touch held-out data. Its persona commands produce opinions,
which our evidence standard (CLAUDE.md) does not accept.

## Decision
- A fork of autoresearch (proposed name `plus-jan/cscoach`) becomes the **single project repository**:
  the upstream tooling (kept in its upstream paths so upstream merges stay cheap) + this knowledge base
  (migrated with its git history) + the implementation (`src/cscoach/`, `tests/cscoach/`, `configs/`,
  `reports/`) once work starts.
- The knowledge base (`CLAUDE.md`, `ROADMAP.md`, `docs/`, `.claude/skills/<cscoach skills>`) remains the
  source of truth. The upstream `docs/*.md` files describe autoresearch itself, not cscoach.
- Loops are allowed **only under docs/specs/07_autoresearch_protocol.md**: gated keep rule (CI lower
  bound of the improvement > 0, corrected for the loop budget), training matches only, sealed test
  evaluated once, bounded budget, variant ledger, persona commands = ideation only.
- Code is now allowed in the project repository. The consistency checklist becomes a script
  (`scripts/kbcheck.py`) run in CI (amended by ADR-0009: checks run locally via `scripts/check.sh`). The rest of ADR-0004 (reference algorithms in docs/specs/04 §7,
  parameter values in docs/specs/06, report-back duties) stays in force.
- Upstream sync: `scripts/sync_upstream.sh` on a work branch (merge, `.gitignore` union, refresh
  `guide/AUTORESEARCH.md` and the badge, run all checks). `README.md` is ours (`merge=ours`), and the
  upstream README is kept as `guide/AUTORESEARCH.md`. Our README carries the MIT notice and the upstream
  version badge (an upstream parity test checks it; refresh it when an upstream merge bumps the version).
- Unchanged: ADR-0003 (CSDS is the only data source), ADR-0005 (within-match player metrics, no
  re-identification), ADR-0006 (research-driven planning).

## Consequences
- Positive: one repository for plan, evidence and code; a ready loop runner for fixes, debugging and
  gated model search; upstream safety hooks (privacy-block protects the AWS credentials).
- Negative: upstream files (docs, tests, CI) sit next to ours and must be kept apart
  (`scripts/kbcheck.py` checks only cscoach paths); upstream CI runs on our PRs (not a gate since ADR-0009).
- Follow-ups: M0.6 (migration, done with `scripts/migrate_to_autoresearch_fork.sh`), M2.5 (gated loop
  harness), MV.14 (simulation of the false-keep rate of the gated loop, A-42).
  `plus-jan/cscoach-template` gets a pointer to this repository and is archived.
