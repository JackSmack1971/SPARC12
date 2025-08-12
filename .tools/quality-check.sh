#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXCLUDE_DIRS=".git|.tools|memory-bank|.roo"
EXIT_CODE=0

# Search for TODOs excluding specific directories
TODO_FILES=$(grep -R "TODO" "$REPO_ROOT" --line-number --exclude-dir={.git,.tools,memory-bank,.roo} || true)
if [[ -n "$TODO_FILES" ]]; then
  echo "TODOs found:"
  echo "$TODO_FILES"
  EXIT_CODE=1
fi

# Search for potential secrets
SECRET_PATTERNS='(AWS_SECRET_ACCESS_KEY|API_KEY|SECRET_KEY|PASSWORD|PRIVATE KEY)'
SECRET_FILES=$(grep -R -E "$SECRET_PATTERNS" "$REPO_ROOT" --line-number --exclude-dir={.git,.tools,memory-bank,.roo} || true)
if [[ -n "$SECRET_FILES" ]]; then
  echo "Potential secrets found:"
  echo "$SECRET_FILES"
  EXIT_CODE=1
fi

# Check for files larger than 1MB
LARGE_FILES=$(find "$REPO_ROOT" -type f -not -path "*/.git/*" -not -path "*/memory-bank/*" -not -path "*/.roo/*" -size +1M || true)
if [[ -n "$LARGE_FILES" ]]; then
  echo "Files exceeding 1MB:"
  echo "$LARGE_FILES"
  EXIT_CODE=1
fi

if [[ "$EXIT_CODE" -ne 0 ]]; then
  echo "Quality checks failed."
else
  echo "All quality checks passed."
fi
exit $EXIT_CODE
