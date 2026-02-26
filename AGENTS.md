# Zen-AI-Pentest - Agent Guide

> **For AI Agents**: Essential information for understanding and working with the Zen-AI-Pentest codebase.

---

## 📋 Project Overview

**Zen-AI-Pentest** is a professional, autonomous AI-powered penetration testing framework that executes **real security tools** with intelligent orchestration. It is built for security professionals, bug bounty hunters, and enterprise security teams.

- **Name**: zen-ai-pentest
- **Version**: 3.0.0
- **License**: MIT
- **Python**: 3.9+
- **Repository**: https://github.com/SHAdd0WTAka/zen-ai-pentest
- **Status**: Production Ready

### 🎯 Core Philosophy: Real Data Execution (No Mocks!)

This framework executes **actual security tools** - no simulations:
- ✅ **Nmap** - Real port scanning with XML output parsing
- ✅ **Nuclei** - Real vulnerability detection with JSON output
- ✅ **SQLMap** - Real SQL injection testing with safety controls
- ✅ **72+ Tools** - Including FFuF, WhatWeb, WAFW00F, Subfinder, HTTPX, Nikto, and more
- ✅ **Multi-Agent** - Researcher, Analyst, Exploit agents cooperating
- ✅ **Docker Sandbox** - Isolated tool execution for safety

---

## 🏗️ Architecture

```
zen-ai-pentest/
├── agents/                 # AI Agent implementations (ReAct, orchestration)
│   ├── react_agent.py     # Core ReAct implementation
│   ├── agent_base.py      # Multi-agent base classes
│   ├── agent_orchestrator.py
│   └── research_agent.py, exploit_agent.py, analysis_agent.py
├── api/                    # FastAPI Backend
│   ├── main.py           # FastAPI app entry point
│   ├── auth*.py          # Authentication (JWT, RBAC)
│   ├── schemas.py        # Pydantic models
│   ├── websocket*.py     # WebSocket handlers
│   └── routes/           # API route handlers
├── autonomous/            # Autonomous agent system (ReAct Loop)
│   ├── agent_loop.py      # Core ReAct loop with REAL tool execution
│   ├── sqlmap_integration.py  # SQLMap with safety controls
│   ├── exploit_validator.py
│   └── memory.py
├── core/                  # Core framework components
│   ├── orchestrator.py    # ZenOrchestrator - Central coordination
│   ├── models.py          # Data models
│   ├── database.py        # Database connection management
│   ├── llm_backend.py     # Multi-LLM routing
│   └── workflow_engine.py
├── tools/                 # 72+ Security tool integrations
│   ├── nmap_integration.py
│   ├── nuclei_integration.py
│   ├── sqlmap_integration.py
│   ├── ffuf_integration.py
│   ├── subdomain_scan.py
│   └── tool_registry.py, tool_caller.py
├── guardrails/            # Security guardrails
│   ├── ip_validator.py    # Blocks private networks
│   ├── domain_validator.py
│   ├── risk_levels.py     # 4-level risk system
│   └── rate_limiter.py
├── risk_engine/           # Risk analysis engine
│   ├── cvss.py, epss.py
│   └── false_positive_engine.py
├── database/              # SQLAlchemy models
│   ├── models.py          # User, Scan, Finding, Report models
│   └── crud.py
├── integrations/          # CI/CD integrations (GitHub, GitLab, Slack, JIRA)
├── notifications/         # Alerts (Slack, Email, Discord, Telegram)
├── benchmarks/            # Performance testing
├── tests/                 # Test suite (300+ test files)
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   ├── security/         # Security tests (SAST, DAST)
│   └── autonomous/       # Autonomous agent tests
├── docs/                  # Documentation (70+ markdown files)
├── docker/                # Docker configurations
└── scripts/               # Utility scripts
```

---

## 💻 Technology Stack

### Core Dependencies
- **Python**: 3.9+ (Primary: 3.11)
- **Web Framework**: FastAPI 0.115.8+ (REST API + WebSocket)
- **Server**: Uvicorn 0.34.0+
- **Database**: PostgreSQL 15+ (SQLAlchemy 2.0+, Alembic migrations)
- **Cache/Queue**: Redis 7+ (Celery 5.3+ for task queue)
- **Validation**: Pydantic 2.0+
- **HTTP**: requests 2.32.0+, aiohttp 3.13.3+, urllib3 2.6.3+
- **DNS**: dnspython 2.7.0+

### Security & Cryptography
- **JWT**: PyJWT 2.8.0+
- **Password Hashing**: passlib 1.7.4+, bcrypt 4.0.0+
- **Cryptography**: cryptography 44.0.0+

### AI/LLM Integration
- **Framework**: LangChain 0.3.17+, langchain-core 0.3.35+
- **Backends**: Kimi AI (default), OpenAI, Anthropic, OpenRouter

