# Zen AI Pentest v2.0.0 Release Notes

## 🎉 Major Release - 2026 Roadmap Complete

### Release Date: 2026-01-31

---

## 📦 PyPI Package

```bash
pip install zen-ai-pentest==2.0.0
```

**Package**: `zen_ai_pentest-2.0.0-py3-none-any.whl`
**Size**: ~155 KB
**Python**: 3.9+

---

## 🐳 Docker Image

```bash
# Pull from Docker Hub (when available)
docker pull shadd0wtaka/zen-ai-pentest:2.0.0

# Or build locally
docker build -t zen-ai-pentest:2.0.0 .
docker run -p 8000:8000 zen-ai-pentest:2.0.0
```

---

## ✨ New Features

### Q1: Autonomous Pentesting Engine
- **ReAct Loop** with self-correction capabilities
- **Tool Executor** supporting 15+ security tools
- **Multi-layer Memory System** (short-term, long-term, semantic, episodic)
- **Safety Controls** with 4 safety levels

### Q2: Low False-Positive Framework
- **Risk Scoring Engine** with multi-factor formula
- **CVSS 3.1 Calculator**
- **EPSS Integration** (exploit probability)
- **Business Impact Assessment**
- **Severity-based SLAs** (24h/72h/14d/30d)

### Q3: DevSecOps Integration
- **FastAPI Backend** with WebSocket support
- **React Frontend** with real-time updates
- **CI/CD Integrations** (GitHub, GitLab, Jenkins, K8s)
- **REST API** with automatic documentation

### Q4: Community & Benchmarks
- **Benchmark Framework** (OWASP, WrongSecrets, DVWA, WebGoat)
- **Community Templates** (Web, API, Cloud, Container, Mobile)
- **Comprehensive Documentation**

---

## 🧪 Test Results

```
Total Tests: 42
Passed: 42 (100%)
Coverage: 49% overall, 81%+ for core modules
```

---

## 🚀 Quick Start

### 1. Install
```bash
pip install zen-ai-pentest
```

### 2. Configure
```bash
export OPENAI_API_KEY="sk-..."
export ZEN_SAFETY_LEVEL="non_destructive"
```

### 3. Run Autonomous Scan
```python
from autonomous.react import ReActLoop, AgentConfig

config = AgentConfig(max_iterations=10)
agent = ReActLoop(llm_client=client, config=config)
result = await agent.run(
    goal="Find SQL injection vulnerabilities",
    target="https://example.com"
)
```

### 4. Start Web UI
```bash
cd web_ui/backend
uvicorn main:app --reload
```

---

## 🖥️ Frontend Components

| Component | Status | Description |
|-----------|--------|-------------|
| ScanDashboard | ✅ | Real-time scan monitoring |
| AgentStatus | ✅ | Live agent tracking |
| FindingsList | ✅ | Security findings management |
| RiskScoreCard | ✅ | Interactive risk visualization |

---

## 📚 Documentation

- [Getting Started](docs/tutorials/getting-started.md)
- [API Reference](docs/api/)
- [Architecture](docs/architecture/)
- [Roadmap Status](ROADMAP_2026_STATUS.md)

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `ZEN_SAFETY_LEVEL` | `non_destructive` | Safety level |
| `ZEN_MAX_ITERATIONS` | `50` | Max agent iterations |

---

## 🛡️ Safety Levels

| Level | Tools | Use Case |
|-------|-------|----------|
| READ_ONLY | nmap, amass | Production |
| NON_DESTRUCTIVE | +nuclei, nikto | Staging |
| EXPLOIT | +sqlmap | Test env |
| AGGRESSIVE | +metasploit | Lab only |

---

## 📊 Statistics

- **Lines of Code**: 25,000+
- **Test Coverage**: 49% (81%+ core)
- **Python Files**: 150+
- **CI/CD Workflows**: 18
- **Security Tools**: 15+

---

## 🔗 Links

- **PyPI**: https://pypi.org/project/zen-ai-pentest/
- **GitHub**: https://github.com/SHAdd0WTAka/zen-ai-pentest
- **Docker Hub**: https://hub.docker.com/r/shadd0wtaka/zen-ai-pentest
- **Docs**: https://github.com/SHAdd0WTAka/zen-ai-pentest/tree/main/docs

---

## 🙏 Contributors

- SHAdd0WTAka - Project Lead
- Community Contributors

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

**Full Changelog**: https://github.com/SHAdd0WTAka/zen-ai-pentest/releases/tag/v2.0.0
