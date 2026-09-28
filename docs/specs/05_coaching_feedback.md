# 05 — Coaching feedback

Research basis [gig_economy_esports_coaching] (read its notes):
- players value individualised, *situated* diagnosis over raw dashboards and distrust generic tips;
- authority must be visible (benchmarks vs. own tier, linked evidence);
- insights expire with patches;
- descriptive feedback ("you lost 15% WPA") is not prescriptive.

Feedback must therefore be **counterfactual, specific, few, and honest about uncertainty**.

Scope: feedback is generated **per match** for the players in a CSDS match (no cross-match identity,
ADR-0005). Longitudinal coaching of a person is out of scope unless a future data source provides
identity. Any such source must itself be CSDS-compatible and approved via an ADR.

## Feedback item lifecycle

1. **Detect:** candidate mistakes, each with evidence rows (CSDS channel + round + tick):
   - `risky_duel`: xK < θ₁ while WP-if-avoided > θ₂ (A-05);
   - `untraded_death` / `no_trade_position`: a teammate could have traded (area-graph transit time <
     trade window, A-17) but was not positioned;
   - `desync_buy`: individual buy class ≠ team buy class, with a negative game-level WP cost (docs/specs/03#economy, A-21);
   - `utility_waste`: utility with ~0 delay and no enemies affected;
   - `late_rotation`: rotation time vs. the area-graph shortest path and the moment of information
     (spotted/footstep/sound events).
2. **Counterfactual:** the minimal feasible alternative gives a ΔWP with a CI (model uncertainty via the
   fractional bootstrap, docs/specs/04 §2(b)). Drop the item if the CI contains 0. Validity: A-04
   (MV.10). Rules [play_like_champions]:
   - **actionable:** change only decision variables known *before* the decision (buy, take/avoid the
     duel, utility timing, position/rotation), never outcome proxies (kills, damage, round result);
   - **realistic:** the counterfactual state must be supported by observed CSDS states (near-twin
     matches or a density check). No unconstrained optimisation over the model;
   - **minimum viable change:** report the smallest change that flips or materially improves the
     outcome estimate, next to the full-path gain.
3. **Rank:** `priority = E[ΔWP] × recurrence within the match × confidence`. Keep ≤ 3 focus themes per
   match (A-30); a recurring theme counts for more than a single moment.
4. **Render:** template-first. An LLM rewrite is allowed only from a structured payload, followed by the
   grounding check (docs/specs/04 §7, A-31).
5. **Gate:** check the assumption gate for `coaching_feedback` (docs/ASSUMPTIONS.md).

## Example (target output — numbers illustrative)

> **Round 7 — buy desync.** You bought for $2,000 while your team saved. Engine estimate: if you had
> saved, round-8 full-buy WP ≈ 48% (80% CI 43–53%) vs 22% (18–26%) actual. Seen in 3 of 12 loss-bonus
> rounds this match.

## Tone & constraints

- Compare to the player's **tier** baseline (estimated from CSDS), never to pros.
- Tag every item with `build_num`, and mark items from older builds as possibly stale.
- No claims below the minimum ESS: say "not enough data in this match".
- Link each item to its round and tick.
- Provide a coach-facing export (per-match file). Coaches want AI for analysis and bookkeeping, not as
  a replacement [gig_economy_esports_coaching].
- Published or visualised output carries "Data provided by PureSkill.gg." (DSA).
