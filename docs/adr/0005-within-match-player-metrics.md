# ADR-0005 — Player metrics and coaching are within-match

- Status: accepted
- Date: 2026-09-28
- Assumption: A-35 (constraint)

## Context
In CSDS, `player_personal.steam_id` is replaced by a per-match alias (A, B, C…), so the same person
cannot be linked across matches (docs/data/csds_spec.md, "Redaction"). Attempts to re-identify players
are forbidden by the DSA.

## Decision
- Player-level values are computed and reported **per match** only.
- Reliability is measured within a match (odd/even rounds). Discrimination and population stability
  are measured across matches.
- Shrinkage priors are **tier-level**, estimated across matches, never per person.
- "Player holdout" splits are replaced by match holdout (the same person may appear in train and test
  under different aliases; this is accepted and noted as a limitation).
- Longitudinal coaching and the prospective effect study (M11) need a consented data route with identity
  → a separate ADR is required before any such work.

- **Never attempt to re-link players across matches**, including indirectly through behavioural
  fingerprints. [same_player_verification_cs2] shows that low-level mechanics identify players with AUC
  ≈ 0.93–0.98, so such linking is technically feasible and explicitly out of bounds. Features may
  describe behaviour within a match; they must not be used to match aliases across matches.

## Consequences
Cross-match player ratings (e.g. the OpenSkill-style ratings from [pandaskill]) are out of scope. The
within-lobby "free-for-all" ranking idea still applies within a match.
