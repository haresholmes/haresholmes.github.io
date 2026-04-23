#!/usr/bin/env bash
# Commit all changes and push to GitHub (uses GitHub CLI for HTTPS auth).
set -euo pipefail
cd "$(dirname "$0")"

if ! gh auth status -h github.com &>/dev/null; then
  echo "GitHub CLI is not logged in yet."
  echo "Run this once (browser will open), then re-run this script:"
  echo "  gh auth login -h github.com -p https -w"
  exit 1
fi

gh auth setup-git

MSG="${1:-Update site}"
git add -A
if git diff --cached --quiet; then
  echo "Nothing new to commit (working tree was already clean)."
else
  git commit -m "$MSG"
fi

git push -u origin main
echo "Done: pushed to origin/main."
