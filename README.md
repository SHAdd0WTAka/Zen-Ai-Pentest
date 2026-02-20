# Zen-AI-Pentest
![Repository Status](docs/status/repo_status_card.svg)

> 🛡️ **Professional AI-Powered Penetration Testing Framework**

[![Tests](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/workflows/Tests%20&%20Coverage/badge.svg)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions)
[![codecov](https://codecov.io/gh/SHAdd0WTAka/Zen-Ai-Pentest/branch/main/graph/badge.svg)](https://codecov.io/gh/SHAdd0WTAka/Zen-Ai-Pentest)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security Scan](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/workflows/Security%20Scan%20(Improved)/badge.svg)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions)

- **Guest Control**: Execute tools inside isolated VMs

### 🚀 Modern API & Backend
- **FastAPI**: High-performance REST API
- **PostgreSQL**: Persistent data storage
- **WebSocket**: Real-time scan updates
- **JWT Auth**: Role-based access control (RBAC)
- **Background Tasks**: Async scan execution

### 📊 Reporting & Notifications
- **PDF Reports**: Professional findings reports
- **HTML Dashboard**: Interactive web interface
- **Slack/Email**: Instant notifications
- **JSON/XML**: Integration with other tools

### 🐳 Easy Deployment
- **Docker Compose**: One-command full stack deployment
- **CI/CD**: GitHub Actions pipeline
- **Production Ready**: Optimized for enterprise use

---

## 🎯 Real Data Execution - No Mocks!

Zen-AI-Pentest executes **real security tools** - no simulations, no mocks, only actual tool execution:

- ✅ **Nmap** - Real port scanning with XML output parsing
- ✅ **Nuclei** - Real vulnerability detection with JSON output
- ✅ **SQLMap** - Real SQL injection testing with safety controls
- ✅ **FFuF** - Blazing fast web fuzzer
- ✅ **WhatWeb** - Technology detection (900+ plugins)
- ✅ **WAFW00F** - WAF detection (50+ signatures)
- ✅ **Subfinder** - Subdomain enumeration
- ✅ **HTTPX** - Fast HTTP prober
- ✅ **Nikto** - Web vulnerability scanner
- ✅ **Multi-Agent** - Researcher & Analyst agents cooperate
- ✅ **Docker Sandbox** - Isolated tool execution for safety

📖 **Enhanced Tools:** [README_ENHANCED_TOOLS.md](README_ENHANCED_TOOLS.md)

All tools run with **safety controls**:
- Private IP blocking (protects internal networks)
- Timeout management (prevents hanging)
- Resource limits (CPU/memory constraints)
- Read-only filesystems (Docker sandbox)

📖 **Details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## 🚀 Quick Start

[![Version](https://img.shields.io/badge/Version-3.0.0-orange)](https://github.com/SHAdd0WTAka/zen-ai-pentest/releases)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Commits](https://img.shields.io/badge/Commits-740+-brightgreen)](https://github.com/SHAdd0WTAka/zen-ai-pentest/commits/main)
[![Phase](https://img.shields.io/badge/Phase-6%20AI%20Personas-blueviolet)](./docs/status/repo_status_card.svg)

[![PyPI](https://img.shields.io/pypi/v/zen-ai-pentest?color=green)](https://pypi.org/project/zen-ai-pentest/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](docker/)
[![Tests](https://img.shields.io/badge/Tests-40%2B%20Tools-brightgreen)](tools/)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions)
[![Security](https://img.shields.io/badge/Security-Passing-brightgreen)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/SHAdd0WTAka/zen-ai-pentest/branch/main/graph/badge.svg)](https://codecov.io/gh/SHAdd0WTAka/zen-ai-pentest)

[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&logoColor=white)](https://discord.gg/BSmCqjhY)
[![Docs](https://img.shields.io/badge/Docs-Complete-blue)](docs/)
[![Roadmap](https://img.shields.io/badge/Roadmap-2026-blueviolet)](ROADMAP_2026.md)
[![OpenSSF](https://www.bestpractices.dev/projects/11957/badge?t=passing)](https://www.bestpractices.dev/de/projects/11957/passing)
[![Marketplace](https://img.shields.io/badge/Marketplace-Action-green?logo=github)](https://github.com/marketplace/actions/zen-ai-pentest)
[![Authors](https://img.shields.io/badge/Authors-SHAdd0WTAka%20%7C%20KimiAI-purple)](#-authors--team)

---

## 📚 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
  - [For AI Agents](#-for-ai-agents)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [API Reference](#-api-reference)
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

## 🎯 Overview

**Zen-AI-Pentest** is an autonomous, AI-powered penetration testing framework that combines cutting-edge language models with professional security tools. Built for security professionals, bug bounty hunters, and enterprise security teams.

```mermaid
  graph TB
      subgraph "Client Interface"
          WebUI[🌐 Web UI]
          CLI[💻 CLI]
          API_Client[🔌 REST API]
      end

      subgraph "API Gateway"
          FastAPI[FastAPI + WebSocket]
          Auth[🔐 JWT/RBAC]
          AgentMgr[🤖 Agent Manager]
      end

      subgraph "Workflow Orchestrator"
          Guardrails[🛡️ Guardrails]
          TaskQueue[📊 Task Queue]
          RiskLevels[⚠️ Risk Levels 0-3]
          VPN[🔒 VPN Check]
          State[📈 State Machine]
      end

      subgraph "Agent Pool"
          Agent1[🤖 Agent #1]
          Agent2[🤖 Agent #2]
          AgentN[🤖 Agent #N]
      end

      subgraph "Security Toolkit"
          Nmap[🔍 nmap]
          Whois[📡 whois]
          Dig[🌐 dig]
          Nuclei[⚡ nuclei]
          SQLMap[🎯 sqlmap]
      end

      subgraph "Data Layer"
          Postgres[🐘 PostgreSQL]
          Redis[⚡ Redis Cache]
          Storage[📁 File Storage]
      end

      WebUI --> FastAPI
      CLI --> FastAPI
      API_Client --> FastAPI
      FastAPI --> Auth
      Auth --> AgentMgr
      AgentMgr --> Guardrails
      Guardrails --> TaskQueue
      TaskQueue --> RiskLevels
      RiskLevels --> VPN
      VPN --> State
      State --> Agent1
      State --> Agent2
      State --> AgentN
      Agent1 --> Nmap
      Agent1 --> Whois
      Agent2 --> Dig
      Agent2 --> Nuclei
      AgentN --> SQLMap
      Nmap --> Postgres
      Whois --> Redis
      SQLMap --> Storage
```

### Key Highlights

- 🤖 **AI-Powered**: Leverages state-of-the-art LLMs for intelligent decision making
- 🔒 **Security-First**: Multiple safety controls and validation layers
- 🚀 **Production-Ready**: Enterprise-grade with CI/CD, monitoring, and support
- 📊 **Comprehensive**: 40+ integrated security tools
- 🔧 **Extensible**: Plugin system for custom tools and integrations
- ☁️ **Cloud-Native**: Deploy on AWS, Azure, or GCP
- 📱 **Quick Access**: Scan QR codes for instant mobile access

<p align="center">
  <a href="docs/qr_codes/index.html">
    <img src="docs/qr_codes/qr_grid_preview.png" alt="QR Codes" width="600">
  </a>
  <br>
  <sub>☝️ Click to view all QR codes or scan with your phone!</sub>
</p>

---

## ✨ Features

### 🤖 Autonomous AI Agent
- **ReAct Pattern**: Reason → Act → Observe → Reflect
- **State Machine**: IDLE → PLANNING → EXECUTING → OBSERVING → REFLECTING → COMPLETED
- **Memory System**: Short-term, long-term, and context window management
- **Tool Orchestration**: Automatic selection and execution of 20+ pentesting tools
- **Self-Correction**: Retry logic and adaptive planning
- **Human-in-the-Loop**: Optional pause for critical decisions

### 🎯 Risk Engine
- **False Positive Reduction**: Multi-factor validation with Bayesian filtering
- **Business Impact**: Financial, compliance, and reputation risk calculation
- **CVSS/EPSS Scoring**: Industry-standard vulnerability assessment
- **Priority Ranking**: Automated finding prioritization
- **LLM Voting**: Multi-model consensus for accuracy

### 🔒 Exploit Validation
- **Sandboxed Execution**: Docker-based isolated testing
- **Safety Controls**: 4-level safety system (Read-Only to Full)
- **Evidence Collection**: Screenshots, HTTP captures, PCAP
- **Chain of Custody**: Complete audit trail
- **Remediation**: Automatic fix recommendations

### 📊 Benchmarking
- **Competitor Comparison**: vs PentestGPT, AutoPentest, Manual
- **Test Scenarios**: HTB machines, OWASP WebGoat, DVWA
- **Metrics**: Time-to-find, coverage, false positive rate
- **Visual Reports**: Charts and statistical analysis
- **CI Integration**: Automated regression testing

### 🔗 CI/CD Integration
- **GitHub Actions**: Native action support
- **GitLab CI**: Pipeline integration
- **Jenkins**: Plugin and pipeline support
- **Output Formats**: JSON, JUnit XML, SARIF
- **Notifications**: Slack, JIRA, Email alerts
- **Exit Codes**: Pipeline-friendly status codes

### 🧠 AI Persona System
- **11 Specialized Personas**: Recon, Exploit, Report, Audit, Social, Network, Mobile, Red Team, ICS, Cloud, Crypto
- **CLI Tool**: Interactive and one-shot modes (`k-recon`, `k-exploit`, etc.)
- **REST API**: Flask-based API with WebSocket support
- **Web UI**: Modern browser interface with screenshot analysis
- **Context Preservation**: Multi-turn conversations with memory
- **Screenshot Analysis**: Upload and analyze images with AI personas

### 🛡️ Security Guardrails
- **IP Validation** - Blocks private networks (10.x, 192.168.x, 172.16-31.x)
- **Domain Filtering** - Prevents localhost/internal domain scanning
- **Risk Levels** - 4 levels (SAFE → AGGRESSIVE) with tool restrictions
- **Rate Limiting** - Prevents accidental DoS

### 🤖 Multi-Agent System
- **Workflow Orchestrator** - Manages complex pentest workflows
- **Task Distribution** - Assigns tasks to available agents
- **Real-time Updates** - WebSocket communication
- **Result Aggregation** - Collects and analyzes findings

### 🔒 VPN Integration (Optional)
- **ProtonVPN Support** - Native CLI integration
- **Generic Detection** - Works with OpenVPN, WireGuard, etc.
- **Safety Warnings** - Alerts when scanning without VPN
- **Strict Mode** - Can require VPN for scans

### 🐳 Docker Ready
- **One-Command Deploy** - `docker-compose up -d`
- **Isolated Environment** - All tools pre-installed
- **Scalable** - Run multiple agents
- **Production Ready** - Health checks & monitoring

### 🛠️ 40+ Integrated Tools
| Category | Tools |
|----------|-------|
| **Network** | Nmap, Masscan, Scapy, Tshark |
| **Web** | BurpSuite, SQLMap, Gobuster, OWASP ZAP |
| **Exploitation** | Metasploit Framework |
| **Brute Force** | Hydra, Hashcat |
| **Reconnaissance** | Amass, Nuclei, TheHarvester, Subdomain Scanner |
| **Active Directory** | BloodHound, CrackMapExec, Responder |
| **Wireless** | Aircrack-ng Suite |

### 🔍 Subdomain Scanner
- **Multi-Technique Enumeration**: DNS, Wordlist, Certificate Transparency
- **Advanced Techniques**: Zone Transfer (AXFR), Permutation/Mangling
- **OSINT Integration**: VirusTotal, AlienVault OTX, BufferOver
- **IPv6 Support**: AAAA record enumeration
- **Technology Detection**: Automatic fingerprinting of live hosts
- **Export Formats**: JSON, CSV, TXT
- **REST API**: Async and sync scanning endpoints
- **CLI Tools**: Standalone scanner with comprehensive options

### 🤖 For AI Agents
- **[AGENTS.md](AGENTS.md)** - Essential guide for AI development partners
- **Real Tool Execution** - No mocks, actual security tools
- **Multi-Agent System** - Researcher, Analyst, Exploit agents
- **Safety Controls** - 4-level sandbox system
- **Architecture Guide** - Complete system overview

### 🔔 Notifications & Integrations
- **Telegram Bot**: @Zenaipenbot - Instant CI/CD notifications
- **Discord Integration**: Automated channel updates & GitHub webhooks
- **Slack/Email**: Enterprise notification support
- **GitHub Actions**: Native workflow integration
- **QR Code Gallery**: Quick access to all resources

### ☁️ Multi-Cloud & Virtualization
- **Local**: VirtualBox VM Management
- **Cloud**: AWS EC2, Azure VMs, Google Cloud Compute
- **Snapshots**: Automated clean-state workflows
### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start full stack
docker-compose up -d

# Access:
# Dashboard: http://localhost:3000
# API Docs:  http://localhost:8000/docs
# API:       http://localhost:8000
```

### Option 2: Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python database/models.py

# Start API server
python api/main.py

# Run subdomain scan
python scan_target_subdomains.py

# Or use the advanced CLI
python tools/subdomain_enum.py example.com --advanced
```

### Option 3: AI Personas Quick Start

```bash
# Start the AI Personas API & Web UI
bash api/QUICKSTART.sh

# Or manually:
bash api/manage.sh start
# Open http://127.0.0.1:5000

# CLI Usage
source tools/setup_aliases.sh
k-recon "Target: example.com"
k-exploit "Write SQLi scanner"
k-chat  # Interactive mode
```

### Option 4: VirtualBox VM Setup

```bash
# Automated Kali Linux setup
python scripts/setup_vms.py --kali

# Manual setup
# See docs/setup/VIRTUALBOX_SETUP.md
```

---

## 📖 Installation

For detailed installation instructions, see:
- **[Docker Installation](docs/INSTALLATION.md#quick-start-docker)**
- **[Local Installation](docs/INSTALLATION.md#local-installation)**
- **[Production Deployment](docs/INSTALLATION.md#production-deployment)**
- **[VirtualBox Setup](docs/setup/VIRTUALBOX_SETUP.md)**

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
  -d '{"name":"Network Scan","target":"192.168.1.0/24","scan_type":"network","config":{"ports":"top-1000"}}'

# Execute tool
curl -X POST http://localhost:8000/tools/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tool_name":"nmap_scan","target":"scanme.nmap.org","parameters":{"ports":"22,80,443"}}'

# Generate report
curl -X POST http://localhost:8000/reports \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"scan_id":1,"format":"pdf","template":"default"}'
```

### WebSocket (Real-Time)

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/scans/1");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Scan update:", data);
};
```

---

## 🏗️ System Architecture

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
│  │          │ │          │ │          │ │          │ │          │  │
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

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📡 API Reference

- **[API Documentation](docs/API.md)** - Complete REST API reference
- **[WebSocket API](docs/API.md#websocket)** - Real-time updates
- **[Authentication](docs/API.md#authentication)** - Security and auth

---

## 📁 Project Structure

```
zen-ai-pentest/
├── api/                   # FastAPI Backend (main.py, auth.py, websocket.py)
├── agents/                # AI Agents (react_agent.py, react_agent_vm.py)
├── autonomous/            # ReAct Loop (agent_loop.py, exploit_validator.py, memory.py)
├── tools/                 # 40+ Security Tools
│   ├── Network: nmap, masscan, scapy, tshark
│   ├── Web: nuclei, sqlmap, nikto, zap, burpsuite, ffuf, gobuster
│   ├── Recon: subfinder, amass, httpx, whatweb, wafw00f, subdomain_scan, unified_recon
│   ├── AD: bloodhound, crackmapexec, responder
│   ├── OSINT: sherlock, scout, ignorant
│   ├── Secrets: trufflehog, trivy
│   ├── Wireless: aircrack
│   ├── Code: semgrep
│   ├── AI/Kimi: kimi_cli, kimi_helper, update_personas
│   └── Core: tool_caller, tool_registry
├── risk_engine/           # Risk Analysis (cvss.py, epss.py, false_positive_engine.py)
├── benchmarks/            # Performance Testing
├── integrations/          # CI/CD (github, gitlab, slack, jira, jenkins)
├── database/              # PostgreSQL Models
├── gui/                   # React Dashboard
├── reports/               # PDF/HTML/JSON Generator
├── notifications/         # Alerts (slack, email)
├── docker/                # Deployment configs
├── docs/                  # Documentation (ARCHITECTURE.md, INSTALLATION.md, API.md, setup/)
├── tests/                 # Test Suite
└── scripts/               # Setup Scripts
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

---

## 🐳 Docker Deployment

### Quick Setup (WSL2 + Docker)

Wir empfehlen Docker in WSL2 (Ubuntu) für die beste Performance:

**Option 1: Automatisches Setup**
```bash
# Windows: Setup-Launcher starten
scripts\docker-setup.bat

# Oder direkt in Ubuntu WSL:
./scripts/setup_docker_wsl2.sh
```

**Option 2: Docker Desktop (Windows)**
```powershell
# PowerShell als Administrator:
powershell -ExecutionPolicy Bypass -File scripts/setup_docker_windows.ps1
```

📖 **[Komplette Docker + WSL2 Anleitung](DOCKER_WSL2_SETUP.md)** - Detaillierte Schritte für beide Optionen

### Full Stack Starten

```bash
# Nach Docker-Installation:
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Scale agents
docker-compose up -d --scale agent=3
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | FastAPI server |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| Agent | - | Pentest agent |

📖 **[Complete Docker Guide](DOCKER.md)**

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
| [DOCKER.md](DOCKER.md) | Docker deployment guide |
| [GUARDRAILS.md](GUARDRAILS.md) | Security guardrails documentation |
| [GUARDRAILS_INTEGRATION.md](GUARDRAILS_INTEGRATION.md) | Guardrails integration guide |
| [VPN_INTEGRATION.md](VPN_INTEGRATION.md) | VPN setup and usage |
| [DEMO_E2E.md](DEMO_E2E.md) | End-to-end demo documentation |
| [AGENTS.md](AGENTS.md) | Agent development guide |

---

## 🤝 Contributing

We welcome contributions! Please see:
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** - Community standards
- **[CONTRIBUTORS.md](CONTRIBUTORS.md)** - Our amazing contributors

Quick start:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 🌐 Community & Support

Join our growing community!

### Quick Links

| Platform | Link | QR Code |
|----------|------|---------|
| 🎮 **Discord** | [discord.gg/zJZUJwK9AC](https://discord.gg/zJZUJwK9AC) | [📱 Scan](docs/qr_codes/04_discord.png) |
| 💬 **GitHub Discussions** | [SHAdd0WTAka/zen-ai-pentest/discussions](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions) | [📱 Scan](docs/qr_codes/01_github_repo.png) |
| 📦 **PyPI Package** | [pypi.org/project/zen-ai-pentest](https://pypi.org/project/zen-ai-pentest) | [📱 Scan](docs/qr_codes/06_pypi.png) |

### 📱 All QR Codes
View our complete QR code gallery: [docs/qr_codes/index.html](docs/qr_codes/index.html)

### 💬 Discord Server "Zen-Ai"
**Fully configured with 11 channels:**
- 📢 #announcements
- 📜 #rules
- 💬 #general
- 👋 #introductions
- 📚 #knowledge-base
- 🤖 #tools-automation
- 🔒 #security-research
- 🧠 #ai-ml-discussion
- 🐛 #bug-reports
- 💡 #feature-requests
- 🆘 #support

### 📧 Support
- 📖 **[Documentation](docs/)** - Comprehensive guides
- 🐛 **[Issue Tracker](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues)** - Bug reports
- 📧 **[Email](mailto:support@zen-ai-pentest.dev)** - Direct contact

See [SUPPORT.md](SUPPORT.md) for detailed support options.

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

### Core Development Team

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
      <br />
      <sub>Security Architect</sub>
    </td>
    <td align="center">
      <a href="https://www.moonshot.cn/">
        <img src="https://img.shields.io/badge/Kimi-AI-blue?style=for-the-badge&logo=openai&logoColor=white" width="100px;" alt="Kimi AI"/>
        <br />
        <sub><b>Kimi AI</b></sub>
      </a>
      <br />
      <sub>AI Development Partner</sub>
      <br />
      <sub>Architecture & Design</sub>
    </td>
  </tr>
</table>

### AI Contributors

- **Kimi AI (Moonshot AI)** - Primary AI development partner
  - Led architecture design for autonomous agent loop
  - Implemented Risk Engine with false-positive reduction
  - Created CI/CD integration templates
  - Developed benchmarking framework
  - Co-authored documentation and roadmaps

### Special Thanks

- **Grok (xAI)** - Strategic analysis and competitive research
- **GitHub Copilot** - Code assistance and suggestions
- **Security Community** - Feedback, bug reports, and feature requests

---

## 🎨 Project Artwork

<div align="center">
  <img src="docs/qr_codes/hemisphere_sync.png" alt="Hemisphere Sync" width="600"/>

  ### Hemisphere Sync

  ```
        🧠 GEHIRN
       ╱        ╲
      ╱  LINKS   ╲    ╱  RECHTS   ╲
     ╱  (Kimi)    ╲  ╱(Observer^^)╲
    ╱   Logik      ╲╱  Kreativität ╲
       Analytisch   ╳  Ganzheitlich
       Struktur     ╳     Vision
            ╲      ╱╲    ╱
             ╲    ╱  ╲  ╱
              ╲  ╱    ╲╱
               ╲╱    ╱
                ╲   ╱
                 ╲ ╱
                  ❤️
          HEMISPHERE_SYNC
     "Zwei Hälften - Ein Herz - Ein Team"
  ```

  *A fusion of human vision and AI capability*

  **Left Brain (Kimi - Logik) + Right Brain (Observer^^ - Kreativität) = Hemisphere_Sync**

  | Hemisphere | Zuständig für | Team |
  |------------|---------------|------|
  | **Left Brain** | Logik, Struktur, Code, Analytik | **Kimi** 🤖 |
  | **Right Brain** | Kreativität, Vision, Design, Emotion | **Observer^^** 🎨 |

  *Custom artwork by **SHAdd0WTAka** representing the fusion of human vision and AI capability.*
</div>

---

<p align="center">
  <b>Made with ❤️ for the security community</b><br>
  <sub>© 2026 Zen-AI-Pentest. All rights reserved.</sub>
</p>
