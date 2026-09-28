"""Keep docs/research/sources.yaml, papers/*.md and [id] citations consistent."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs/research"
SOURCES = yaml.safe_load((RESEARCH / "sources.yaml").read_text())
IDS = {s["id"] for s in SOURCES}


def test_ids_unique():
    assert len(IDS) == len(SOURCES)


def test_local_files_exist_and_match():
    for s in SOURCES:
        if s.get("local"):
            path = ROOT / s["local"]
            assert path.exists(), s["id"]
            assert f"id: {s['id']}" in path.read_text()[:500], s["id"]


def test_every_paper_file_is_registered_and_has_notes():
    for f in (RESEARCH / "papers").glob("*.md"):
        if f.name == "README.md":
            continue
        assert f.stem in IDS, f"{f.name} missing from sources.yaml"
        text = f.read_text()
        assert (
            "<!-- cscoach-notes:start -->" in text
            and "TODO" not in text.split("<!-- cscoach-notes:end -->")[0]
        ), f"{f.name}: notes block missing or unfinished"


def test_verified_true_requires_local_full_text():
    for s in SOURCES:
        if s.get("verified") is True:
            assert s.get("local"), f"{s['id']} verified without local full text"


def test_citations_in_docs_resolve():
    cite = re.compile(r"\[([a-z0-9_]+)\]")
    docs = [ROOT / "ROADMAP.md", ROOT / "CLAUDE.md", *(ROOT / "docs").rglob("*.md")]
    for doc in docs:
        if "papers" in doc.parts and doc.name != "README.md":
            continue  # full texts contain their own bracketed references
        for ref in cite.findall(doc.read_text()):
            if "_" in ref:  # our ids always contain an underscore
                assert ref in IDS, f"{doc.relative_to(ROOT)} cites unknown id [{ref}]"
