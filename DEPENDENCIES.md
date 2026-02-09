# Dependencies Installation Guide

Complete guide for installing all dependencies for Zen AI Pentest.

## 🚀 Quick Install

### Option 1: Automated Install (Recommended)

**Linux/Mac:**
```bash
chmod +x install-all-dependencies.sh
./install-all-dependencies.sh
```

**Windows (PowerShell):**
```powershell
.\install-all-dependencies.ps1
```

### Option 2: Manual Install

**Step 1: Create Virtual Environment**
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

**Step 2: Install Python Dependencies**
```bash
# Main dependencies only
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt

# Zen Shield
pip install -r zen_shield/requirements.txt

# Or install everything at once
pip install -r requirements-all.txt
```

**Step 3: Install Node.js Dependencies**
```bash
cd postman
npm install
cd ..
```

## 📦 Dependency Categories

### Core Application (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.104.0 | API Framework |
| uvicorn | >=0.24.0 | ASGI Server |
| pydantic | >=2.5.0 | Data Validation |
| aiohttp | >=3.8.0 | Async HTTP Client |
| asyncpg | >=0.29.0 | PostgreSQL Driver |
| redis | >=5.0.0 | Cache |
| sqlalchemy | >=2.0.0 | ORM |
| python-jose | >=3.3.0 | JWT Tokens |
| passlib | >=1.7.4 | Password Hashing |

### Development (`requirements-dev.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=7.0.0 | Testing Framework |
| black | >=23.0.0 | Code Formatting |
| flake8 | >=6.0.0 | Linting |
| mypy | >=1.0.0 | Type Checking |
| bandit | >=1.7.0 | Security Scanning |
| sphinx | >=6.0.0 | Documentation |

### Zen Shield (`zen_shield/requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.104.0 | Sanitizer API |
| aiohttp | >=3.9.0 | HTTP Client |

### Postman/Newman (`postman/package.json`)

| Package | Version | Purpose |
|---------|---------|---------|
| newman | ^6.0.0 | CLI Collection Runner |
| newman-reporter-htmlextra | ^1.22.0 | HTML Reports |

### Security & Config (Optional)

| Package | Version | Purpose |
|---------|---------|---------|
| keyring | >=24.0.0 | Secure Credential Storage |
| cryptography | >=41.0.0 | Encryption |
| python-dotenv | >=1.0.0 | Environment Variables |

## 🐍 Python Version

**Required:** Python 3.9 or higher

**Recommended:** Python 3.11 or 3.12

**Check version:**
```bash
python --version
```

## 📋 All-in-One Installation Commands

### Ubuntu/Debian
```bash
# System dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nodejs npm

# Clone and install
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest
chmod +x install-all-dependencies.sh
./install-all-dependencies.sh
```

### macOS
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python node

# Clone and install
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest
chmod +x install-all-dependencies.sh
./install-all-dependencies.sh
```

### Windows
```powershell
# Install Chocolatey if not present
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install python nodejs

# Clone and install
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest
.\install-all-dependencies.ps1
```

## ✅ Verification

After installation, verify everything is working:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Check Python packages
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')"
python -c "import aiohttp; print(f'aiohttp: {aiohttp.__version__}')"

# Check Node.js packages
cd postman
npm list newman
cd ..

# Run tests
pytest tests/ -v --tb=short
```

## 🐳 Docker Alternative

If you prefer Docker over local installation:

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.pentest.yml up -d

# This includes all dependencies pre-installed
```

## 🔄 Updating Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade fastapi

# Check for outdated packages
pip list --outdated
```

## 🧹 Clean Installation

If you encounter issues, try a clean install:

```bash
# Remove virtual environment
rm -rf venv/

# Remove Node modules
cd postman
rm -rf node_modules/
cd ..

# Reinstall
./install-all-dependencies.sh  # or .ps1 on Windows
```

## ❓ Troubleshooting

### "pip not found"
```bash
# Install pip
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### "Permission denied"
```bash
# Use --user flag
pip install --user -r requirements.txt
```

### "Node.js not found"
Download from: https://nodejs.org/

### "Virtual environment activation fails"
On Windows PowerShell, you may need to set execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📊 Disk Space Requirements

- Python packages: ~200-300 MB
- Node.js packages: ~100-150 MB
- Virtual environment overhead: ~50 MB

**Total:** ~400-500 MB

## 🔗 Related Files

- `requirements.txt` - Main dependencies
- `requirements-dev.txt` - Development tools
- `requirements-all.txt` - Everything combined
- `zen_shield/requirements.txt` - Shield module
- `postman/package.json` - Node.js dependencies
