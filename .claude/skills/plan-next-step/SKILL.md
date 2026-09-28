---
name: plan-next-step
description: Decide the next step from the latest proven results — take a decision point (D1–D5), re-plan the provisional backlog, and propose the next committed batch of tasks. Use after an exploration or verification task finishes, when a decision point's inputs are complete, when the Part A horizon is nearly exhausted, or when asked "what should we do next / what did we learn".
---

This repo plans by evidence (ADR-0006). Never extend the committed horizon without doing this.

1. **Gather the state:**
   - `docs/FINDINGS.md` (all entries since the last decision);
   - `ROADMAP.md` Part A status, and the Part B decision points whose inputs are now complete;
   - `docs/assumptions.yaml`: which statuses changed, and what is still open and blocking.
2. **Take due decisions.** For each decision point whose inputs are done:
   - restate its question and branches;
   - map the findings to a branch, using the pre-registered criteria where they exist;
   - if no foreseen branch fits, define a new one and justify it;
   - be explicit about uncertainty. A decision on weak evidence says so and names what would reverse it.
3. **Re-plan the backlog (Part C):**
   - For each item, ask: does it still serve the goal given the findings? Is it now blocked by a
     refuted assumption? Did exploration reveal a more valuable item that isn't listed?
   - Drop items (`[-]` + finding reference), rewrite them, or add new ones. New items need a DoD and
     references to assumptions.
   - Rank candidates with the D3 rule: opportunity × measurability in CSDS × P(blocking assumptions
     hold) ÷ effort.
4. **Propose the next committed batch:** the smallest set of tasks that reaches the next decision
   point or the next shippable piece. At most two new modules at a time. Name what it will decide.
5. **Write it down in one change set:**
   - a finding (F-NN) per decision, with rationale and alternatives considered;
   - an ADR if the architecture changes;
   - specs and the assumption register updated;
   - a PROGRESS line;
   - ROADMAP: move the proposed tasks to Part A **only after the user approves**. Until then, list
     them under "Proposed next batch" at the top of Part B.
6. **Report to the user:** what was learned, which branch was chosen and why, what was dropped, and
   the proposed batch with the decision it will enable. Ask for approval.
7. Run `check-knowledge-base` before committing.
