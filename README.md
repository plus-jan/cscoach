# cscoach — CS2 coaching engine

A knowledge base for AI agents building a **data-driven, statistically validated coaching engine** for
amateur and semi-pro Counter-Strike 2 players. It covers calibrated round **Win Probability**, **WPA**
credit, **Expected Kills (xK)**, and economy and spatial analytics, turned into counterfactual,
actionable feedback.

This repository is a **fork of [autoresearch](https://github.com/uditgoenka/autoresearch)** (ADR-0007):
it holds the loop tooling, the knowledge base and (later) the implementation. Loops run only under
[`docs/specs/07_autoresearch_protocol.md`](docs/specs/07_autoresearch_protocol.md). The only data source is the **PureSkill.gg
CSDS corpus**, used through the official `pureskillgg-dsdk` libraries (ADR-0003).

| Start here | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Operating manual for agents: rules, workflow, evidence standard |
| [`ROADMAP.md`](ROADMAP.md) | Research-driven plan: committed tasks, decision points D1–D5 with branches, provisional backlog |
| [`docs/FINDINGS.md`](docs/FINDINGS.md) | Results from our data and the decisions they drove |
| [`docs/specs/`](docs/specs) | Architecture, derived data, models, validation (+ reference algorithms), coaching, parameters, autoresearch loop protocol |
| [`docs/data/`](docs/data) | CSDS corpus guide, vendored channel spec + data dictionary |
| [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md) · [`docs/assumptions.yaml`](docs/assumptions.yaml) | Everything not yet verified, and what it blocks |
| [`docs/research/`](docs/research) | Source registry, full-text papers with verified notes, original German synthesis |
| [`docs/adr/`](docs/adr) | Decisions |
| [`scripts/kbcheck.py`](scripts/kbcheck.py) | Consistency check (also in CI) |
| [`.claude/skills/`](.claude/skills) | Agent workflows (next-task, plan-next-step, validate-model, add-model-feature, resolve-assumption, add-paper, check-knowledge-base) |

**Data attribution:** analyses built on this project use data provided by PureSkill.gg (CC BY-NC-SA 4.0
Data Subscriber Agreement: non-commercial use, attribution "Data provided by PureSkill.gg.",
share-alike).

## Built on autoresearch (NOTICE)

The loop tooling (`claude-plugin/`, `.claude/skills/autoresearch`, `.claude/commands/autoresearch*`,
`.claude/hooks/autoresearch`, `guide/`, `plugins/`, `.agents/`, `.opencode/`, the upstream scripts
and tests, and the `docs/*.md` files at the top of `docs/`) comes from
[uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch), © Udit Goenka, MIT License (see
`LICENSE`). Its original README is [`guide/AUTORESEARCH.md`](guide/AUTORESEARCH.md). In this project,
loops run only under [`docs/specs/07_autoresearch_protocol.md`](docs/specs/07_autoresearch_protocol.md).

[![Version](https://img.shields.io/badge/version-2.2.2-blue.svg)](https://github.com/uditgoenka/autoresearch/releases)
