# Zen-AI-Pentest

> 🛡️ **Professional AI-Powered Penetration Testing Framework**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](docker/)

**Zen-AI-Pentest** is an autonomous, AI-powered penetration testing framework that combines cutting-edge language models with professional security tools. Built for security professionals, bug bounty hunters, and enterprise security teams.

---

## ✨ Features

### 🤖 Autonomous AI Agent
- **ReAct Pattern**: Reason → Act → Observe → Reflect
- **LangGraph Integration**: Stateful agent loops with memory
- **Tool Calling**: Automatic selection and execution of 20+ pentesting tools
- **Human-in-the-Loop**: Pause for critical decisions

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
│                         ZEN-AI-PENTEST v2.0                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      FRONTEND LAYER                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │   React      │  │  WebSocket   │  │   CLI Interface      │  │    │
│  │  │  Dashboard   │  │   Client     │  │                      │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      API LAYER (FastAPI)                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │   Auth       │  │    Scans     │  │     Reports          │  │    │
│  │  │   (JWT)      │  │   CRUD API   │  │   Generator API      │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    CORE LAYER                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │  ReAct Agent │  │  Tool Exec   │  │  VM Orchestrator     │  │    │
│  │  │  (LangGraph) │  │   Engine     │  │  (VBox/Cloud)        │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    TOOLS LAYER (20+)                             │    │
│  │  Network: Nmap | Masscan | Scapy | Tshark                       │    │
│  │  Web: BurpSuite | SQLMap | Gobuster | ZAP                       │    │
│  │  Exploit: Metasploit | SearchSploit                             │    │
│  │  AD: BloodHound | CrackMapExec | Responder                      │    │
│  │  Wireless: Aircrack-ng                                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    DATA LAYER                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │  PostgreSQL  │  │    Redis     │  │   Report Storage     │  │    │
│  │  │   (Main DB)  │  │   (Cache)    │  │   (PDF/HTML/JSON)    │  │    │
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

## 📞 Support

- GitHub Issues: [Report Bug](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues)
- Discussions: [Ask Question](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions)
- Email: support@zen-pentest.local

---

<p align="center">
  <b>Made with ❤️ for the security community</b><br>
  <sub>© 2026 Zen-AI-Pentest. All rights reserved.</sub>
</p>
