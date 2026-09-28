# ADR-0002 — Tier-aware WP with per-tier calibration

- Status: accepted (to be confirmed by experiment M3.5)
- Date: 2026-09-28
- Roadmap task: M3.3, M3.5

## Context
Research question A/C: pro-trained WP overestimates man-advantage value in low tiers.
Separate models per tier fragment data; a single model with `tier` as a feature plus a
per-tier calibration layer shares statistical strength.

Evidence (verified full text): [champ_matchmaking] §5.3 — pooling domains without explicit
conditioning dropped accuracy below the single-domain model (0.6039 vs 0.6559);
[same_player_verification_cs2] §IV-E3 — adding pro demos did not improve an amateur CS2 model.

## Decision
One GBDT with `tier` as categorical feature + per-tier post-hoc calibration fit on a
held-out calibration fold. Revisit if per-tier ECE gates fail (then: per-tier models or
hierarchical/partial-pooling models).

## Consequences
Every report must be stratified by tier. Tier label quality (M1.3) becomes critical.
