# Build Instructions

This document describes how to build Zen-AI-Pentest from source.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- (Optional) Docker and Docker Compose

## Build Steps

### 1. Clone the Repository

```bash
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Development Dependencies (Optional)

```bash
pip install -r requirements-dev.txt  # If available
# Or install common dev tools
pip install pytest pytest-cov black isort ruff bandit safety mypy
```

### 5. Verify Installation

```bash
python -c "import zen_ai_pentest; print('Installation successful')"
```

## Building Documentation

```bash
cd docs
pip install mkdocs mkdocs-material
mkdocs build
```

## Building Docker Image

```bash
docker build -t zen-ai-pentest:latest .
```

Or using Docker Compose:

```bash
docker-compose build
```

## Running Tests

```bash
pytest tests/ -v --tb=short
```

## Code Quality Checks

```bash
# Linting
ruff check .

# Security scanning
bandit -r . -ll

# Type checking
mypy core/ agents/ --ignore-missing-imports
```

## Reproducible Builds

This project supports reproducible builds through:

1. **Pinned Dependencies**: `requirements.txt` contains exact versions
2. **Lock Files**: `package-lock.json` for Node.js dependencies
3. **Docker**: Consistent build environment via Dockerfile

## Build Verification

After building, verify the installation:

```bash
python zen_ai_pentest.py --version
python -m pytest tests/unit/ -q
```

## Troubleshooting

### Import Errors
- Ensure virtual environment is activated
- Check Python version (3.9+ required)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Permission Issues (Linux/Mac)
```bash
chmod +x scripts/*.sh
```

### Windows-Specific
- Use PowerShell or Git Bash for shell scripts
- Ensure Python is added to PATH

---

For more information, see [INSTALLATION.md](INSTALLATION.md).
