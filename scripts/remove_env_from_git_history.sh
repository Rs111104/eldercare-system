#!/usr/bin/env bash
# WARNING: rewrites git history. Run with care and inform collaborators.

# Remove .env from all commits using git filter-repo (preferred) or filter-branch fallback.
if command -v git-filter-repo >/dev/null 2>&1; then
  git filter-repo --path .env --invert-paths
else
  echo "git-filter-repo not found; using git filter-branch fallback. This is slower and more error-prone."
  git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all
fi

echo "Removed .env from history. Force-push required: git push --force --all && git push --force --tags"
