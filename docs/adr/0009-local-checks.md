# ADR-0009 — Checks run locally; no remote CI

- Status: accepted
- Date: 2026-09-28
- Roadmap task: M0.6

## Context
ADR-0007 planned to run `scripts/kbcheck.py` and the upstream test suites in GitHub Actions. The project
owner decided that all work, including checks, runs on the local machine. GitHub is only a remote for the
repository (over SSH), not a build service.

## Decision
- The gate is **`scripts/check.sh`**: `scripts/kbcheck.py` plus the upstream suites (hooks, maintenance,
  orchestrator, regression). It must exit 0 before every commit to the default branch and every upstream
  merge. It replaces "CI green" wherever the docs require it.
- Work branches are merged into `master` locally after the gate passes. Pull requests are not required.
- The workflow files in `.github/workflows/` stay (they come from upstream and keep upstream merges clean),
  but their results are not a gate.

## Consequences
- The checks' result is only as good as the machine they run on: run the gate from a clean working tree.
- Amends ADR-0007 (the "run in CI" sentences). Data and experiment runs are local anyway (ADR-0008:
  CSDS stays on local storage).
