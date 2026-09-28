# ADR-0003 — PureSkill.gg CSDS is the sole data source; no demo parsing

- Status: accepted
- Date: 2026-09-28
- Roadmap: M1, all feature work

## Context
The earlier plan parsed `.dem` files with demoparser2 and mixed several sources (local demos, FACEIT API,
HLTV, external nav meshes). The project owner decided to base everything on one curated, rank-labelled
amateur corpus accessed through official tooling.

## Decision
- Data: **PureSkill.gg Competitive CS2 Gameplay Data Set (CSDS)** from AWS Data Exchange only.
- Access: official libraries `pureskillgg-dsdk` (ADX export, `GameDsLoader`, tomes) and
  `pureskillgg-csgo-dsdk` (`pop_overtime`, PII tooling).
- **All derived features must be computable from CSDS channels.** No demo parsing, scraping, external
  datasets or external map/nav data (the spatial model uses an empirical area graph, A-37).

## Consequences
- Removed: demoparser2 ingestion, the external-data plans, and nav-mesh sourcing from awpy.
- Gained: rank labels (`player_info`), engineered columns (velocities, equipment values, place names),
  per-tick telemetry, and a steady daily supply (~90–150 matches/day), with about a year retained.
- New constraints: no cross-match identity (ADR-0005); CC BY-NC-SA 4.0 DSA (A-38); a corpus sample
  bias (A-34); the channel-set change in Aug 2026 (A-39).
- Pro-level data is not in scope. The pro-vs-amateur question (A-01) becomes "across tiers/platforms
  within CSDS", and pro evidence comes only from the literature.
