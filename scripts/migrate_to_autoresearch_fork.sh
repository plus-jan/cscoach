#!/usr/bin/env bash
# Migrate the cscoach knowledge base into a fork of uditgoenka/autoresearch (ADR-0007, ROADMAP M0.6).
#
# Usage: scripts/migrate_to_autoresearch_fork.sh <fork-clone-dir> [kb-url] [kb-branch] [work-branch]
#   <fork-clone-dir>  a clone of the fork (e.g. plus-jan/cscoach), on its default branch
#   kb-url            default: https://github.com/plus-jan/cscoach-template
#   kb-branch         default: claude/epic-thompson-s45ea2
#   work-branch       default: claude/cscoach-migration
#
# What it does (one commit per step, nothing is pushed):
#   1. moves the upstream README to guide/AUTORESEARCH.md
#   2. merges the knowledge base with its history (--allow-unrelated-histories)
#   3. .gitignore union (+ keep the cscoach skills tracked), README notice, README.md merge=ours
#   4. enables the upstream safety hooks in .claude/settings.json (project-relative paths)
#   5. runs scripts/kbcheck.py and the upstream test suites
set -euo pipefail

FORK="${1:?usage: $0 <fork-clone-dir> [kb-url] [kb-branch] [work-branch]}"
KB_URL="${2:-https://github.com/plus-jan/cscoach-template}"
KB_BRANCH="${3:-claude/epic-thompson-s45ea2}"
WORK="${4:-claude/cscoach-migration}"
SKILLS=(next-task plan-next-step validate-model add-model-feature resolve-assumption add-paper check-knowledge-base)

cd "$FORK"
[[ -z "$(git status --porcelain)" ]] || { echo "fork clone is not clean" >&2; exit 1; }
[[ -f claude-plugin/skills/autoresearch/SKILL.md ]] || { echo "not an autoresearch clone" >&2; exit 1; }

git remote get-url upstream >/dev/null 2>&1 || git remote add upstream https://github.com/uditgoenka/autoresearch
git remote get-url kb >/dev/null 2>&1 || git remote add kb "$KB_URL"
git fetch kb "$KB_BRANCH"
git checkout -b "$WORK"

# 1. upstream README -> guide/AUTORESEARCH.md (README.md becomes the cscoach README)
git mv README.md guide/AUTORESEARCH.md
git commit -q -m "Move upstream README to guide/AUTORESEARCH.md (ADR-0007)"

# 2. merge the knowledge base with history
if ! git merge --allow-unrelated-histories --no-edit -m "Merge cscoach knowledge base (ADR-0007)" "kb/$KB_BRANCH"; then
  conflicts="$(git diff --name-only --diff-filter=U)"
  for f in $conflicts; do
    [[ "$f" == ".gitignore" ]] || { echo "unexpected conflict: $f" >&2; exit 1; }
  done
  # .gitignore: union of both sides, order kept, duplicates dropped
  { git show :2:.gitignore; echo; echo "# --- cscoach ---"; git show :3:.gitignore; } | awk '!NF || !seen[$0]++' > .gitignore
  git add .gitignore
  git commit -q --no-edit
fi

# 3. keep cscoach skills tracked (upstream ignores .claude/skills/* except autoresearch); README is ours
{
  echo
  echo "# cscoach skills (ADR-0007)"
  for s in "${SKILLS[@]}"; do echo "!.claude/skills/$s/"; done
} >> .gitignore
grep -q '^README.md merge=ours' .gitattributes 2>/dev/null || echo 'README.md merge=ours' >> .gitattributes
git config merge.ours.driver true
# Attribution (MIT) + upstream version badge. The upstream parity test checks README.md for the badge,
# so refresh this line after every upstream merge that bumps the version.
badge="$(grep -m1 'img.shields.io/badge/version-' guide/AUTORESEARCH.md)"
cat >> README.md <<NOTICE

## Built on autoresearch (NOTICE)

The loop tooling (\`claude-plugin/\`, \`.claude/skills/autoresearch\`, \`.claude/commands/autoresearch*\`,
\`.claude/hooks/autoresearch\`, \`guide/\`, \`plugins/\`, \`.agents/\`, \`.opencode/\`, the upstream scripts
and tests, and the \`docs/*.md\` files at the top of \`docs/\`) comes from
[uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch), © Udit Goenka, MIT License (see
\`LICENSE\`). Its original README is [\`guide/AUTORESEARCH.md\`](guide/AUTORESEARCH.md). In this project,
loops run only under [\`docs/specs/07_autoresearch_protocol.md\`](docs/specs/07_autoresearch_protocol.md).

$badge
NOTICE
git add .gitignore .gitattributes README.md
git commit -q -m "Track cscoach skills; README notice for autoresearch; keep our README on upstream merges"

# 4. enable upstream safety hooks for project sessions (paths relative to the project dir)
[[ ! -f .claude/settings.json ]] || { echo ".claude/settings.json exists; merge hooks by hand" >&2; exit 1; }
node - <<'NODE'
const fs = require('fs');
const root = '"$CLAUDE_PROJECT_DIR"/.claude/hooks/autoresearch';
const cmd = (name) => `bash ${root}/node-hook-runner.sh ${root}/${name}`;
const settings = { hooks: {
  PreToolUse: [{ matcher: 'Write|Bash|Glob|Grep|Read|Edit', hooks: [
    { type: 'command', command: cmd('scout-block.cjs'), timeout: 10 },
    { type: 'command', command: cmd('privacy-block.cjs'), timeout: 10 },
    { type: 'command', command: cmd('dangerous-cmd-block.cjs'), timeout: 10 } ] }],
  UserPromptSubmit: [{ hooks: [{ type: 'command', command: cmd('iteration-context.cjs'), timeout: 10 }] }],
} };
fs.writeFileSync('.claude/settings.json', JSON.stringify(settings, null, 2) + '\n');
NODE
git add .claude/settings.json
git commit -q -m "Enable autoresearch safety hooks for project sessions (docs/specs/07 §8)"

# 5. checks
python3 scripts/kbcheck.py
for t in tests/test-hooks.sh tests/test-orchestrator.sh tests/test-regression.sh tests/test-maintenance.sh; do
  bash "$t" >/dev/null 2>&1 || { echo "upstream test failed: $t" >&2; exit 1; }
done
echo "upstream tests: OK"
git log --oneline -1
echo "Done. Review, then: git push -u origin $WORK and open a PR on the fork."
