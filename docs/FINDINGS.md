# Findings log

Results **from our own data** (CSDS) that change what we believe or what we do next. It is the
backbone of research-driven planning (ADR-0006): every decision point (ROADMAP Part B) and every
exploration or verification task writes an entry here, and `plan-next-step` reads it.

Literature evidence stays in `docs/research/` and is not a finding; synthetic-data results never are
(A-33).

## Rules

- One entry per result, numbered `F-NN` and never reused. Newest at the bottom.
- An entry states the **result** (numbers with CIs), the **evidence** (report path in the code repo,
  CSDS revisions, config hash), what it **changes** (assumption statuses, parameters, specs, ADRs) and
  the **next step** chosen, with its rationale.
- Negative and null results are recorded too. "No difference" is a finding.
- A finding can be superseded by a later one, which must say `supersedes: F-NN`.

## Template

```
### F-NN — <short title>
- date: YYYY-MM-DD · task: <E.x | MV.x | M.x> · decision: <D1..D5 or —>
- question: <what we asked; pre-registered criterion if any>
- result: <numbers with CIs; strata>
- evidence: <code-repo report path, CSDS revision ids/dates, config hash>
- confidence: high | medium | low (why)
- changes: <A-NN status → …; parameters; specs; ADR-XXXX>
- next step: <chosen branch/tasks> — rationale: <why this beats the alternatives>
- supersedes: <F-NN or —>
```

## Log

_No findings yet: CSDS access (M1.1) is pending. The first expected entries come from M1.3/M1.4 (corpus
composition), MV.1 (rules and decoding) and E.1–E.4 (exploration)._
