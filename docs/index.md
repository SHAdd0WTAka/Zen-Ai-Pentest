# Zen AI Pentest Documentation

## Overview

Zen AI Pentest is an autonomous red team framework that combines AI-powered reasoning with real security tool execution for comprehensive penetration testing.

## Quick Start

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

# Access web UI
open http://localhost:8000
```

## Architecture

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

## Key Features

### 1. Autonomous Pentesting (Q1)
- **ReAct Loop**: Reasoning + Acting with self-correction
- **Tool Executor**: 15+ security tools with safety controls
- **Memory System**: Multi-layer persistent storage

### 2. Risk Scoring (Q2)
- **Multi-Factor Formula**: CVSS×0.25 + EPSS×0.25 + Business×0.35 + Validation×0.15
- **Severity Levels**: Critical (24h), High (72h), Medium (14d), Low (30d)
- **Context-Aware**: Internet exposure, data sensitivity, compliance

### 3. DevSecOps Integration (Q3)
- **Web UI**: Real-time scan monitoring
- **CI/CD**: GitHub Actions, GitLab CI, Jenkins, Kubernetes
- **API**: RESTful API with WebSocket updates

### 4. Community (Q4)
- **Benchmarks**: OWASP, WrongSecrets, DVWA, WebGoat
- **Templates**: Web, API, Cloud, Container, Mobile
- **Documentation**: Comprehensive guides

## Usage

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

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/autonomous/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Configuration

### Environment Variables

```bash
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
MISTRAL_API_KEY=...

# Safety
ZEN_SAFETY_LEVEL=non_destructive  # read_only, non_destructive, exploit, aggressive
ZEN_MAX_ITERATIONS=50

# Paths
ZEN_DATA_DIR=./data
ZEN_LOG_DIR=./logs
```

## Safety Levels

| Level | Description | Tools Allowed |
|-------|-------------|---------------|
| READ_ONLY | Passive reconnaissance only | nmap, amass, subfinder |
| NON_DESTRUCTIVE | Active scanning without exploitation | nuclei, nikto, gobuster |
| EXPLOIT | Controlled exploitation | sqlmap, metasploit (limited) |
| AGGRESSIVE | Full exploitation | All tools (requires explicit approval) |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Support

- GitHub Issues: [github.com/SHAdd0WTAka/zen-ai-pentest/issues](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues)
- Discussions: [github.com/SHAdd0WTAka/zen-ai-pentest/discussions](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions)

## Roadmap

See [ROADMAP_2026_STATUS.md](../ROADMAP_2026_STATUS.md) for detailed implementation status.
