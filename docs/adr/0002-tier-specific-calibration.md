# ADR-0002 — Tier-aware WP with per-tier calibration

- Status: accepted provisionally (MV.3 confirms or replaces it)
- Date: 2026-09-28
- Roadmap: M3.3, MV.3 (decides this ADR) · Assumption: A-01

## Context
Research question A/C (unverified, A-01): WP fitted on one skill level misestimates man-advantage value on others.
Separate models per tier fragment data; a single model with `tier` as a feature plus a
per-tier calibration layer shares statistical strength.

Evidence (verified full text): [champ_matchmaking] §5.3 — pooling domains without explicit
conditioning dropped accuracy below the single-domain model (0.6039 vs 0.6559);
[same_player_verification_cs2] §IV-E3 — adding pro demos did not improve an amateur CS2 model.

## Decision
One GBDT with `tier` and `platform` as categorical features + per-tier/platform post-hoc
calibration fit on a held-out calibration fold of CSDS matches. Revisit if per-tier ECE gates fail (then: per-tier models or
hierarchical/partial-pooling models).

## Consequences
Every report must be stratified by tier and platform. Tier label quality (M1.4, MV.2) becomes critical.
