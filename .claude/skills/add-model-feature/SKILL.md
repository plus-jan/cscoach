---
name: add-model-feature
description: Add a new feature to the WP or xK model safely (CSDS source check, leakage check, ablation, validation). Use when proposing or implementing a new model input.
---

1. **Source check:** name the exact CSDS channels/columns it comes from (`docs/data/csds_spec.md`). If
   CSDS cannot support it, the feature is out of scope (ADR-0003). Note the channel-set requirement
   (v42-only channels like `player_inputs`, `bullet_damage`, A-39) and any undocumented codes it
   depends on (A-15).
2. **Prior evidence:** check `docs/research/papers/README.md` and cite `[id]` where relevant.
3. **Define it precisely** in `docs/specs/03_models.md` / `02_data_contracts.md`: its source, and a tick
   window that uses only data with tick ≤ snapshot tick. Account for as-of merge staleness on merged
   columns.
4. **New thresholds** need an assumption entry + a row in `docs/specs/06_parameters.md`.
5. **In the project repo:** a leakage test (the feature is unchanged when future rows are removed), then an
   ablation on identical grouped splits. Keep the feature only if the log-loss improvement CI excludes 0
   and no stratum's ECE regresses beyond its gate. Several candidate features or encodings → run them as
   a Classic `/autoresearch` loop with the gated Verify and Guard of docs/specs/07 §2 (training matches
   only, bounded budget), then one sealed-test evaluation with `validate-model`. Report the number of
   variants tried.
6. Record the experiment in `docs/PROGRESS.md`. Add the feature to the spec's feature list and the
   monotone-constraint table if it has a clear direction (A-27).
