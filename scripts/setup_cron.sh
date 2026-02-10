#!/bin/bash
#
# Setup Cron Jobs for Blog Automation
# - 08:00: Daily English content generation
# - 18:00: AI exposure check (to be implemented)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "Setting up cron jobs for Soo Edu blog automation..."
echo ""

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Remove existing sooedu blog jobs
crontab -l 2>/dev/null | grep -v "daily_post_and_push.sh" | grep -v "check_ai_exposure" > /tmp/new_crontab.txt || true

# Daily content generation at 08:00  
echo "0 8 * * * $REPO_DIR/scripts/daily_post_and_push.sh >> $REPO_DIR/logs/daily_content.log 2>&1" >> /tmp/new_crontab.txt

# Knowledge graph snapshot at 08:30 (after content generation)
echo "30 8 * * * $REPO_DIR/scripts/update_knowledge_graph.sh >> $REPO_DIR/logs/knowledge_graph.log 2>&1" >> /tmp/new_crontab.txt

# AI exposure check at 18:00 (placeholder - script to be created)
echo "0 18 * * * $REPO_DIR/scripts/check_ai_exposure.sh >> $REPO_DIR/logs/ai_exposure.log 2>&1" >> /tmp/new_crontab.txt

# Install new crontab
crontab /tmp/new_crontab.txt

echo "✅ Cron jobs installed!"
echo ""
echo "Scheduled jobs:"
crontab -l | grep -E "(daily_post_and_push|check_ai_exposure)"
echo ""
echo "Logs will be saved to:"
echo "  - $REPO_DIR/logs/daily_content.log"
echo "  - $REPO_DIR/logs/ai_exposure.log"
