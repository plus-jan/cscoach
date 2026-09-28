#!/usr/bin/env bash
# Local gate (ADR-0009): the knowledge-base check, the cscoach tests and the four upstream test suites.
# Run before every commit and merge; there is no remote CI. Exit 0 only if all pass.
set -uo pipefail
cd "$(dirname "$0")/.."

fail=0
run() {
  local name="$1"; shift
  local out
  if out=$("$@" 2>&1); then
    echo "PASS  $name :: $(tail -1 <<<"$out")"
  else
    echo "FAIL  $name"; echo "$out" | tail -20; fail=1
  fi
}

run kbcheck      python3 scripts/kbcheck.py
run cscoach      uv run --quiet pytest -q tests/cscoach
for t in hooks maintenance orchestrator regression; do
  run "$t" bash "tests/test-$t.sh"
done
exit "$fail"
