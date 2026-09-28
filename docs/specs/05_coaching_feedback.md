# 05 — Coaching feedback

Research basis [gig_economy_esports_coaching] (read its notes): players value individualised,
*situated* diagnosis over raw dashboards and distrust generic tips; authority must be visible
(benchmarks vs. own tier, linked replay evidence); insights expire with patches; descriptive "you lost 15% WPA" is not prescriptive. Feedback must be
**counterfactual, specific, few, and honest about uncertainty**.

## Feedback item lifecycle

1. **Detect** (`coaching/detectors.py`): candidate mistakes with evidence rows, e.g.
   - `risky_duel`: xK < θ₁ while WP_if_hold > θ₂ (post-plant, man advantage)
   - `untraded_death` / `no_trade_position`: teammate within trade distance but not
     positioned (nav distance > trade window)
   - `desync_buy`: individual buy class ≠ team buy class and negative two-round EV
   - `utility_waste`: utility with ~0 delay / no enemies affected
   - `late_rotation`: rotation time vs nav shortest path & information timing
2. **Counterfactual** (`coaching/counterfactual.py`): minimal feasible alternative →
   ΔWP with cluster-bootstrap/model-ensemble CI.
3. **Rank**: `priority = E[ΔWP] × recurrence_rate × confidence`; keep ≤ 3 focus themes per
   match, aggregated across rounds (themes > single moments).
4. **Render** (`coaching/narrative.py`): template-first. Optional LLM rewrite is allowed
   only with a structured payload and a post-check that every number in the text
   appears in the payload (implemented as `assert_grounded`).

## Example (target output)

> **Round 7 — buy desync.** You bought for $2,000 while your team saved. Engine
> estimate: if you had saved, round-8 full buy WP ≈ 48% (80% CI 43–53%) vs 22%
> (18–26%) actual. Seen in 3 of 12 loss-bonus rounds this match.

## Tone & constraints

- Tag every feedback item with `game_build`; mark items from older builds as possibly stale.
- Offer a coach-facing export (per-player file, longitudinal trends) — coaches want AI for
  analysis and bookkeeping, not as a replacement [gig_economy_esports_coaching].
- Tier-appropriate: compare to the player's tier baseline, not pros.
- No claims when ESS below threshold; say "not enough data yet".
- Link each item to a demo tick for review (`demo_tick`).
