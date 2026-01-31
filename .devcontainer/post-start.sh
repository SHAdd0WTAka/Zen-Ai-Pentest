#!/bin/bash

echo "🔄 Zen AI Pentest - Container starting..."

# Check for updates
echo "📦 Checking for dependency updates..."
pip list --outdated 2>/dev/null | head -20

# Ensure directories exist
mkdir -p logs evidence data/sql_injection data/payloads

# Display welcome message
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Zen AI Pentest Development Environment           ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Available Commands:                                       ║"
echo "║    • python -m zen_ai_pentest --help                      ║"
echo "║    • python examples/cve_and_ransomware_demo.py           ║"
echo "║    • python examples/post_scan_demo.py                    ║"
echo "║    • pytest tests/ -v                                     ║"
echo "║    • black .                                              ║"
echo "║    • flake8 .                                             ║"
echo "║                                                            ║"
echo "║  Documentation: /workspaces/zen-ai-pentest/docs/          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
