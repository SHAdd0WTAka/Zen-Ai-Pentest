# Zen-AI-Pentest 🤖🔒

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Size](https://img.shields.io/badge/code%20size-21k%2B%20lines-success)](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest)

> **Autonomous AI-powered penetration testing framework with real-time dashboard, automated scheduling, and enterprise-grade security.**

![Architecture](docs/assets/architecture-diagram.png)

## 🌟 Key Features

### 🤖 AI-Powered Analysis
- **Analysis Bot** with 4,281 lines of intelligent vulnerability analysis
- CVSS/EPSS risk scoring
- Automated exploitability assessment
- Remediation recommendations

### 🛡️ Enterprise Security
- **Secure Validator**: CVSS 7.5 → 2.0 reduction
- ISO 27001 compliant audit logging
- Tamper-proof log integrity
- Input validation (SSRF, SQLi, XSS prevention)

### ⚡ Real-Time Dashboard
- WebSocket-based live updates
- Task progress tracking
- System metrics monitoring
- Security alert notifications

### ⏰ Automated Scheduling
- Cron-based job scheduling
- Recurring vulnerability scans
- Automatic report generation
- Missed job recovery

### 🚀 Performance Optimized
- Multi-layer caching
- Connection pooling
- Async processing
- Circuit breaker pattern

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ZEN-AI-PENTEST v2.4                       │
│                    21,672+ Lines of Code                     │
├─────────────────────────────────────────────────────────────┤
│  Modules:                                                    │
│  • Analysis Bot .................... 4,281 LOC (21%)        │
│  • ZenOrchestrator ................. 3,441 LOC (17%)        │
│  • Audit Logger .................... 2,677 LOC (13%)        │
│  • Task Scheduler .................. 2,218 LOC (11%)        │
│  • Live Dashboard .................. 1,829 LOC (9%)         │
│  • Performance Opt. ................ 1,419 LOC (7%)         │
│  • App Integration ................. 1,126 LOC (6%)         │
│  • Tool Integrations ............... 1,556 LOC (8%)         │
│  • Secure Validator .................. 550 LOC (3%)         │
│  • Test Suite ...................... 2,500+ LOC (5%)        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Nmap (for scanning)
- SQLMap (for SQL injection testing)
- Optional: Nuclei, GoBuster, Subfinder

### Installation

```bash
# Clone repository
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Install Python dependencies
pip install -r requirements.txt

# Install pentest tools (Linux/macOS)
bash scripts/install-tools.sh --all

# Or Windows (PowerShell as Admin)
.\scripts\install-tools.ps1 -All
```

### Start the Server

```bash
# Development
python -m uvicorn api.main:app --reload

# Production
docker-compose up -d
```

### Access

- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Dashboard**: WebSocket at `ws://localhost:8000/api/v1/dashboard/ws`

## 📡 API Usage

### Submit a Scan

```bash
curl -X POST http://localhost:8000/api/v1/orchestrator/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "vulnerability_scan",
    "target": "example.com",
    "options": {"ports": "80,443"},
    "priority": "high"
  }'
```

### Schedule Recurring Scan

```bash
curl -X POST http://localhost:8000/api/v1/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Security Scan",
    "task_type": "vulnerability_scan",
    "task_data": {"target": "production.example.com"},
    "cron": "0 2 * * *"
  }'
```

### Check Tool Status

```bash
curl http://localhost:8000/system/tools/status
```

## 🧪 Testing

```bash
# Run all tests
python tests/run_tests.py --all

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Quick integration test
python quick_test.py
```

## 🏗️ Architecture

### Component Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Web UI     │     │     CLI      │     │   API Client │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │ HTTP/WebSocket
┌───────────────────────────▼───────────────────────────┐
│                  FastAPI Application                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │
│  │ REST API    │ │  WebSocket  │ │  Authentication │  │
│  └─────────────┘ └─────────────┘ └─────────────────┘  │
└───────────────────────────┬───────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────┐
│                   Core Services                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │Orchestrator  │  │  Scheduler   │  │   Dashboard  ││
│  │  (3,441 LOC) │  │  (2,218 LOC) │  │  (1,829 LOC) ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │Audit Logger  │  │Analysis Bot  │  │   Security   ││
│  │  (2,677 LOC) │  │  (4,281 LOC) │  │   Validator  ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
└───────────────────────────────────────────────────────┘
```

## 📦 Modules

| Module | Description | LOC |
|--------|-------------|-----|
| `analysis_bot/` | AI vulnerability analysis | 4,281 |
| `orchestrator/` | Central coordination | 3,441 |
| `audit/` | Audit logging & compliance | 2,677 |
| `scheduler/` | Job scheduling | 2,218 |
| `dashboard/` | Real-time dashboard | 1,829 |
| `performance/` | Caching & optimization | 1,419 |
| `app/` | Application factory | 1,126 |
| `tools/integrations/` | Pentest tool wrappers | 1,556 |
| `core/` | Security utilities | 550 |
| `tests/` | Test suite | 2,500+ |

## 🔒 Security Features

- ✅ **Input Validation**: SSRF, SQLi, Command Injection prevention
- ✅ **Audit Logging**: ISO 27001 compliant with cryptographic signatures
- ✅ **Log Integrity**: Chain of custody verification
- ✅ **Rate Limiting**: API protection
- ✅ **Circuit Breaker**: Fault tolerance

## 🚢 Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/zenpentest

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design & components
- [API Guide](docs/API_GUIDE.md) - Complete API reference
- [Deployment](docs/DEPLOYMENT.md) - Installation & configuration
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Build details

## 🛠️ Pentest Tools Integrated

**Required:**
- ✅ Nmap - Port scanning
- ✅ SQLMap - SQL injection testing

**Optional:**
- ✅ Nuclei - Vulnerability scanning
- ✅ GoBuster - Directory enumeration
- ✅ Subfinder - Subdomain discovery
- ✅ Amass - DNS enumeration
- ✅ FFUF - Web fuzzing
- ✅ Nikto - Web server scanner
- ✅ WhatWeb - Web fingerprinting
- ✅ WAFW00F - WAF detection

## 📈 Performance

- **Concurrent Tasks**: Up to 50 (configurable)
- **WebSocket Connections**: 100+ simultaneous
- **Cache Hit Rate**: >90% with proper tuning
- **API Response Time**: <100ms average

## 🎯 Use Cases

- **Bug Bounty Hunting**: Automated reconnaissance & scanning
- **Enterprise Security**: Scheduled compliance scans
- **DevSecOps**: CI/CD integration
- **Security Audits**: Comprehensive vulnerability assessment

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- Analysis Bot based on 100-agent research
- Security patterns from industry best practices
- Built with FastAPI, SQLAlchemy, and modern Python

## 📞 Support

- Documentation: https://docs.zenpentest.example.com
- Issues: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues
- Discussions: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/discussions

---

<p align="center">
  <b>Built with ❤️ and ☕ in a 14-day intensive development session</b><br>
  <b>21,672+ lines of production-ready code</b>
</p>
