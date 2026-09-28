#!/bin/bash
# Installs the package in Claude Code on the web sessions so tests/lint can run.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
cd "$CLAUDE_PROJECT_DIR"
pip install -q -e ".[dev]" >/dev/null 2>&1 || pip install -e ".[dev]"
