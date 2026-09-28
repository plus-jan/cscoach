# cscoach — CS2 coaching engine (knowledge base)

A knowledge base for AI agents building a **data-driven, statistically validated coaching engine** for
amateur and semi-pro Counter-Strike 2 players. It covers calibrated round **Win Probability**, **WPA**
credit, **Expected Kills (xK)**, and economy and spatial analytics, turned into counterfactual,
actionable feedback.

This repository contains **concepts only, no code** (ADR-0004). The only data source is the
**PureSkill.gg CSDS corpus**, used through the official `pureskillgg-dsdk` libraries (ADR-0003).

| Start here | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Operating manual for agents: rules, workflow, evidence standard |
| [`ROADMAP.md`](ROADMAP.md) | Tasks with IDs and Definition of Done, incl. milestone **MV** (empirical verification) |
| [`docs/specs/`](docs/specs) | Architecture, derived data, models, validation (+ reference algorithms), coaching, parameters |
| [`docs/data/`](docs/data) | CSDS corpus guide, vendored channel spec + data dictionary |
| [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md) · [`docs/assumptions.yaml`](docs/assumptions.yaml) | Everything not yet verified, and what it blocks |
| [`docs/research/`](docs/research) | Source registry, full-text papers with verified notes, original German synthesis |
| [`docs/adr/`](docs/adr) | Decisions |
| [`.claude/skills/`](.claude/skills) | Agent workflows (next-task, validate-model, add-model-feature, resolve-assumption, add-paper, check-knowledge-base) |

**Data attribution:** analyses built on this project use data provided by PureSkill.gg (CC BY-NC-SA 4.0
Data Subscriber Agreement: non-commercial use, attribution "Data provided by PureSkill.gg.",
share-alike).
