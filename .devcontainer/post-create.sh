#!/bin/bash

echo "🚀 Setting up Zen AI Pentest development environment..."

# Create required directories
mkdir -p logs evidence data/sql_injection data/payloads templates/reports

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install main dependencies
echo "📦 Installing project dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install pytest pytest-asyncio pytest-cov black isort flake8 bandit safety mypy pre-commit

# Setup pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
if [ -f .pre-commit-config.yaml ]; then
    pre-commit install
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "⚠️  Please update .env with your API keys and configuration"
    fi
fi

# Setup git configuration
echo "🔧 Configuring git..."
git config --global --add safe.directory /workspaces/zen-ai-pentest 2>/dev/null || true

# Run initial validation
echo "✅ Running initial validation..."
python -m py_compile core/orchestrator.py agents/agent_base.py 2>/dev/null && echo "✓ Core files compile successfully" || echo "⚠️  Some files have compilation issues"

echo ""
echo "✨ Development environment setup complete!"
echo ""
echo "📚 Quick Start:"
echo "  1. Update .env with your API keys"
echo "  2. Run demos: python examples/cve_and_ransomware_demo.py"
echo "  3. Run tests: pytest tests/ -v"
echo "  4. Lint code: flake8 . --count --select=E9,F63,F7,F82"
echo ""
echo "🔒 Security Note: Never commit API keys or sensitive data!"