### Container & Deployment
- **Docker**: docker 6.1.0+
- **Compose**: docker-compose 3.8+
- **Images**: python:3.11-slim, postgres:15-alpine, redis:7-alpine

### Data Processing
- **Data Analysis**: pandas 2.0.0+, numpy 1.24.0+
- **Reporting**: Jinja2 3.1.5+, WeasyPrint 61.0+ (PDF), markdown 3.5.0+

### Async & Utilities
- **Async**: asyncio, aiofiles 23.0.0+, websockets 12.0+
- **CLI**: click 8.1.0+, rich 13.0.0+, typer 0.9.0+
- **Config**: python-dotenv 1.0.0+, pyyaml 6.0.1+, pydantic-settings 2.0.0+

---

## 🔧 Build & Development Commands

### Setup

```bash
# 1. Clone and enter repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env with your settings (DATABASE_URL, SECRET_KEY, API keys)

# 5. Initialize database
python scripts/init_db.py

# 6. Install pre-commit hooks
pre-commit install
```

### Running the Application

```bash
# API server (development)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# API server (production)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2

# CLI mode
python zen_ai_pentest.py --interactive
python zen_cli.py

# Docker deployment
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Make Commands (Makefile)

```bash
make test           # Run tests
coverage            # Coverage report (terminal)
make coverage-xml   # Coverage XML for VS Code
make coverage-html  # Coverage HTML report
make open-coverage  # Open coverage in browser
make install        # Install dependencies and hooks
make setup          # Full setup
make clean          # Clean cache files
```

---

## 🧪 Testing Commands

### Running Tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# With coverage (HTML + terminal)
pytest --cov=. --cov-report=html --cov-report=term

# Specific test file
pytest tests/unit/test_react_agent.py -v

# Specific test class/method
pytest tests/unit/test_react_agent.py::TestReActAgent::test_reasoning -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Exclude slow tests
pytest -m "not slow"

# Security tests only
pytest tests/security/ -v
```

### Test Markers

- `slow`: Marks tests as slow (deselect with `-m "not slow"`)
- `integration`: Integration tests requiring external services
- `unit`: Unit tests (isolated)
- `security`: Security-focused tests

### Coverage Requirements

| Component | Minimum Coverage |
|-----------|-----------------|
| Core modules | 85% |
| API endpoints | 80% |
| Tool integrations | 75% |
| Security/guardrails | 100% |
| Database models | 80% |
| Risk engine | 90% |

---

## 📐 Code Style Guidelines

### Formatters & Linters

- **Black**: Code formatting (line length: 127)
- **isort**: Import sorting (black profile)
- **Ruff**: Linting (E, F, W rules)
- **mypy**: Type checking (optional)
- **Bandit**: Security linting

### Python Style Rules

```python
# Line length: 127 characters

# Imports: grouped and sorted (stdlib, third-party, local)
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI

from tools.nmap_integration import NmapScanner

# Class naming: PascalCase
class MyClassName:
    """Docstring with description.
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    """
    
    # Constants: UPPER_CASE
    MAX_RETRIES = 3
    
    def __init__(self, param1: str, param2: int = 10) -> None:
        """Initialize the class.
        
        Args:
            param1: First parameter
            param2: Second parameter (default: 10)
        """
        self.param1 = param1
        self._param2 = param2  # Private prefix with _

# Function naming: snake_case
def my_function_name(param: str) -> bool:
    """Function description.
    
    Args:
        param: Parameter description
        
    Returns:
        Boolean result
    """
    return True
```

### Running Code Quality Checks

```bash
# Format code
black .

# Check formatting
black --check .

# Sort imports
isort .

# Linting
ruff check .

# Security scan
bandit -r . -ll

# Run all pre-commit hooks
pre-commit run --all-files
```

### Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:
- Black (code formatting)
- isort (import sorting)
- Flake8 (linting)
- Trailing whitespace fixer
- YAML/JSON validator
- detect-private-key
- detect-secrets
- Bandit (security)

---

## 🛡️ Security Considerations

### Legal Responsibility

**⚠️ MANDATORY**: Always include these warnings when assisting with this framework:

```
⚠️ LEGAL WARNING: Only scan systems you own or have EXPLICIT WRITTEN
permission to test. Unauthorized scanning is ILLEGAL and can result in:
- Criminal prosecution
- Civil liability
- Fines and imprisonment

You are SOLELY RESPONSIBLE for your actions.
```

### Safety Controls (Guardrails)

The framework includes multi-layer protection:

| Control | Implementation |
|---------|---------------|
| Private IP Blocking | Blocks 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8 |
| Domain Filtering | Blocks .local, .internal, .corp, .home, localhost |
| Risk Levels | 4 levels (0=SAFE, 3=AGGRESSIVE) controlling tool access |
| Rate Limiting | Prevents accidental DoS |
| Docker Sandbox | Resource limits, read-only filesystems |
| Timeout Management | Default 300s per tool execution |

### Risk Levels

