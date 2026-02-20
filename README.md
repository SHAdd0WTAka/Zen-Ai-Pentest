# Zen-AI-Pentest
![Repository Status](docs/status/repo_status_card.svg)

> 🛡️ **Professional AI-Powered Penetration Testing Framework**

[![Tests](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/workflows/Tests%20&%20Coverage/badge.svg)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions)
[![codecov](https://codecov.io/gh/SHAdd0WTAka/Zen-Ai-Pentest/branch/main/graph/badge.svg)](https://codecov.io/gh/SHAdd0WTAka/Zen-Ai-Pentest)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security Scan](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/workflows/Security%20Scan/badge.svg)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions)

[![Version](https://img.shields.io/badge/Version-3.0.0-orange)](https://github.com/SHAdd0WTAka/zen-ai-pentest/releases)
[![PyPI](https://img.shields.io/pypi/v/zen-ai-pentest?color=green)](https://pypi.org/project/zen-ai-pentest/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](docker/)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions)

[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&logoColor=white)](https://discord.gg/BSmCqjhY)
[![Docs](https://img.shields.io/badge/Docs-Complete-blue)](docs/)
[![OpenSSF](https://www.bestpractices.dev/projects/11957/badge?t=passing)](https://www.bestpractices.dev/de/projects/11957/passing)

---

## 📚 Table of Contents

- [⚡ Quick Start](#-quick-start)
- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Performance](#-performance)
- [Test Coverage](#-test-coverage)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Docker Deployment](#-docker-deployment)
- [Safety First](#-safety-first)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [Community & Support](#-community--support)
- [License](#-license)

---

## ⚡ Quick Start

Get started with Zen-AI-Pentest in under 5 minutes:

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# Start with Docker Compose
docker-compose up -d

# Access:
# Dashboard: http://localhost:3000
# API Docs:  http://localhost:8000/docs
# API:       http://localhost:8000
```

### Option 2: Python Package

```bash
# Install from PyPI
pip install zen-ai-pentest

# Quick scan
python -m zen_ai_pentest scan --target example.com
```

### Option 3: Local Development

```bash
# Clone and setup
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run
uvicorn api.main:app --reload
```

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

---

## 🎯 Overview

**Zen-AI-Pentest** is an autonomous, AI-powered penetration testing framework that combines cutting-edge language models with professional security tools. Built for security professionals, bug bounty hunters, and enterprise security teams.

### Key Capabilities

- 🤖 **AI-Powered**: Leverages state-of-the-art LLMs for intelligent decision making
- 🔒 **Security-First**: Multiple safety controls and validation layers
- 🚀 **Production-Ready**: Enterprise-grade with CI/CD, monitoring, and support
- 📊 **Comprehensive**: 40+ integrated security tools
- 🔧 **Extensible**: Plugin system for custom tools and integrations
- ☁️ **Cloud-Native**: Deploy on AWS, Azure, or GCP

---

## ✨ Features

### 🤖 Autonomous AI Agent
- **ReAct Pattern**: Reason → Act → Observe → Reflect
- **State Machine**: IDLE → PLANNING → EXECUTING → OBSERVING → REFLECTING → COMPLETED
- **Memory System**: Short-term, long-term, and context window management
- **Tool Orchestration**: Automatic selection and execution of 40+ pentesting tools
- **Self-Correction**: Retry logic and adaptive planning

### 🎯 Risk Engine
- **False Positive Reduction**: Multi-factor validation with Bayesian filtering
- **CVSS/EPSS Scoring**: Industry-standard vulnerability assessment
- **Priority Ranking**: Automated finding prioritization
- **LLM Voting**: Multi-model consensus for accuracy

### 🔒 Exploit Validation
- **Sandboxed Execution**: Docker-based isolated testing
- **Safety Controls**: 4-level safety system (Read-Only to Full)
- **Evidence Collection**: Screenshots, HTTP captures, PCAP
- **Chain of Custody**: Complete audit trail

### 🛠️ 40+ Integrated Tools

| Category | Tools |
|----------|-------|
| **Network** | Nmap, Masscan, Scapy, Tshark |
| **Web** | SQLMap, Gobuster, Nikto, FFuF |
| **Exploitation** | Metasploit Framework |
| **Brute Force** | Hydra, Hashcat |
| **Reconnaissance** | Amass, Nuclei, TheHarvester |
| **Active Directory** | BloodHound, CrackMapExec |

---

## 🏗️ Architecture

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT INTERFACE                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   🌐 Web UI  │  │   💻 CLI     │  │   🔌 API     │              │
│  │   (React)    │  │   (Python)   │  │   (REST)     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
└─────────┼─────────────────┼─────────────────┼───────────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │ HTTPS / JWT
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                                 │
│                    FastAPI + WebSocket                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   🔐 Auth    │ │   📋 Work-   │ │   🤖 Agent   │                │
│  │   (JWT/RBAC) │ │   flow API   │ │   Manager    │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW ORCHESTRATOR                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   🛡️         │  │   📊 Task    │  │   ⚠️ Risk    │              │
│  │   Guardrails │  │   Queue      │  │   Levels     │              │
│  │   (IP/Domain │  │              │  │   (0-3)      │              │
│  │   Filter)    │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   🔒 VPN     │  │   📈 State   │  │   📝 Report  │              │
│  │   Check      │  │   Machine    │  │   Generator  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ WebSocket + Task Distribution
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT POOL                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   🤖 Agent   │  │   🤖 Agent   │  │   🤖 Agent   │              │
│  │   #1         │  │   #2         │  │   #N         │              │
│  │   (Docker)   │  │   (Docker)   │  │   (Docker)   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
└─────────┼─────────────────┼─────────────────┼───────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SECURITY TOOLKIT                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │   🔍     │ │   📡     │ │   🌐     │ │   ⚡     │ │   🎯     │  │
│  │   nmap   │ │  whois   │ │   dig    │ │  nuclei  │ │  sqlmap  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   🐘 Postgre │  │   ⚡ Redis   │  │   📁 File    │              │
│  │   SQL        │  │   Cache      │  │   Storage    │              │
│  │   (State)    │  │   (Queue)    │  │   (Reports)  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### Architecture Components

| Layer | Purpose | Technologies |
|-------|---------|--------------|
| **Client** | User interfaces | React, CLI, REST API |
| **API Gateway** | Request handling | FastAPI, WebSocket |
| **Orchestrator** | Workflow management | Celery, Redis |
| **Agent Pool** | AI agent execution | Docker, Python |
| **Tools** | Security tools | Nmap, SQLMap, Nuclei |
| **Data** | Persistence | PostgreSQL, Redis |

For detailed architecture, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📖 Installation

### Prerequisites

- Python 3.11+ (for local installation)
- Docker 20.10+ (for Docker installation)
- 4GB RAM minimum, 8GB recommended
- 10GB disk space

### Docker Installation (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# 2. Copy environment file
cp .env.example .env
# Edit .env with your settings

# 3. Start services
docker-compose up -d

# 4. Verify
docker-compose ps
curl http://localhost:8000/health
```

### Local Installation

```bash
# 1. Clone repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Initialize database
python scripts/init_db.py

# 6. Run server
uvicorn api.main:app --reload
```

### Platform-Specific Instructions

- **Windows**: See [docs/INSTALLATION.md#windows](docs/INSTALLATION.md#windows)
- **Linux**: See [docs/INSTALLATION.md#linux](docs/INSTALLATION.md#linux)
- **macOS**: See [docs/INSTALLATION.md#macos](docs/INSTALLATION.md#macos)

---

## 💻 Usage

### Python API

```python
from agents.react_agent import ReActAgent, ReActAgentConfig

# Configure agent
config = ReActAgentConfig(
    max_iterations=10,
    use_vm=True,
    vm_name="kali-pentest"
)

# Create agent
agent = ReActAgent(config)

# Run autonomous scan
result = agent.run(
    target="example.com",
    objective="Comprehensive security assessment"
)

# Generate report
print(agent.generate_report(result))
```

### REST API

```bash
# Authentication
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Create scan
curl -X POST http://localhost:8000/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Network Scan",
    "target": "192.168.1.0/24",
    "scan_type": "network"
  }'

# Execute tool
curl -X POST http://localhost:8000/tools/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "tool_name": "nmap_scan",
    "target": "scanme.nmap.org",
    "parameters": {"ports": "22,80,443"}
  }'
```

### CLI Usage

```bash
# Quick scan
zen-cli scan --target example.com

# Full scan with all tools
zen-cli scan --target example.com --full

# List available tools
zen-cli tools list

# Execute specific tool
zen-cli tools run nmap_scan --target example.com
```

---

## 📡 API Reference

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Authenticate and get token |
| `/scans` | GET/POST | List/create scans |
| `/scans/{id}/findings` | GET | Get scan findings |
| `/tools/execute` | POST | Execute security tool |
| `/reports` | POST | Generate report |

See [docs/API_GUIDE.md](docs/API_GUIDE.md) for complete API documentation.

---

## 📊 Performance

### Benchmarks

Performance tested on AWS EC2 t3.medium (2 vCPU, 4GB RAM):

| Operation | Time | Notes |
|-----------|------|-------|
| Nmap Top 1000 Ports | ~15s | TCP SYN scan |
| Nuclei Basic Scan | ~30s | 1000+ templates |
| SQLMap Detection | ~60s | Level 1, Risk 1 |
| Full Web Assessment | ~5min | Multiple tools |
| Report Generation (PDF) | ~10s | 100 findings |

### Scalability

- **Concurrent Scans**: 10+ (with 4 workers)
- **Concurrent Users**: 100+ (with proper DB connection pooling)
- **Findings Storage**: Millions (with PostgreSQL partitioning)

### Optimization Tips

1. **Use Redis caching** for repeated scans
2. **Enable connection pooling** for database
3. **Scale workers** based on CPU cores
4. **Use SSD storage** for database

See [docs/BENCHMARKS.md](docs/BENCHMARKS.md) for detailed benchmarks.

---

## 🧪 Test Coverage

### Current Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| Core Modules | 85% | ✅ |
| API Endpoints | 80% | ✅ |
| Tool Integrations | 75% | ✅ |
| Security/Guardrails | 100% | ✅ |
| Risk Engine | 90% | ✅ |

### Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=. --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Coverage Badges

[![codecov](https://codecov.io/gh/SHAdd0WTAka/zen-ai-pentest/branch/main/graph/badge.svg)](https://codecov.io/gh/SHAdd0WTAka/zen-ai-pentest)

See [docs/TESTING.md](docs/TESTING.md) for detailed testing documentation.

---

## 📁 Project Structure

```
zen-ai-pentest/
├── agents/                    # AI Agent implementations
├── api/                       # FastAPI Backend
├── autonomous/               # Autonomous agent system
├── tools/                    # Security tool integrations
├── risk_engine/              # Risk analysis engine
├── database/                 # Database models
├── tests/                    # Test suite
├── docs/                     # Documentation
├── docker/                   # Docker configurations
├── scripts/                  # Utility scripts
└── README.md                 # This file
```

---

## 🔧 Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/zen_pentest

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION=3600

# AI Providers
KIMI_API_KEY=your-kimi-api-key
DEFAULT_BACKEND=kimi
DEFAULT_MODEL=kimi-k2.5

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SMTP_HOST=smtp.gmail.com
```

See `.env.example` for all options.

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_react_agent.py -v

# Integration tests
pytest tests/integration/ -v
```

See [docs/TESTING.md](docs/TESTING.md) for detailed testing guide.

---

## 🐳 Docker Deployment

### Quick Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale workers
docker-compose up -d --scale worker=3
```

### Production Deployment

```bash
# Production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

See [DOCKER.md](DOCKER.md) for complete Docker documentation.

---

## 🛡️ Safety First

### Default Protections

- ✅ **Private IP Blocking** - Prevents scanning 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- ✅ **Loopback Protection** - Blocks 127.x.x.x and ::1
- ✅ **Local Domain Filter** - Prevents .local, .internal, localhost
- ✅ **Risk Level Control** - Restricts tools by safety level
- ✅ **Rate Limiting** - Prevents abuse

### Risk Levels

| Level | Tools | Description |
|-------|-------|-------------|
| **SAFE (0)** | whois, dns, subdomain | Reconnaissance only |
| **NORMAL (1)** | + nmap, nuclei | Standard scanning |
| **ELEVATED (2)** | + sqlmap, exploit | Light exploitation |
| **AGGRESSIVE (3)** | + pivot, lateral | Full exploitation |

⚠️ **Always ensure you have authorization before scanning!**

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Get started in 5 minutes |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Development guide |
| [docs/TESTING.md](docs/TESTING.md) | Testing guide |
| [docs/API_GUIDE.md](docs/API_GUIDE.md) | API documentation |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Troubleshooting guide |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [DOCKER.md](DOCKER.md) | Docker deployment |
| [GUARDRAILS.md](GUARDRAILS.md) | Security guardrails |

---

## 🤝 Contributing

We welcome contributions! Please see:

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development setup
- [docs/TESTING.md](docs/TESTING.md) - Testing requirements
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community standards

Quick start:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 🌐 Community & Support

### Quick Links

| Platform | Link |
|----------|------|
| 🎮 **Discord** | [discord.gg/zJZUJwK9AC](https://discord.gg/zJZUJwK9AC) |
| 💬 **GitHub Discussions** | [Discussions](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions) |
| 🐛 **Issue Tracker** | [Issues](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues) |
| 📧 **Email** | support@zen-ai-pentest.dev |

### Documentation

- [Complete Documentation](docs/)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Support](SUPPORT.md)

---

## ⚠️ Disclaimer

**IMPORTANT**: This tool is for authorized security testing only. Always obtain proper permission before testing any system you do not own. Unauthorized access to computer systems is illegal.

- Use only on systems you have explicit permission to test
- Respect privacy and data protection laws
- The authors assume no liability for misuse or damage

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent framework
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Kali Linux](https://www.kali.org/) - Penetration testing distribution
- All open-source security tool creators

---

## 👥 Authors & Team

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/SHAdd0WTAka">
        <img src="https://github.com/SHAdd0WTAka.png?size=100" width="100px;" alt="SHAdd0WTAka"/>
        <br />
        <sub><b>@SHAdd0WTAka</b></sub>
      </a>
      <br />
      <sub>Project Founder & Lead Developer</sub>
    </td>
    <td align="center">
      <a href="https://www.moonshot.cn/">
        <img src="https://img.shields.io/badge/Kimi-AI-blue?style=for-the-badge&logo=openai&logoColor=white" width="100px;" alt="Kimi AI"/>
        <br />
        <sub><b>Kimi AI</b></sub>
      </a>
      <br />
      <sub>AI Development Partner</sub>
    </td>
  </tr>
</table>

---

<p align="center">
  <b>Made with ❤️ for the security community</b><br>
  <sub>© 2026 Zen-AI-Pentest. All rights reserved.</sub>
</p>
