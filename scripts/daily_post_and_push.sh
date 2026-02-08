#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

: "${OLLAMA_BASE_URL:=http://localhost:11434}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 2
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git not found" >&2
  exit 2
fi

# Generate today's post (skip if already exists)
set +e
python3 "scripts/generate_todays_sentence.py" --ollama-url "$OLLAMA_BASE_URL"
gen_rc=$?
set -e
if [[ $gen_rc -ne 0 && $gen_rc -ne 3 ]]; then
  echo "Post generation failed (exit=$gen_rc)." >&2
  exit "$gen_rc"
fi

git add -A

if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

today="$(date +%Y-%m-%d)"
git -c user.name="${GIT_USER_NAME:-Soo Edu Bot}" \
  -c user.email="${GIT_USER_EMAIL:-sooedu@users.noreply.github.com}" \
  commit -m "chore: add today's sentence ($today)"

# Push to origin if configured
if git remote get-url origin >/dev/null 2>&1; then
  git push
else
  echo "Remote 'origin' is not set; skipping push." >&2
fi
