#!/usr/bin/env python
"""Convert research-paper PDFs to agent-readable markdown in docs/research/papers/.

Usage:
    python scripts/pdf_to_md.py path/to/2510.17199v1.pdf [more.pdf ...]
    python scripts/pdf_to_md.py paper.pdf --id some_source_id   # when no arXiv id in filename

The source id is resolved from docs/research/sources.yaml by arXiv id (found in the
filename) or given with --id. Output: docs/research/papers/<id>.md with YAML front matter,
a hand-written "cscoach notes" block (preserved across re-conversion) and the full text.
Requires: pip install pymupdf4llm
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "docs/research/sources.yaml"
OUT_DIR = ROOT / "docs/research/papers"
NOTES_START = "<!-- cscoach-notes:start -->"
NOTES_END = "<!-- cscoach-notes:end -->"
ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")

NOTES_TEMPLATE = f"""{NOTES_START}
## cscoach notes (hand-written — preserved on re-conversion)

- **Relevance:** TODO
- **Verified claims (with section/page):** TODO
- **Corrections vs. research_synthesis_de.md:** TODO
- **Use in project:** TODO (spec sections / roadmap tasks)
- **Caveats:** TODO
{NOTES_END}"""


def load_sources() -> list[dict]:
    return yaml.safe_load(SOURCES.read_text())


def resolve(pdf: Path, explicit_id: str | None, sources: list[dict]) -> tuple[dict, str | None]:
    m = ARXIV_RE.search(pdf.name)
    arxiv = m.group(1) if m else None
    version = m.group(2) if m else None
    if explicit_id:
        hits = [s for s in sources if s["id"] == explicit_id]
    else:
        hits = [s for s in sources if arxiv and str(s.get("arxiv", "")) == arxiv]
    if not hits:
        sys.exit(f"{pdf.name}: no sources.yaml entry (arxiv={arxiv}); add one or pass --id")
    return hits[0], (f"{arxiv}{version}" if arxiv and version else arxiv)


def clean(md: str) -> str:
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def convert(pdf: Path, source: dict, arxiv_version: str | None) -> Path:
    import pymupdf4llm  # imported lazily so --help works without it

    out = OUT_DIR / f"{source['id']}.md"
    notes = NOTES_TEMPLATE
    if out.exists():
        old = out.read_text()
        if NOTES_START in old and NOTES_END in old:
            notes = old[old.index(NOTES_START) : old.index(NOTES_END) + len(NOTES_END)]
    body = clean(pymupdf4llm.to_markdown(str(pdf), show_progress=False))
    front = {
        "id": source["id"],
        "title": source.get("title"),
        "authors": source.get("authors"),
        "year": source.get("year"),
        "venue": source.get("venue"),
        "url": source.get("url"),
        "arxiv_version": arxiv_version,
        "license": source.get("license", "unknown — check before redistributing"),
        "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()[:16],
        "converted": date.today().isoformat(),
        "converter": "pymupdf4llm",
    }
    header = "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True) + "---\n"
    warn = (
        "> Auto-converted from PDF. Tables, equations and figure text may be garbled — "
        "check the original PDF before quoting numbers.\n"
    )
    out.write_text(
        f"{header}\n# {source.get('title')}\n\n{warn}\n{notes}\n\n## Full text\n\n{body}"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("pdfs", nargs="+", type=Path)
    ap.add_argument("--id", help="sources.yaml id (only with a single PDF)")
    args = ap.parse_args()
    if args.id and len(args.pdfs) > 1:
        sys.exit("--id only works with a single PDF")
    sources = load_sources()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pdf in args.pdfs:
        src, ver = resolve(pdf, args.id, sources)
        print(f"{pdf.name} -> {convert(pdf, src, ver).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
