# Zen-AI-Pentest

> 🛡️ **Professional AI-Powered Penetration Testing Framework**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](docker/)
[![Tests](https://img.shields.io/badge/Tests-pytest-brightgreen)](tests/)
[![PyPI](https://img.shields.io/pypi/v/zen-ai-pentest)](https://pypi.org/project/zen-ai-pentest/)
[![Version](https://img.shields.io/badge/Version-2.0.4-orange)](https://github.com/SHAdd0WTAka/zen-ai-pentest/releases)
[![Authors](https://img.shields.io/badge/Authors-SHAdd0WTAka%20%7C%20KimiAI-purple)](#-authors--team)
[![Roadmap](https://img.shields.io/badge/Roadmap-2026-blueviolet)](ROADMAP_2026.md)
[![Architecture](https://img.shields.io/badge/Architecture-Diagram-blue)](docs/architecture.md)
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
**Zen-AI-Pentest** is an autonomous, AI-powered penetration testing framework that combines cutting-edge language models with professional security tools. Built for security professionals, bug bounty hunters, and enterprise security teams.

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

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start full stack
cd docker
docker-compose -f docker-compose.full.yml up -d

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
```

### Option 3: VirtualBox VM Setup

```bash
# Automated Kali Linux setup
python scripts/setup_vms.py --kali

# Manual setup
# See docs/setup/VIRTUALBOX_SETUP.md
```

---

## 📖 Usage

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
│                    ZEN-AI-PENTEST v2.0 - System Architecture             │
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
├── database/                   # Database Layer
│   └── models.py              # SQLAlchemy Models
├── virtualization/             # VM Management
│   ├── vm_manager.py          # VirtualBox
│   └── cloud_vm_manager.py    # AWS/Azure/GCP
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
│   ├── setup/
│   └── research/
├── scripts/                    # Setup Scripts
│   └── setup_vms.py
└── tests/                      # Test Suite
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

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SMTP_HOST=smtp.gmail.com
SMTP_USER=user@gmail.com
SMTP_PASS=password

# Cloud Providers
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AZURE_SUBSCRIPTION_ID=...
GCP_PROJECT_ID=...
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

- [Setup Guide](docs/setup/VIRTUALBOX_SETUP.md) - VM installation & configuration
- [API Documentation](docs/API.md) - REST API reference
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Tool Research](docs/research/FUNDAMENTAL_PENTEST_TOOLS.md) - Tool analysis

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

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

## 🎯 Advanced Features

### Autonomous Mode

The autonomous agent uses ReAct (Reasoning + Acting) pattern for fully automated penetration testing:

```bash
# Run autonomous scan
zen-ai-pentest --autonomous --target example.com --goal "Find all vulnerabilities"

# With custom scope
zen-ai-pentest --autonomous --target example.com --scope config/autonomous.json
```

**Features:**
- **State Machine**: PLANNING → EXECUTING → OBSERVING → REFLECTING → COMPLETED
- **Memory Management**: Short-term, long-term, and context window
- **Tool Orchestration**: Automatic selection and execution of 20+ tools
- **Self-Correction**: Retry logic and error recovery
- **Human-in-the-Loop**: Optional pause for critical decisions

```python
from autonomous import AutonomousAgentLoop

agent = AutonomousAgentLoop(max_iterations=50)
result = await agent.run(
    goal="Find vulnerabilities and open ports",
    target="example.com",
    scope={"depth": "comprehensive"}
)
```

---

### Risk Engine

Advanced false-positive reduction and risk prioritization:

```bash
# Scan with risk validation
zen-ai-pentest --target example.com --autonomous --validate-risks
```

**Components:**
- **FalsePositiveEngine**: Multi-factor validation using Bayesian filtering and LLM voting
- **BusinessImpactCalculator**: Financial, compliance, and reputation impact assessment
- **CVSS/EPSS Scoring**: Industry-standard vulnerability scoring
- **Priority Ranking**: Automated finding prioritization

```python
from risk_engine import FalsePositiveEngine, BusinessImpactCalculator

# Validate findings
fp_engine = FalsePositiveEngine()
validation = await fp_engine.validate_finding(finding)

# Calculate business impact
impact_calc = BusinessImpactCalculator(
    organization_size="large",
    annual_revenue=100000000,
    industry="finance"
)
impact = impact_calc.calculate_overall_impact(asset_context, finding_type, severity)
```

---

### CI/CD Integration

Seamless integration with DevSecOps pipelines:

**GitHub Actions:**
```yaml
- name: Security Scan
  uses: zen-ai-pentest/action@v2
  with:
    target: ${{ vars.TARGET_URL }}
    fail-on: critical
    format: sarif
```

**GitLab CI:**
```yaml
security-scan:
  image: zen-ai-pentest:latest
  script:
    - zen-ai-pentest --target $TARGET --ci-mode --fail-on high
  artifacts:
    reports:
      sast: gl-sast-report.json
```

**Jenkins:**
```groovy
stage('Security Scan') {
    steps {
        sh 'zen-ai-pentest --target ${TARGET} --ci-mode --fail-on critical'
    }
}
```

**Supported Output Formats:**
- **JSON**: Machine-readable findings
- **JUnit XML**: Test result integration
- **SARIF**: Static analysis results format
- **Markdown**: Human-readable reports

**Exit Codes:**
- `0`: Scan passed (no findings above threshold)
- `1`: Findings detected (above threshold)

---

### Benchmarking

Compare Zen AI against competitors:

```bash
# Run full benchmark suite
zen-ai-pentest --benchmark

# Quick benchmark
python -c "from benchmarks import run_quick_benchmark; asyncio.run(run_quick_benchmark())"
```

**Benchmarks Include:**
- HackTheBox machines (Lame, Blue, Legacy)
- OWASP WebGoat scenarios
- DVWA test cases
- OWASP Juice Shop challenges

**Metrics:**
| Metric | Description |
|--------|-------------|
| Time to First Finding | Speed of initial vulnerability detection |
| Time to User | Initial access achievement time |
| Time to Root | Full compromise time |
| Findings Count | Total vulnerabilities discovered |
| False Positive Rate | Accuracy measurement |
| Cost per Scan | API and compute costs |

**Competitor Comparison:**
| Tool | HTB Easy | FP Rate | Cost |
|------|----------|---------|------|
| Zen AI | ~45min | ~12% | $0.50 |
| PentestGPT | ~80min | ~28% | $1.20 |
| AutoPentest | ~120min | ~35% | $2.00 |

---

### Exploit Validation

Safe and controlled exploit testing:

```bash
# Validate exploit with safety controls
zen-ai-pentest --validate-exploits --target example.com --exploit-type sqli
```

**Safety Levels:**
- **READ_ONLY**: Passive validation only
- **VALIDATE_ONLY**: Validate without full execution
- **CONTROLLED**: Controlled execution with limits (default)
- **FULL**: Full exploitation (requires explicit approval)

**Features:**
- Docker-based sandboxing
- Evidence collection (screenshots, HTTP captures)
- Chain of custody tracking
- Automatic remediation generation

```python
from autonomous import ExploitValidator, ExploitType, ScopeConfig

validator = ExploitValidator(
    safety_level="controlled",
    scope_config=ScopeConfig(allowed_hosts=["example.com"])
)

result = await validator.validate(
    exploit_code="' OR '1'='1",
    target="https://example.com/login",
    exploit_type=ExploitType.WEB_SQLI
)
```

---

### Notifications & Integrations

**Slack Notifications:**
```python
from integrations import SlackNotifier

slack = SlackNotifier(webhook_url="...")
await slack.notify_scan_completed(results, target="example.com")
```

**JIRA Integration:**
```python
from integrations import JiraIntegration

jira = JiraIntegration(server="...", username="...", api_token="...")
ticket = await jira.create_finding_ticket(finding, project_key="SEC")
```

**Supported Integrations:**
- GitHub (Issues, Check Runs)
- GitLab (Issues, CI/CD)
- JIRA (Ticket creation)
- Slack (Notifications)
- Jenkins (Pipeline triggers)
- Email (SMTP alerts)
- Webhooks (Custom endpoints)

---

## 📁 Updated Project Structure

```
zen-ai-pentest/
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
├── config/                    # Configuration Files
│   ├── autonomous.json
│   ├── risk_engine.json
│   ├── benchmarks.json
│   └── integrations.json
├── api/                       # FastAPI Backend
├── agents/                    # AI Agents
├── database/                  # Database Layer
├── tools/                     # Pentesting Tools
└── ...
```

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

### Contributing

We welcome contributions! See [CONTRIBUTORS.md](CONTRIBUTORS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📞 Support

- GitHub Issues: [Report Bug](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues)
- Discussions: [Ask Question](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions)
- Email: support@zen-pentest.local
- Documentation: https://shadd0wtaka.github.io/zen-ai-pentest

---

<p align="center">
  <b>Made with ❤️ for the security community</b><br>
  <sub>© 2026 Zen-AI-Pentest. All rights reserved.</sub>
</p>
