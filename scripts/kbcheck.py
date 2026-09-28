#!/usr/bin/env python3
"""Consistency check for the cscoach knowledge base (skill `check-knowledge-base`, ADR-0007).

Checks only cscoach paths, so upstream autoresearch files in the fork are ignored.
Exit code 0 = consistent, 1 = problems (listed on stdout). Needs PyYAML.
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASK = r"(M\d+\.\d+|MV\.\d+|E\.\d+)"
TYPES = {"research", "data", "game_rule", "method", "policy", "causal", "constraint", "synthetic"}
STATUSES = {"open", "supported", "refuted", "decided"}
CAPABILITIES = {"wp_timeline", "wpa", "xk", "economy_feedback", "spatial_feedback", "player_metrics",
                "coaching_feedback"}
CSCOACH_SKILLS = {"next-task", "plan-next-step", "validate-model", "add-model-feature",
                  "resolve-assumption", "add-paper", "check-knowledge-base"}


def kb_markdown() -> list[pathlib.Path]:
    """Markdown files that belong to the cscoach knowledge base (not upstream autoresearch docs)."""
    files = [ROOT / "CLAUDE.md", ROOT / "README.md", ROOT / "ROADMAP.md"]
    files += [ROOT / "docs" / n for n in ("ASSUMPTIONS.md", "FINDINGS.md", "PROGRESS.md")]
    for sub in ("specs", "adr", "data", "research"):
        files += sorted((ROOT / "docs" / sub).rglob("*.md"))
    files += [ROOT / ".claude" / "skills" / s / "SKILL.md" for s in sorted(CSCOACH_SKILLS)]
    return [f for f in files if f.exists()]


def main() -> int:
    probs: list[str] = []
    try:
        assumptions = yaml.safe_load((ROOT / "docs/assumptions.yaml").read_text())
        sources = yaml.safe_load((ROOT / "docs/research/sources.yaml").read_text())
    except yaml.YAMLError as exc:
        print(f"YAML error: {exc}")
        return 1

    road = (ROOT / "ROADMAP.md").read_text()
    tasks = re.findall(r"\*\*" + TASK + r" —", road)
    task_ids = set(tasks)
    if len(tasks) != len(task_ids):
        probs.append("duplicate roadmap task ids")
    aids = {a["id"] for a in assumptions}
    sids = {s["id"] for s in sources}
    if len(aids) != len(assumptions):
        probs.append("duplicate assumption ids")
    params = (ROOT / "docs/specs/06_parameters.md").read_text().lower()

    # 1-2. assumptions register and parameters
    for a in assumptions:
        aid = a["id"]
        if a.get("type") not in TYPES:
            probs.append(f"{aid}: invalid type {a.get('type')!r}")
        if a.get("status") not in STATUSES:
            probs.append(f"{aid}: invalid status {a.get('status')!r}")
        if a.get("status") != "open" and not a.get("evidence"):
            probs.append(f"{aid}: non-open status without evidence")
        probs += [f"{aid}: test {t} not in ROADMAP" for t in (a.get("test") or []) if t not in task_ids]
        probs += [f"{aid}: unknown capability {b}" for b in (a.get("blocks") or []) if b not in CAPABILITIES]
        probs += [f"{aid}: parameter {p!r} not in docs/specs/06" for p in (a.get("parameters") or [])
                  if str(p).lower() not in params]
    for ref in set(re.findall(r"\|\s*(A-\d\d)\s*\|", params.upper())):
        if ref not in aids:
            probs.append(f"docs/specs/06: unknown {ref}")

    # 3. citations and references in knowledge-base markdown
    for doc in kb_markdown():
        if doc.name == "csds_spec.md":
            continue
        rel = doc.relative_to(ROOT)
        txt = doc.read_text().split("## Full text")[0].split("## Source notes")[0]
        for grp in re.findall(r"\[([a-z0-9_, ]+)\]", txt):
            for ref in (x.strip() for x in grp.split(",")):
                if "_" in ref and ref not in sids and ref != "paper_id":
                    probs.append(f"{rel}: unknown source [{ref}]")
        probs += [f"{rel}: unknown {r}" for r in re.findall(r"\bA-\d\d\b", txt) if r not in aids]
        probs += [f"{rel}: unknown task {r}" for r in re.findall(r"\b" + TASK + r"\b", txt)
                  if r not in task_ids]

    for s in sources:
        if s.get("local") and not (ROOT / s["local"]).exists():
            probs.append(f"source {s['id']}: missing local file")
        if s.get("verified") in (True, "notes") and not s.get("local"):
            probs.append(f"source {s['id']}: verified without local file")
    for f in (ROOT / "docs/research/papers").glob("*.md"):
        if f.name == "README.md":
            continue
        if f.stem not in sids:
            probs.append(f"unregistered paper {f.name}")
        if "TODO" in f.read_text().split("<!-- cscoach-notes:end -->")[0]:
            probs.append(f"unfinished notes in {f.name}")

    # 4. roadmap parts, decisions, findings
    part_c = road.split("# Part C")[1] if "# Part C" in road else ""
    if re.search(r"- \[x\]", part_c):
        probs.append("ticked task in ROADMAP Part C")
    probs += [f"unknown decision D{d}" for d in re.findall(r"\bD(\d)(?:-[a-d])?\b", road) if d not in "12345"]
    findings = re.findall(r"^### (F-\d+)", (ROOT / "docs/FINDINGS.md").read_text(), re.M)
    if len(findings) != len(set(findings)):
        probs.append("duplicate finding ids")

    # 5. data rule: no data artefacts committed
    data = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*")
            if p.suffix in {".pdf", ".parquet", ".dem"} and ".git" not in p.parts]
    if data:
        probs.append(f"data artefacts committed: {data}")

    verified = {v: sum(1 for s in sources if s.get("verified") == v) for v in (True, "notes", "search", None)}
    if probs:
        print("\n".join(sorted(set(probs))))
        return 1
    print(f"OK: {len(task_ids)} tasks, {len(aids)} assumptions, {len(sids)} sources {verified}, "
          f"{len(findings)} findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
