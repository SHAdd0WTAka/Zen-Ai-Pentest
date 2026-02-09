# Zen-AI-Pentest Development Skills

## Projekt-Übersicht

**Zen-AI-Pentest** ist ein autonomes, KI-gesteuertes Penetration-Testing-Framework mit:
- 1206+ Dateien, 179MB Repository
- 58 GitHub Actions Workflows
- 20+ integrierte Sicherheitstools
- Multi-Agent-Architektur mit ReAct Pattern
- FastAPI-Backend mit WebSocket-Support
- React-Dashboard für Web-UI

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (React + TypeScript + Tailwind)               │
├─────────────────────────────────────────────────────────┤
│  API LAYER (FastAPI + WebSocket + JWT Auth)             │
├─────────────────────────────────────────────────────────┤
│  AUTONOMOUS LAYER (ReAct Agent + Memory + Tool Exec)    │
├─────────────────────────────────────────────────────────┤
│  RISK ENGINE (CVSS + EPSS + False Positive Reduction)   │
├─────────────────────────────────────────────────────────┤
│  TOOLS LAYER (Nmap, SQLMap, Metasploit, etc.)           │
├─────────────────────────────────────────────────────────┤
│  DATA LAYER (PostgreSQL + SQLite + Redis)               │
└─────────────────────────────────────────────────────────┘
```

## Kritische Issues (P0)

1. **Command Injection Risk** - `tool_executor.py` nutzt `subprocess_shell` statt `subprocess_exec`
2. **Variable Bug** - `react_agent_vm.py`: `config.vm_username` sollte `self.vm_config.vm_username` sein
3. **Hardcoded Credentials** - Default-Credentials in API auth fallback
4. **SSL Verification Disabled** - Mehrere Tools haben `verify=False`

## Module-Übersicht

### Core (`core/`)
- `orchestrator.py` - ZenOrchestrator, Hauptkoordinator
- `plugin_manager.py` - Plugin-System
- `rate_limiter.py` - Rate Limiting
- `cache.py` - Multi-Tier Caching
- `shield_integration.py` - Zen Shield Integration

### Agents (`agents/`)
- `react_agent.py` - ReAct Pattern Implementierung
- `react_agent_enhanced.py` - Erweiterter ReAct Agent
- `react_agent_vm.py` - VM-basierter Agent
- `agent_orchestrator.py` - Agent-Koordination
- Spezialisierte Agents: `research_agent`, `analysis_agent`, `exploit_agent`

### Autonomous (`autonomous/`)
- `agent_loop.py` - State Machine (IDLE → PLANNING → EXECUTING → OBSERVING → REFLECTING → COMPLETED)
- `tool_executor.py` - Tool-Ausführung mit Safety-Levels
- `exploit_validator.py` - Sandbox-Validierung
- `memory.py` - LangGraph Memory Integration
- `react.py` - ReAct Core Loop

### Risk Engine (`risk_engine/`)
- `false_positive_engine.py` - Bayes'sche Filter + Multi-LLM Voting
- `business_impact_calculator.py` - Finanzielle/Compliance-Auswirkungen
- `cvss.py` - CVSS 3.1 Calculator
- `epss.py` - EPSS Client

### API (`api/`)
- `main.py` - FastAPI App
- `auth.py` - JWT Authentication
- `routes/` - 50+ API Endpunkte
- `websocket.py` + `websocket_v2.py` - Real-time Updates

### Tools (`tools/`)
- Network: `nmap_integration.py` (fehlt!), `masscan_integration.py`, `scapy_integration.py`
- Web: `sqlmap_integration.py`, `gobuster_integration.py`, `burpsuite_integration.py`
- Exploit: `metasploit_integration.py`, `hydra_integration.py`
- AD: `bloodhound_integration.py`, `crackmapexec_integration.py`, `responder_integration.py`

### Memory (`memory/`)
- 4-Layer Architecture: Working → Short-term → Long-term → Vector Store
- Backends: SQLite, Redis
- LangGraph Integration

## CI/CD Workflows (58 total)

**Kritische Workflows:**
- `ci.yml` - Haupt-CI
- `security.yml` - Sicherheits-Scans
- `code-quality.yml` - Linting & Formatting
- `pr-validation.yml` - PR Checks
- `release.yml` - Release-Prozess
- `deploy.yml` - Deployment

**Auto-Workflows:**
- `dependabot-auto-merge.yml` - Automatische Dependency-Updates
- `auto-fix-repository.yml` - Automatische Fixes
- `health-check.yml` - Repository-Health

## Entwicklungs-Standards

### Code Style
- **Black**: Line length 127
- **isort**: Profile "black"
- **Ruff**: E, F, W rules
- **mypy**: Type checking (optional)

### Testing
- **pytest** mit asyncio-Unterstützung
- Coverage-Target: 70%
- Security-Tests: Bandit, Safety

### Security
- Alle Dependencies auf CVE-Versionen prüfen
- Keine Hardcoded Secrets
- Input-Validierung mit `input_validator.py`
- Zen Shield für Output-Sanitization

## Wichtige Befehle

```bash
# Setup
pip install -e ".[dev]"

# Tests
pytest --cov=. --cov-report=html

# Linting
black .
isort .
flake8

# Security
bandit -r .
safety check

# API starten
uvicorn api.main:app --reload

# Docker
docker-compose up -d
```

## Versions-Inkonsistenzen (zu fixen)

- `setup.py`: Version 2.3.9 ✅
- `pyproject.toml`: Version 2.3.9
- `README.md`: Version 2.3.9 ✅
- `action.yml`: Version 2.3.9

**Empfohlene Version: 2.3.9**