| Level | Name | Tools | Description |
|-------|------|-------|-------------|
| 0 | SAFE | whois, dns, subdomain | Reconnaissance only |
| 1 | NORMAL | + nmap, nuclei | Standard scanning |
| 2 | ELEVATED | + sqlmap, exploit | Light exploitation |
| 3 | AGGRESSIVE | + pivot, lateral | Full exploitation |

### For AI Agents Working on This Codebase

1. **Never commit API keys** - Use environment variables or Obsidian Vault
2. **Keep safety controls** - Don't disable IP blocking or domain filtering
3. **Validate all inputs** - Use guardrails validators
4. **Use timeouts** - Always set execution timeouts
5. **Test safely** - Use scanme.nmap.org for testing
6. **Docker isolation** - Use sandboxed executor when possible

---

## 🔐 Configuration & Secrets

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/zen_pentest

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION=3600

# AI Providers (Kimi AI recommended)
KIMI_API_KEY=your-kimi-api-key
DEFAULT_BACKEND=kimi
DEFAULT_MODEL=kimi-k2.5

# Alternative Backends (optional)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# OPENROUTER_API_KEY=...

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SMTP_HOST=smtp.gmail.com

# Cloud Providers
AWS_ACCESS_KEY_ID=AKIA...
AZURE_SUBSCRIPTION_ID=...
```

### Obsidian Vault (Recommended for Production)

Store secrets securely in an encrypted Obsidian vault:

```bash
# Setup Obsidian Secrets Vault
bash mcp/obsidian/setup.sh

# Edit secrets
~/Documents/Obsidian Vault/Secrets/secrets.yaml
```

---

## 🔄 CI/CD Pipeline

The project uses GitHub Actions with 70+ workflows:

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | Continuous Integration |
| `tests-coverage.yml` | Test execution and coverage |
| `security.yml` | Security scanning (Bandit, Snyk, CodeQL) |
| `docker.yml` | Docker image build and push |
| `pypi-release.yml` | PyPI package publishing |
| `deploy-cloudflare.yml` | Cloudflare Pages deployment |

### Pull Request Checklist

- [ ] Code follows style guide (Black, Ruff)
- [ ] All tests pass locally
- [ ] New code has test coverage (minimum 80%)
- [ ] Security components have 100% coverage
- [ ] No new security vulnerabilities (`bandit -r .`)
- [ ] Documentation updated

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Tool not found | Ensure tool is in PATH (nmap, sqlmap, nuclei) |
| Permission denied | Check Docker permissions or run with sudo |
| Timeout errors | Increase timeout in tool configuration |
| XML parsing fails | Validate tool output format |
| Import errors | Install requirements: `pip install -r requirements.txt` |
| Database connection | Check DATABASE_URL and PostgreSQL status |
| Redis connection | Verify Redis is running on port 6379 |

---

## 📚 Important Documentation

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `IMPLEMENTATION_SUMMARY.md` | Complete feature overview |
| `GUARDRAILS.md` | Security guardrails documentation |
| `CONTRIBUTING.md` | Contribution guidelines |
| `docs/DEVELOPMENT.md` | Development setup guide |
| `docs/TESTING.md` | Testing guide |
| `docs/API.md` | API reference |
| `VPN_INTEGRATION.md` | VPN setup and usage |

---

## 🚀 Quick Reference

### API Endpoints

```bash
# Authentication
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Create scan
curl -X POST http://localhost:8000/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Network Scan","target":"scanme.nmap.org","scan_type":"network"}'

# Execute tool
curl -X POST http://localhost:8000/tools/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tool_name":"nmap_scan","target":"scanme.nmap.org","parameters":{"ports":"22,80,443"}}'
```

### Project Scripts

```bash
# Initialize database
python scripts/init_db.py

# Run setup wizard
python setup_wizard.py

# Subdomain scan
python scan_target_subdomains.py

# Tool-specific scans
python tools/subdomain_enum.py example.com --advanced
```

---

## 📊 Project Status

**Current State: Production Ready (v3.0.0)**

- ✅ 72+ Integrated Security Tools
- ✅ Multi-Agent System with ReAct Pattern
- ✅ Risk Engine with CVSS/EPSS Scoring
- ✅ Docker Sandbox for Safe Execution
- ✅ FastAPI Backend with WebSocket
- ✅ PostgreSQL Database with SQLAlchemy
- ✅ 300+ Test Files
- ✅ CI/CD Pipeline with 70+ Workflows
- ✅ Security Guardrails (100% coverage required)

---

## 🤝 Contributing

When making changes:
1. Follow the existing code style (Black, line length 127)
2. Add tests for new features (minimum 80% coverage)
3. Update relevant documentation
4. Ensure safety controls are maintained
5. Run pre-commit hooks before committing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

*This document is for AI agents working on Zen-AI-Pentest. For human contributors, see README.md and CONTRIBUTING.md.*

**Last Updated**: 2026-02-25
