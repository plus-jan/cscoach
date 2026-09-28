# ADR-0006 — Research-driven planning: invariants fixed, route decided by findings

- Status: accepted
- Date: 2026-09-28
- Roadmap: M0.5

## Context
The original roadmap fixed a full pipeline (WP → WPA → xK → economy → spatial → coaching) taken from
a literature synthesis that turned out to contain several errors. Key premises are unverified: tier
differences (A-01), counterfactual validity of WP (A-04), precision of per-match player metrics
(A-24/A-07). If a premise fails, large parts of that plan become wasted work. The route should instead
follow from what our own data shows.

## Decision
- **Fixed (invariants):** data policy (ADR-0003), accuracy rules and evidence standard (CLAUDE.md),
  release gate and assumption register (docs/ASSUMPTIONS.md), no code in this repo (ADR-0004).
- **Hypothesis (route):** the pipeline in docs/specs/01 is a working hypothesis. Each stage lists the
  assumptions it depends on.
- The roadmap is split into a **committed horizon** (Part A), **decision points** D1–D5 with explicit
  branches (Part B), and a **provisional backlog** (Part C).
- An **exploration phase (E.1–E.5)** right after data access lets the data generate hypotheses and
  size opportunities, alongside the literature.
- Results go into **docs/FINDINGS.md**. The **plan-next-step** skill turns findings into the next
  committed batch, which the user approves.
- A fallback feedback mode that needs no counterfactual validity (**benchmark mode**, docs/specs/05)
  is specified in advance, so D2-c has a defined route.

## Consequences
- Less upfront commitment; the backlog may change substantially after E and D1–D3.
- Every decision leaves a record (a finding + an ADR if the architecture changes).
- The research questions of the project become explicit and testable, including whether the planned
  modules address the main reasons amateurs lose rounds (A-41).
