# ADR-0001 — Match-grouped splits and cluster-bootstrap uncertainty

- Status: accepted
- Date: 2026-09-28
- Roadmap task: M0.2

## Context
WP training rows are snapshots. All snapshots of a round share one label and all rounds
of a match share players, teams, map and server. Row-level random splits leak identity
and outcome information and produce optimistic metrics; row-level standard errors are
too narrow (clustered outcomes, cf. research section H).

## Decision
- All train/calibration/test splits are grouped by `match_id`.
- All confidence intervals use cluster bootstrap over matches.
- Effective sample size (Kish design effect from the within-round ICC) is reported next
  to raw row counts.

## Consequences
Metrics will look worse than naive ones — this is intended. Small tiers may be unable to
support per-tier isotonic calibration; fall back to Platt scaling (see configs).
