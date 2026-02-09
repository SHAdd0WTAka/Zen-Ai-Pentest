#!/bin/bash
# Install all dependencies for Zen AI Pentest
# Run this script to install Python, Node.js, and all project dependencies

set -e

echo "🚀 Installing all dependencies for Zen AI Pentest..."
echo "======================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.9+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js is not installed${NC}"
    echo "Some features (Postman tests) will not be available"
    echo "Install from: https://nodejs.org"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "\n📦 Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n🔄 Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Upgrade pip
echo -e "\n⬆️  Upgrading pip..."
pip install --upgrade pip

# Install main requirements
echo -e "\n📥 Installing main Python dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Main dependencies installed${NC}"

# Install dev requirements
echo -e "\n🛠️  Installing development dependencies..."
pip install -r requirements-dev.txt
echo -e "${GREEN}✓ Development dependencies installed${NC}"

# Install Zen Shield requirements
echo -e "\n🛡️  Installing Zen Shield dependencies..."
pip install -r zen_shield/requirements.txt
echo -e "${GREEN}✓ Zen Shield dependencies installed${NC}"

# Install optional dependencies for better functionality
echo -e "\n✨ Installing optional dependencies..."
pip install keyring cryptography python-dotenv || true
echo -e "${GREEN}✓ Optional dependencies installed${NC}"

# Node.js dependencies (Postman)
if command -v npm &> /dev/null; then
    echo -e "\n📮 Installing Postman/Newman dependencies..."
    cd postman
    npm install
    cd ..
    echo -e "${GREEN}✓ Postman dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping Postman dependencies (npm not found)${NC}"
fi

# Create necessary directories
echo -e "\n📁 Creating necessary directories..."
mkdir -p logs evidence data/sql_injection templates/reports shared/scans shared/reports
echo -e "${GREEN}✓ Directories created${NC}"

# Summary
echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}✅ All dependencies installed successfully!${NC}"
echo -e "${GREEN}======================================================${NC}"
echo ""
echo "📝 Next steps:"
echo "   1. Activate virtual environment:"
echo "      source venv/bin/activate  (Linux/Mac)"
echo "      venv\Scripts\activate     (Windows)"
echo ""
echo "   2. Run the application:"
echo "      python -m api.main"
echo ""
echo "   3. Or run tests:"
echo "      pytest tests/"
echo ""
echo "📚 Documentation:"
echo "   - API docs: http://localhost:8000/docs (after starting)"
echo "   - README.md for more information"
echo ""
