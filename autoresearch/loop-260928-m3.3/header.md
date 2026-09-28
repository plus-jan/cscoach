# M3.3 gated loop — header (written before iteration 1)

- task: M3.3 calibration layer · config `configs/wp_calibration.yaml` (model.calibration only) · task
  `gbdt_wp_calibrated` (M3.2 champion GBDT out-of-fold predictions, then calibration cross-fitted over the 5 training
  folds: fold k is calibrated by a calibrator fitted on the other folds; `cscoach.models.calibration`).
- data, split, keep rule, guard, seeds: as in the M3.2 loop (autoresearch/loop-260928-m3.2/header.md); a new budget
  of 15 variants for this task.
- champion (iteration 0): no calibration (clipped identity).

Planned variants: global isotonic; global Platt; global + per tier (A-28 design, auto method); per platform;
per tier × platform. Kept changes become the champion for the next variant.
