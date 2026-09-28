#!/usr/bin/env bash
# Merge upstream autoresearch into the current branch of the cscoach fork (ADR-0007).
# Run on a work branch, never on the default branch. Nothing is pushed.
#
#   1. git merge upstream/master (README.md is ours via .gitattributes merge=ours)
#   2. .gitignore conflicts → union of both sides
#   3. refresh guide/AUTORESEARCH.md from the upstream README and the version badge in our README
#   4. run scripts/kbcheck.py and the upstream test suites
set -euo pipefail

REF="${1:-upstream/master}"
[[ -z "$(git status --porcelain)" ]] || { echo "working tree is not clean" >&2; exit 1; }
git config merge.ours.driver true
git fetch upstream

if ! git merge --no-edit "$REF"; then
  for f in $(git diff --name-only --diff-filter=U); do
    [[ "$f" == ".gitignore" ]] || { echo "conflict in $f: resolve by hand, then rerun steps 3-4" >&2; exit 1; }
  done
  { git show :2:.gitignore; git show :3:.gitignore; } | awk '!NF || !seen[$0]++' > .gitignore
  git add .gitignore
  git commit -q --no-edit
fi

git show "$REF:README.md" > guide/AUTORESEARCH.md
badge="$(grep -m1 'img.shields.io/badge/version-' guide/AUTORESEARCH.md)"
old="$(grep -m1 'img.shields.io/badge/version-' README.md || true)"
if [[ -n "$old" && "$old" != "$badge" ]]; then
  python3 - "$old" "$badge" <<'PY'
import sys, pathlib
p = pathlib.Path("README.md")
p.write_text(p.read_text().replace(sys.argv[1], sys.argv[2], 1))
PY
fi
git add guide/AUTORESEARCH.md README.md
git diff --cached --quiet || git commit -q -m "Sync upstream autoresearch README and version badge"

python3 scripts/kbcheck.py
for t in tests/test-hooks.sh tests/test-orchestrator.sh tests/test-regression.sh tests/test-maintenance.sh; do
  bash "$t" >/dev/null 2>&1 || { echo "upstream test failed: $t" >&2; exit 1; }
done
echo "upstream tests: OK"
