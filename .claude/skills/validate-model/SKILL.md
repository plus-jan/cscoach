---
name: validate-model
description: Evaluate a trained model (WP or xK) against the validation protocol and gates, producing a reproducible report. Use after any model change or when asked whether a model is accurate enough.
---

1. Confirm the split is grouped by `match_id`, with duplicates removed first (docs/specs/04 §1). The
   training code must assert that no match appears in two splits.
2. Evaluate on the **test** fold only. Compute the metrics of docs/specs/04 §2 overall and per tier,
   platform, map, round phase and alive state. Every metric and every model difference gets a
   cluster-bootstrap CI over matches (method per A-24/MV.4), plus the ESS.
3. Compare the numbers against the gates in `docs/specs/06_parameters.md`. Note which gates are still
   assumptions (A-06/A-07) rather than decided policy.
4. Inspect the reliability curves for systematic bias, e.g. overconfidence in man-advantage states for
   low tiers (A-01).
5. Never relax a gate to pass. Diagnose the failure (features, calibration fold size, tier-label noise,
   drift by `build_num`). Then iterate, or document the failure and open a roadmap task.
6. Write the report (CLAUDE.md "Evidence") and link it from `docs/PROGRESS.md`. Summarise: a metric
   table with CIs, the gate verdicts, and the assumptions affected.
