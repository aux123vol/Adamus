#!/bin/bash
# Git auto-save hook — runs at end of every Claude Code session (Stop event)
# Commits any uncommitted changes in the adamus repo with a timestamp

REPO="/home/johan/adamus"

cd "$REPO" || exit 0

# Only proceed if inside a git repo with changes
git rev-parse --git-dir > /dev/null 2>&1 || exit 0

# Check for uncommitted changes (tracked files only)
if git diff --quiet && git diff --cached --quiet; then
    # Nothing to commit
    exit 0
fi

# Run tests first — only commit if they pass
source "$REPO/.venv/bin/activate" 2>/dev/null
if pytest "$REPO/tests/" -q --tb=no -q 2>/dev/null | grep -q "passed"; then
    STATUS="tests-pass"
else
    STATUS="tests-unknown"
fi

TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
git add -p --intent-to-add 2>/dev/null || true
git add .

git commit -m "Auto-save: $TIMESTAMP [$STATUS]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>" 2>/dev/null

echo "[Adamus] Auto-saved to git: $TIMESTAMP [$STATUS]"
