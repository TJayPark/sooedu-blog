#!/bin/bash
#
# Knowledge Graph Snapshot Generator and Git Push
# Generates daily snapshot of Neo4j knowledge graph
# Run via cron daily at 08:30 (after daily content generation)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "Soo Edu - Knowledge Graph Snapshot Generator"
echo "================================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"

cd "$REPO_DIR"

# Generate knowledge graph snapshot
echo ""
echo "📊 Generating knowledge graph snapshot..."
python3 "$SCRIPT_DIR/generate_knowledge_graph.py"

GENERATE_EXIT=$?

if [ $GENERATE_EXIT -ne 0 ]; then
    echo "❌ Knowledge graph generation failed (exit code: $GENERATE_EXIT)"
    exit $GENERATE_EXIT
fi

echo ""
echo "✅ Knowledge graph snapshot generated!"

# Check for changes
echo ""
echo "🔍 Checking for changes..."

if ! git diff --quiet assets/data/ || ! git diff --cached --quiet assets/data/; then
    echo "✅ Changes detected in knowledge graph data"
    
    # Configure git user (for this session only)
    git config user.name "Soo Edu Bot"
    git config user.email "sooedu@users.noreply.github.com"
    
    # Stage knowledge graph data
    git add assets/data/
    
    # Create commit
    COMMIT_MSG="🧠 Update knowledge graph snapshot - $(date '+%Y-%m-%d')"
    echo ""
    echo "💾 Committing changes..."
    echo "   Message: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"
    
    # Push to remote
    echo ""
    echo "🚀 Pushing to GitHub..."
    git push origin main
    
    echo ""
    echo "================================================"
    echo "✅ SUCCESS! Knowledge graph updated on GitHub"
    echo "================================================"
else
    echo "ℹ️  No changes to commit (graph unchanged)"
fi

echo ""
echo "Done at $(date '+%Y-%m-%d %H:%M:%S')"
