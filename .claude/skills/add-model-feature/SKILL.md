---
name: add-model-feature
description: Add a new feature to the WP or xK model safely (leakage check, ablation, validation). Use when proposing or implementing a new model input.
---

1. Check `docs/research/papers/README.md` for prior evidence on the feature (cite `[id]`).
   Define the feature precisely in `docs/specs/03_models.md` (source columns, tick
   window — must use only data with tick <= snapshot tick).
2. Implement in `src/cscoach/features/`; add unit tests incl. a leakage test (feature
   unchanged when future ticks are removed from the input).
3. Add to `configs/model_*.yaml`; set monotone constraint if there is a clear direction.
4. Ablation: train with/without on identical grouped splits; keep the feature only if
   log-loss improves with cluster-bootstrap CI excluding 0 and no tier ECE regresses.
5. Record the experiment dir and decision in `docs/PROGRESS.md`.
