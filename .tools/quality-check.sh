#!/usr/bin/env bash
set -euo pipefail

# Get repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Validate repository root exists
if [[ ! -d "$REPO_ROOT" ]]; then
    echo "Error: Repository root directory not found: $REPO_ROOT"
    exit 1
fi

# Define directories to exclude (centralized)
EXCLUDE_DIRS=(".git" ".tools" "memory-bank" ".roo")
EXIT_CODE=0

# Helper function to build grep exclude parameters
build_grep_excludes() {
    local excludes=""
    for dir in "${EXCLUDE_DIRS[@]}"; do
        excludes+="--exclude-dir=$dir "
    done
    echo "$excludes"
}

# Helper function to build find path exclusions
build_find_excludes() {
    local excludes=""
    for dir in "${EXCLUDE_DIRS[@]}"; do
        excludes+="-not -path \"*/$dir/*\" "
    done
    echo "$excludes"
}

echo "Running quality checks on: $REPO_ROOT"
echo "========================================"

# Search for TODOs excluding specific directories
echo "Checking for TODOs..."
GREP_EXCLUDES=$(build_grep_excludes)
TODO_FILES=$(eval "grep -R 'TODO' '$REPO_ROOT' --line-number $GREP_EXCLUDES" 2>/dev/null || true)

if [[ -n "$TODO_FILES" ]]; then
    echo "❌ TODOs found:"
    echo "$TODO_FILES"
    EXIT_CODE=1
else
    echo "✅ No TODOs found"
fi

echo ""

# Search for potential secrets (case-insensitive and more comprehensive)
echo "Checking for potential secrets..."
SECRET_PATTERNS='(aws_secret_access_key|api_key|secret_key|password|private[_-]key|auth[_-]token|bearer[_-]token)'
SECRET_FILES=$(eval "grep -R -E -i '$SECRET_PATTERNS' '$REPO_ROOT' --line-number $GREP_EXCLUDES" 2>/dev/null || true)

if [[ -n "$SECRET_FILES" ]]; then
    echo "❌ Potential secrets found:"
    echo "$SECRET_FILES"
    EXIT_CODE=1
else
    echo "✅ No potential secrets found"
fi

echo ""

# Check for files larger than 1MB
echo "Checking for large files (>1MB)..."
FIND_EXCLUDES=$(build_find_excludes)
LARGE_FILES=$(eval "find '$REPO_ROOT' -type f $FIND_EXCLUDES -size +1M" 2>/dev/null || true)

if [[ -n "$LARGE_FILES" ]]; then
    echo "❌ Files exceeding 1MB found:"
    while IFS= read -r file; do
        size=$(du -h "$file" | cut -f1)
        echo "  $file ($size)"
    done <<< "$LARGE_FILES"
    EXIT_CODE=1
else
    echo "✅ No large files found"
fi

echo ""
echo "========================================"

# Final result
if [[ "$EXIT_CODE" -ne 0 ]]; then
    echo "❌ Quality checks failed."
else
    echo "✅ All quality checks passed."
fi

exit $EXIT_CODE
