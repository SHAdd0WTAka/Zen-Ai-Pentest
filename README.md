# Zen-AI-Pentest

> 🛡️ **Professional AI-Powered Penetration Testing Framework**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
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

## 🚀 Quick Start

> ⚠️ **Wichtig:** Jeder Benutzer muss seine eigenen API Keys konfigurieren!
> Siehe [README_USER_SETUP.md](README_USER_SETUP.md) für Details.

[![Version](https://img.shields.io/badge/Version-2.3.9-orange)](https://github.com/SHAdd0WTAka/zen-ai-pentest/releases)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

[![PyPI](https://img.shields.io/pypi/v/zen-ai-pentest?color=green)](https://pypi.org/project/zen-ai-pentest/)
[![Marketplace](https://img.shields.io/badge/Marketplace-Action-green?logo=github)](https://github.com/marketplace/actions/zen-ai-pentest)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](docker/)
[![Tests](https://img.shields.io/badge/Tests-pytest-brightgreen)](tests/)

[![CI Status](https://img.shields.io/badge/CI-Optimized-brightgreen)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions/workflows/ci.yml)
[![Security](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions/workflows/security.yml/badge.svg)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions/workflows/security.yml)
[![PyPI](https://img.shields.io/pypi/v/zen-ai-pentest?label=PyPI&color=green)](https://pypi.org/project/zen-ai-pentest/)
[![Deployment Status](https://img.shields.io/github/deployments/SHAdd0WTAka/Zen-Ai-Pentest/pypi?label=Deployment)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/deployments)

[![Authors](https://img.shields.io/badge/Authors-SHAdd0WTAka%20%7C%20KimiAI-purple)](#-authors--team)
[![Roadmap](https://img.shields.io/badge/Roadmap-2026-blueviolet)](ROADMAP_2026.md)
[![Architecture](https://img.shields.io/badge/Architecture-Diagram-blue)](docs/ARCHITECTURE.md)

## 🚀 Security Status

[![CodeQL](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/security/code-scanning)
[![Security Score](https://img.shields.io/badge/Security%20Score-100%2F100-brightgreen)](docs/production-hardening.md)
[![Dependencies](https://img.shields.io/badge/dependencies-0%20vulnerabilities-brightgreen)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/security/dependabot)
[![Health Score](https://img.shields.io/badge/Health%20Score-84%2F100-blue)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions)
[![Issues](https://img.shields.io/badge/Issues-0%20open-brightgreen)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues)
[![codecov](https://codecov.io/gh/SHAdd0WTAka/zen-ai-pentest/branch/main/graph/badge.svg)](https://codecov.io/gh/SHAdd0WTAka/zen-ai-pentest)

---

## 📚 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [Support](#-support)
- [License](#-license)

---

## 🎯 Overview

**Zen-AI-Pentest** is an autonomous, AI-powered penetration testing framework that combines cutting-edge language models with professional security tools. Built for security professionals, bug bounty hunters, and enterprise security teams.

```mermaid
  graph TB
      subgraph "User Interface"
          CLI[CLI]
          API[REST API]
          WebUI[Web UI]
      end

      subgraph "Core Engine"
          Orchestrator[Agent Orchestrator]
          StateMachine[State Machine]
          RiskEngine[Risk Engine]
      end

      subgraph "AI Agents"
          Recon[Reconnaissance]
          Vuln[Vulnerability]
          Exploit[Exploit]
          Report[Report]
      end

      subgraph "Tools"
          Nmap[Nmap]
          SQLMap[SQLMap]
          Metasploit[Metasploit]
      end

      subgraph "External APIs"
          OpenAI[OpenAI]
          Anthropic[Anthropic]
          ThreatIntel[Threat Intelligence]
      end

      CLI --> API
      WebUI --> API
      API --> Orchestrator
      Orchestrator --> StateMachine
      StateMachine --> Recon
      StateMachine --> Vuln
      StateMachine --> Exploit
      Exploit --> OpenAI
      RiskEngine --> ThreatIntel
```

### Key Highlights

- 🤖 **AI-Powered**: Leverages state-of-the-art LLMs for intelligent decision making
- 🔒 **Security-First**: Multiple safety controls and validation layers
- 🚀 **Production-Ready**: Enterprise-grade with CI/CD, monitoring, and support
- 📊 **Comprehensive**: 20+ integrated security tools
- 🔧 **Extensible**: Plugin system for custom tools and integrations

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

### 🛠️ 20+ Integrated Tools
| Category | Tools |
|----------|-------|
| **Network** | Nmap, Masscan, Scapy, Tshark |
| **Web** | BurpSuite, SQLMap, Gobuster, OWASP ZAP |
| **Exploitation** | Metasploit Framework |
| **Brute Force** | Hydra, Hashcat |
| **Reconnaissance** | Amass, Nuclei, TheHarvester |
| **Active Directory** | BloodHound, CrackMapExec, Responder |
| **Wireless** | Aircrack-ng Suite |

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

# Configure your API keys (each user must do this!)
python scripts/setup_wizard.py -b kimi -m kimi-k2.5 -k "your-api-key"
# Or interactive: python scripts/setup_wizard.py

# Verify configuration
python scripts/check_config.py

# Initialize database
python database/models.py

# Start API server
python api/main.py
```

### Option 3: VirtualBox VM Setup

```bash
# Automated Kali Linux setup
python scripts/setup_vms.py --kali

# Manual setup
# See docs/setup/VIRTUALBOX_SETUP.md
```

---

## 🤖 AI Assistant (Kimi Helper)

Zen-AI-Pentest includes a built-in AI assistant with specialized personas for different pentesting phases:

```bash
# One-shot queries
python tools/kimi_helper.py -p recon "Analyze example.com for subdomains"
python tools/kimi_helper.py -p exploit "Write SQLi scanner for login forms"
python tools/kimi_helper.py -p report "Generate CVSS report for XSS bug"
python tools/kimi_helper.py -p audit "Review this code for vulnerabilities"

# Interactive mode with context
python tools/kimi_helper.py -i
# Commands: /recon, /exploit, /report, /audit, /clear, /exit

# Switch between AI backends
python scripts/switch_model.py --list
python scripts/switch_model.py -b openai -m gpt-4o
```

**Available Personas:**
- **recon**: OSINT specialist for reconnaissance
- **exploit**: Python exploit developer
- **report**: Technical writer for pentest reports
- **audit**: Security code reviewer

See [KIMI_PERSONAS.md](docs/KIMI_PERSONAS.md) for details.

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
  -d '{
    "name":"Network Scan",
    "target":"192.168.1.0/24",
    "scan_type":"network",
    "config":{"ports":"top-1000"}
  }'

# Execute tool
curl -X POST http://localhost:8000/tools/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "tool_name":"nmap_scan",
    "target":"scanme.nmap.org",
    "parameters":{"ports":"22,80,443"}
  }'

# Generate report
curl -X POST http://localhost:8000/reports \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "scan_id":1,
    "format":"pdf",
    "template":"default"
  }'
```

### WebSocket (Real-Time)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scans/1');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Scan update:', data);
};
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ZEN-AI-PENTEST v2.2 - System Architecture             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    FRONTEND LAYER                                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │   React      │  │  WebSocket   │  │   CLI Interface      │  │    │
│  │  │  Dashboard   │  │   Client     │  │   (Rich/Typer)       │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      API LAYER (FastAPI)                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │   Auth       │  │    Scans     │  │   Integrations       │  │    │
│  │  │   (JWT)      │  │   CRUD API   │  │   (GitHub/Slack)     │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    AUTONOMOUS LAYER                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │   ReAct      │  │   Memory     │  │   Exploit Validator  │  │    │
│  │  │   Loop       │  │   System     │  │   (Sandboxed)        │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    RISK ENGINE LAYER                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │   False      │  │   Business   │  │   CVSS/EPSS          │  │    │
│  │  │   Positive   │  │   Impact     │  │   Scoring            │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    TOOLS LAYER (20+)                             │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │ Network: Nmap | Masscan | Scapy | Tshark                │   │    │
│  │  │ Web: BurpSuite | SQLMap | Gobuster | Nuclei | ZAP       │   │    │
│  │  │ Exploit: Metasploit | SearchSploit | ExploitDB          │   │    │
│  │  │ AD: BloodHound | CrackMapExec | Responder               │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    DATA & REPORTING LAYER                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │  PostgreSQL  │  │ Benchmarks   │  │   Report Generator   │  │    │
│  │  │   (Main DB)  │  │ & Metrics    │  │   (PDF/HTML/JSON)    │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
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
├── api/                        # FastAPI Backend
│   ├── main.py                # API Server
│   ├── schemas.py             # Pydantic Models
│   ├── auth.py                # JWT Authentication
│   └── websocket.py           # WebSocket Manager
├── agents/                     # AI Agents
│   ├── react_agent.py         # ReAct Agent
│   └── react_agent_vm.py      # VM-based Agent
├── autonomous/                 # Autonomous Agent System
│   ├── agent_loop.py          # ReAct Loop Engine
│   ├── exploit_validator.py   # Exploit Validation
│   ├── memory.py              # Memory Management
│   └── tool_executor.py       # Tool Execution
├── risk_engine/               # Risk Analysis
│   ├── false_positive_engine.py
│   ├── business_impact_calculator.py
│   ├── cvss.py
│   └── epss.py
├── benchmarks/                # Benchmark Framework
│   ├── run_benchmarks.py
│   └── comparison.py
├── integrations/              # CI/CD Integrations
│   ├── github.py
│   ├── gitlab.py
│   ├── jira.py
│   ├── slack.py
│   └── jenkins.py
├── database/                   # Database Layer
│   └── models.py              # SQLAlchemy Models
├── tools/                      # Pentesting Tools
│   ├── nmap_integration.py
│   ├── sqlmap_integration.py
│   ├── metasploit_integration.py
│   └── ... (20+ tools)
├── gui/                        # Web Interface
│   └── vm_manager_gui.py      # React Dashboard
├── reports/                    # Report Generation
│   └── generator.py           # PDF/HTML/JSON
├── notifications/              # Alerts
│   ├── slack.py
│   └── email.py
├── docker/                     # Deployment
│   ├── Dockerfile
│   └── docker-compose.full.yml
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── INSTALLATION.md
│   ├── API.md
│   └── setup/
├── tests/                      # Test Suite
└── scripts/                    # Setup Scripts
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
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

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

## 📚 Documentation

- **[Getting Started](docs/tutorials/getting-started.md)** - First steps
- **[Installation Guide](docs/INSTALLATION.md)** - Setup instructions
- **[API Documentation](docs/API.md)** - REST API reference
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Support](SUPPORT.md)** - Help and support

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

## 💬 Support

Need help? We've got you covered:

- 📖 **[Documentation](docs/)** - Comprehensive guides
- 💬 **[GitHub Discussions](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions)** - Community Q&A
- 🐛 **[Issue Tracker](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues)** - Bug reports
- 🌐 **[Discord](https://discord.gg/zen-ai-pentest)** - Real-time chat
- 📧 **[Email Support](mailto:support@zen-ai-pentest.dev)** - Direct contact

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

## 🗺️ Roadmap

See [ROADMAP_2026.md](ROADMAP_2026.md) for our detailed 2026 roadmap.

Highlights:
- **Q1 2026**: SIEM integrations, React Dashboard
- **Q2 2026**: Mobile app, quantum-resistant crypto
- **Q3 2026**: Multi-cloud native, serverless support
- **Q4 2026**: Autonomous SOC capabilities

---

<p align="center">
  <b>Made with ❤️ for the security community</b><br>
  <sub>© 2026 Zen-AI-Pentest. All rights reserved.</sub>
</p>
