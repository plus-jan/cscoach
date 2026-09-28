---
name: add-paper
description: Add a research paper (PDF) to docs/research/papers as agent-readable markdown with a verified notes block, and register it in sources.yaml. Use when the user provides a PDF or a spec/task cites a paper without local full text.
---

1. Register first: add or complete the entry in `docs/research/sources.yaml` (id, title, authors,
   year, venue, url, `arxiv` if any, questions A–J, `use_in_project`).
2. Convert the PDF outside this repo (the scratchpad), e.g. with `pymupdf4llm.to_markdown(pdf)`
   (`pip install pymupdf4llm`). Collapse runs of 3+ blank lines. Don't commit PDFs.
3. Write `docs/research/papers/<id>.md` with:
   - YAML front matter: id, title, authors, year, venue, url, arxiv_version, license, pdf_sha256 (first 16
     hex chars), converted (date), converter;
   - `# <title>`, then a note that PDF conversion may garble tables and equations;
   - the notes block between `<!-- cscoach-notes:start -->` and `<!-- cscoach-notes:end -->`, containing:
     relevance, **verified claims with section/table references**, corrections vs.
     `research_synthesis_de.md` and `sources.yaml`, use in the project (specs/tasks/assumptions),
     caveats (split protocol, calibration reported?, sample size);
   - `## Full text` followed by the converted text.
4. **Read the paper** before writing the notes. Check every number you quote against the table/section.
5. Update `sources.yaml` (`local`, `verified: true`, `verified_claim`, `license`), the index and the
   by-question lists in `docs/research/papers/README.md`, and any spec, assumption or ADR the paper
   supports or contradicts.
6. Licensing: record the license. Keep the repository private unless redistribution is allowed.
