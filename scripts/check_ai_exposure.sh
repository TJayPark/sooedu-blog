#!/bin/bash
#
# AI Exposure Check Wrapper Script
# Run this via cron at 18:00 daily
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "Soo Edu - AI Search Exposure Check"
echo "================================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"

cd "$REPO_DIR"

# Run the Python checker
python3 "$SCRIPT_DIR/check_ai_exposure.py"

CHECK_EXIT=$?

if [ $CHECK_EXIT -ne 0 ]; then
    echo "❌ Exposure check failed (exit code: $CHECK_EXIT)"
    exit $CHECK_EXIT
fi

echo ""
echo "Done at $(date '+%Y-%m-%d %H:%M:%S')"
