# Zen AI Pentest Documentation

Welcome to the Zen AI Pentest documentation! This guide will help you get started, deploy, and use the framework effectively.

---

## 📚 Documentation Index

### Getting Started
- **[Installation Guide](INSTALLATION.md)** - Complete installation instructions
  - Docker setup (recommended)
  - Local installation
  - Production deployment
  - VirtualBox VM setup

### API Reference
- **[API Documentation](API.md)** - Complete REST API reference
  - Authentication
  - Endpoints reference
  - Response codes
  - Rate limiting
- **[API Examples](API_EXAMPLES.md)** - Code examples in multiple languages
  - curl examples
  - Python requests examples
  - JavaScript fetch examples
  - WebSocket examples

### Deployment
- **[AWS Deployment](deployment/aws-deployment.md)** - Deploy on Amazon Web Services
  - EC2 setup, RDS PostgreSQL, EKS, S3
- **[Azure Deployment](deployment/azure-deployment.md)** - Deploy on Microsoft Azure
  - VMs, PostgreSQL, AKS, Blob Storage
- **[GCP Deployment](deployment/gcp-deployment.md)** - Deploy on Google Cloud Platform
  - Compute Engine, Cloud SQL, GKE, Cloud Armor

### Architecture & Design
- **[Architecture Overview](architecture.md)** - System architecture and design
  - Component details
  - Data flow
  - Security architecture
  - Technology stack

### Troubleshooting
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
  - Database connection issues
  - API startup errors
  - Docker problems
  - Performance tuning

### Additional Guides
- **[Docker Setup](DOCKER_SETUP.md)** - Detailed Docker configuration
- **[Plugin System](PLUGIN_SYSTEM.md)** - Extending with custom tools
- **[Benchmarks](BENCHMARKS.md)** - Performance comparisons
- **[Production Hardening](production-hardening.md)** - Security best practices

---

## 🚀 Quick Start

### Installation

```bash
# From PyPI (recommended)
pip install zen-ai-pentest

# From source
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest
pip install -e ".[dev]"
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# Access services
# Web UI:      http://localhost:3000
# API Docs:    http://localhost:8000/docs
# API Base:    http://localhost:8000
```

---

## 🏗️ Architecture Overview

```
zen-ai-pentest/
├── autonomous/          # ReAct loop, tools, memory
├── risk_engine/         # CVSS, EPSS, business impact
├── web_ui/              # FastAPI backend + React frontend
├── ci_cd/               # CI/CD integrations
├── core/                # Orchestrator, models
├── agents/              # LLM agents
└── modules/             # Pentest modules
```

---

## ✨ Key Features

### 1. Autonomous Pentesting
- **ReAct Loop**: Reasoning + Acting with self-correction
- **Tool Executor**: 15+ security tools with safety controls
- **Memory System**: Multi-layer persistent storage

### 2. Risk Scoring
- **Multi-Factor Formula**: CVSS×0.25 + EPSS×0.25 + Business×0.35 + Validation×0.15
- **Severity Levels**: Critical (24h), High (72h), Medium (14d), Low (30d)
- **Context-Aware**: Internet exposure, data sensitivity, compliance

### 3. DevSecOps Integration
- **Web UI**: Real-time scan monitoring
- **CI/CD**: GitHub Actions, GitLab CI, Jenkins, Kubernetes
- **API**: RESTful API with WebSocket updates

### 4. Multi-Cloud Support
- **AWS**: EC2, RDS, EKS, S3 deployment
- **Azure**: VMs, PostgreSQL, AKS deployment
- **GCP**: Compute Engine, Cloud SQL, GKE deployment

---

## 💻 Usage Examples

### Autonomous Agent

```python
from autonomous.react import ReActLoop, AgentConfig

config = AgentConfig(max_iterations=30, safety_level="non_destructive")
agent = ReActLoop(llm_client=client, config=config)
result = await agent.run(
    goal="Find SQL injection vulnerabilities",
    target="example.com"
)
```

### Risk Scoring

```python
from risk_engine import RiskScorer

scorer = RiskScorer()
score = scorer.calculate(
    finding={"cvss": 9.8, "epss": 0.95, "cve_id": "CVE-2021-44228"},
    target_context={"internet_facing": True, "data_sensitivity": "pii"}
)
print(f"Risk: {score.value} ({score.severity.name})")
```

### Tool Execution

```python
from autonomous.tool_executor import ToolExecutor, SafetyLevel

executor = ToolExecutor(safety_level=SafetyLevel.NON_DESTRUCTIVE)
result = await executor.execute("nmap", "example.com", {"ports": "80,443"})
```

### REST API

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=admin123"

# Create scan
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"target": "example.com", "scan_type": "full"}'
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/autonomous/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
MISTRAL_API_KEY=...

# Safety
ZEN_SAFETY_LEVEL=non_destructive  # read_only, non_destructive, exploit, aggressive
ZEN_MAX_ITERATIONS=50

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/zen_pentest

# Paths
ZEN_DATA_DIR=./data
ZEN_LOG_DIR=./logs
```

### Safety Levels

| Level | Description | Tools Allowed |
|-------|-------------|---------------|
| READ_ONLY | Passive reconnaissance only | nmap, amass, subfinder |
| NON_DESTRUCTIVE | Active scanning without exploitation | nuclei, nikto, gobuster |
| EXPLOIT | Controlled exploitation | sqlmap, metasploit (limited) |
| AGGRESSIVE | Full exploitation | All tools (requires explicit approval) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

---

## 💬 Support

| Resource | Link |
|----------|------|
| 🐛 Issues | [GitHub Issues](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues) |
| 💬 Discussions | [GitHub Discussions](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions) |
| 🌐 Discord | [Discord Community](https://discord.gg/zen-ai-pentest) |
| 📧 Email | [support@zen-ai-pentest.dev](mailto:support@zen-ai-pentest.dev) |
| 🔧 Troubleshooting | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| 📚 Full Docs | [docs/](.) |

---

## 🗺️ Roadmap

See [ROADMAP_2026.md](../ROADMAP_2026.md) for our detailed 2026 roadmap.

Highlights:
- **Q1 2026**: Autonomous Engine ✅
- **Q2 2026**: Risk Framework ✅
- **Q3 2026**: DevSecOps Integration ✅
- **Q4 2026**: Community & Benchmarks

---

<p align="center">
  <b>Zen AI Pentest - AI-Powered Penetration Testing</b><br>
  <sub>© 2026 Zen AI Pentest. All rights reserved.</sub>
</p>
