---
name: validate-model
description: Evaluate a trained model (wp or xk) against the validation protocol and gates, producing a reproducible report. Use after any model change or when asked whether a model is accurate enough.
---

1. Confirm the data split is grouped by `match_id` (`assert_no_group_leakage`).
2. Run `cscoach validate --model <wp|xk> --run <model_dir>` (or the Python API in
   `cscoach.validation.report`) on the **test** fold only.
3. Check: overall and per-tier/per-map ECE, Brier, log-loss, Brier skill vs baseline
   with cluster-bootstrap CIs, ESS. Look at reliability curves for systematic bias
   (e.g. overconfidence in 5v4 states for low tiers).
4. If a gate fails, do NOT relax the gate. Diagnose (features, calibration fold size,
   tier label noise) and iterate, or document the failure and open a task.
5. Summarise: table of metrics with CIs, gate verdicts, path to `metrics.json`.
