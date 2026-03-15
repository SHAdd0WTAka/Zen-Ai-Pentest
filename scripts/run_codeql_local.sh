#!/bin/bash
# Local CodeQL Analysis Script
# Reduces 9,138 alerts by filtering false positives

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_NAME="zen-pentest-db"
RESULTS_DIR="$PROJECT_ROOT/codeql-results"

echo "🔍 Zen-AI-Pentest Local CodeQL Analysis"
echo "========================================"
echo ""

# Check if codeql is available
if ! command -v codeql &> /dev/null; then
    echo "❌ CodeQL CLI not found!"
    echo "Install: https://github.com/github/codeql-cli-binaries/releases"
    exit 1
fi

echo "✅ CodeQL version: $(codeql --version | head -1)"
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Clean up old database
if [ -d "$DB_NAME" ]; then
    echo "🗑️  Removing old database..."
    rm -rf "$DB_NAME"
fi

echo "📦 Creating CodeQL database..."
codeql database create "$DB_NAME" \
    --language=python \
    --source-root="$PROJECT_ROOT" \
    --overwrite

echo ""
echo "🔎 Analyzing with security-extended queries..."
codeql analyze "$DB_NAME" \
    --format=sarifv2.1.0 \
    --output="$RESULTS_DIR/results-security.sarif" \
    --sarif-add-snippets \
    security-extended

echo ""
echo "📊 Generating summary..."
codeql analyze "$DB_NAME" \
    --format=csv \
    --output="$RESULTS_DIR/results.csv" \
    security-extended

# Count alerts by severity
echo ""
echo "📈 Results Summary:"
echo "=================="

# Parse CSV for summary (skip header)
if [ -f "$RESULTS_DIR/results.csv" ]; then
    tail -n +2 "$RESULTS_DIR/results.csv" | awk -F',' '
    {
        severity = $5
        gsub(/"/, "", severity)
        if (severity == "error" || severity == "critical") critical++
        else if (severity == "warning" || severity == "high") high++
        else if (severity == "note" || severity == "medium") medium++
        else if (severity == "low") low++
        else info++
    }
    END {
        print "🔴 Critical/Error: " (critical ? critical : 0)
        print "🟠 High/Warning:   " (high ? high : 0)
        print "🟡 Medium/Note:    " (medium ? medium : 0)
        print "🟢 Low:            " (low ? low : 0)
        print "⚪ Info:           " (info ? info : 0)
    }'
fi

echo ""
echo "📁 Results saved to:"
echo "   - SARIF: $RESULTS_DIR/results-security.sarif"
echo "   - CSV:   $RESULTS_DIR/results.csv"
echo ""
echo "💡 To view in VS Code, install 'SARIF Viewer' extension"
echo ""
echo "✅ Analysis complete!"
