# ADR-0008 — CSDS license: non-commercial use, public derived work under CC BY-NC-SA 4.0

- Status: accepted
- Date: 2026-09-28
- Roadmap task: M1.1 (decides A-38)

## Context
Access works: the ADX subscription is approved and the CSDS revisions from 2025-09-01 to 2026-09-28 are
exported to local storage (32,379 match headers; about 4,510 matches with all channels). A header tome
`header.2025-09-01,2026-09-28.full` exists. The export script and manifest follow in M1.2.

The binding license is PureSkill.gg's **Data Subscriber Agreement (DSA)** on AWS Data Exchange, a version of
CC BY-NC-SA 4.0. The project owner read the DSA in their AWS account and confirmed that it matches the public
summary on the product page (https://aws.amazon.com/marketplace/pp/prodview-v3o7zrt6okwmo, read 2026-09-28):
- "you may not use the data for commercial purposes, you must attribute PureSkill.gg, and you must use the
  same license for any derived work";
- published visualisations, videos, summaries or transformed versions carry the exact text
  **"Data provided by PureSkill.gg."**, and the provider is notified when derived content is published;
- "Any attempts to identify people, players' Steam IDs, or online identities are not permitted";
  downloading source demo files is prohibited;
- the data is free; AWS transfer costs are the subscriber's.

The project owner's intended use: **non-commercial only**, and derived work **will be published**. The
project repository `plus-jan/cscoach` is public.

## Decision
1. cscoach is a **non-commercial** project. Neither CSDS data nor anything derived from it (tables, tomes,
   features, trained models and weights, calibration maps, reports, coaching text) is used in a commercial
   product or service. This includes pook.sh if it becomes commercial: it may not use cscoach models trained
   on CSDS.
2. **Raw CSDS data is never committed or redistributed.** It stays outside the repository (currently
   `/media/jan/merged/cs2coach`); the repository ignores data files.
3. **Derived data and models that we publish** (reports, figures, derived tables, model weights) are
   licensed **CC BY-NC-SA 4.0** and carry "Data provided by PureSkill.gg.". The code stays under the
   repository's MIT license; the licenses of code and derived data are stated separately wherever both
   appear.
4. **Notify PureSkill.gg** (contact@pureskill.gg) before the first public release of derived content
   (a published report, model or app), and record the notification in `docs/PROGRESS.md`.
5. **No re-identification:** no linking of per-match aliases to Steam IDs, names or accounts, no attempt to
   obtain source demos (confirms ADR-0005).

## Consequences
- A-38 → `decided`. It no longer blocks any capability.
- Every player-facing output and every published artefact shows the attribution line
  (docs/specs/05 already requires it for coaching output).
- Follow-ups: M1.2 adds a `reports/` license note (CC BY-NC-SA 4.0 + attribution) once the first report
  exists. A commercial plan later would need a new ADR and a different data basis, because the DSA
  forbids it.
