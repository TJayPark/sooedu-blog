#!/bin/bash
#
# Daily English Content Generator & Git Push Script
# Generates SEO-optimized English learning content and pushes to GitHub
# Run this via cron for daily automation
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
POSTS_DIR="$REPO_DIR/_posts"
GENERATOR_SCRIPT="$SCRIPT_DIR/generate_daily_english.py"

# Git configuration (use env vars if set, otherwise use defaults)
GIT_USER_NAME="${GIT_USER_NAME:-Soo Edu Bot}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-sooedu@users.noreply.github.com}"

# AI Service Configuration
# Set USE_CLAUDE=1 to use Anthropic Claude API
# Otherwise, will use local Ollama
USE_CLAUDE="${USE_CLAUDE:-0}"

echo "================================================"
echo "Soo Edu - Daily English Content Generator"
echo "================================================"
echo "Repository: $REPO_DIR"
echo "Posts directory: $POSTS_DIR"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "AI Service: $([ "$USE_CLAUDE" = "1" ] && echo "Anthropic Claude" || echo "Local Ollama")"
echo "================================================"

# Navigate to repository
cd "$REPO_DIR"

# Configure git user (for this session only)
git config user.name "$GIT_USER_NAME"
git config user.email "$GIT_USER_EMAIL"

# Generate daily English content
echo ""
echo "📝 Generating daily English learning content..."

if [ "$USE_CLAUDE" = "1" ]; then
    # Use Anthropic Claude API
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "❌ Error: ANTHROPIC_API_KEY environment variable not set"
        echo "Please set your Anthropic API key:"
        echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
        exit 1
    fi
    
    python3 "$GENERATOR_SCRIPT" \
        --use-claude \
        --output-dir "$POSTS_DIR"
else
    # Use local Ollama
    OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
    
    # Check if Ollama is running
    if ! curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        echo "❌ Error: Cannot connect to Ollama at $OLLAMA_URL"
        echo "Please start Ollama: ollama serve"
        exit 1
    fi
    
    python3 "$GENERATOR_SCRIPT" \
        --ollama-url "$OLLAMA_URL" \
        --output-dir "$POSTS_DIR"
fi

GENERATE_EXIT=$?

if [ $GENERATE_EXIT -ne 0 ]; then
    echo "❌ Content generation failed (exit code: $GENERATE_EXIT)"
    exit $GENERATE_EXIT
fi

echo "✅ Content generated successfully!"

# Check for changes
echo ""
echo "🔍 Checking for changes..."

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "✅ Changes detected"
    
    # Stage all changes in _posts directory
    git add "$POSTS_DIR"
    
    # Create commit
    COMMIT_MSG="📚 Add daily English content - $(date '+%Y-%m-%d')"
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
    echo "✅ SUCCESS! Daily content published to GitHub"
    echo "================================================"
else
    echo "ℹ️  No changes to commit (post may already exist for today)"
fi

echo ""
echo "Done at $(date '+%Y-%m-%d %H:%M:%S')"
