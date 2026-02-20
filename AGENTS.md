# Zen-AI-Pentest - Agent Guide

> **For AI Agents**: Essential information for understanding and working with the Zen-AI-Pentest codebase.

---

## 📋 Project Overview

**Zen-AI-Pentest** is an autonomous, AI-powered penetration testing framework that executes **real security tools** with intelligent orchestration.

- **Name**: zen-ai-pentest
- **Version**: 3.0.0
- **License**: MIT
- **Python**: 3.9+
- **Repository**: https://github.com/SHAdd0WTAka/zen-ai-pentest

### 🎯 Core Philosophy: Real Data Execution (No Mocks!)

This framework executes **actual security tools** - no simulations:
- ✅ **Nmap** - Real port scanning with XML output parsing
- ✅ **Nuclei** - Real vulnerability detection with JSON output
- ✅ **SQLMap** - Real SQL injection testing with safety controls
- ✅ **Multi-Agent** - Researcher & Analyst agents cooperating
- ✅ **Docker Sandbox** - Isolated tool execution for safety

---

## 🏗️ Architecture

```
zen-ai-pentest/
├── agents/                 # AI Agents (ReAct, orchestration)
│   ├── react_agent.py     # Core ReAct implementation
│   ├── agent_base.py      # Multi-agent base classes
│   └── agent_orchestrator.py
├── autonomous/            # Autonomous agent system ⭐
│   ├── agent_loop.py      # ReAct loop with REAL tool execution
│   ├── sqlmap_integration.py  # SQLMap with safety controls
│   ├── exploit_validator.py
│   └── memory.py
├── api/                   # FastAPI backend
│   ├── main.py           # FastAPI app
│   ├── routes/           # API endpoints
│   └── schemas.py        # Pydantic models
├── docker/                # Docker configuration ⭐
│   ├── Dockerfile.tools  # Tool sandbox image
│   └── sandboxed_executor.py  # Secure execution
├── examples/              # Usage examples ⭐
│   └── multi_agent_demo.py    # Researcher+Analyst demo
├── tests/                 # Test suite
│   ├── test_real_nuclei.py    # Real Nuclei tests
│   └── test_sqlmap.py         # SQLMap tests
├── tools/                 # Tool integrations
│   ├── nmap_integration.py
│   └── nuclei_integration.py
└── docs/                  # Documentation
    └── IMPLEMENTATION_SUMMARY.md  # Complete feature overview
```

---

## 🔑 Key Components

### 1. Autonomous Agent System (`autonomous/`)

The heart of the framework - executes real tools with safety controls.

**Key Files:**
- `agent_loop.py` - Core ReAct loop with tool execution
- `sqlmap_integration.py` - SQLMap integration
- `exploit_validator.py` - Safe exploit validation

**Pattern:**
```python
class NmapScanner(BaseTool):
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        # Real subprocess execution
        cmd = f"nmap {options} -p {ports} {target}"
        process = await asyncio.create_subprocess_exec(...)
        # Parse XML/JSON output
        parsed_data = self._parse_nmap_xml(xml_output)
        return ToolResult(success=True, data=parsed_data)
```

### 2. Multi-Agent System (`agents/`)

Cooperative agents that share context via message passing.

**Agent Roles:**
- `RESEARCHER` - Gathers information
- `ANALYST` - Analyzes findings
- `EXPLOIT` - Manages exploitation
- `COORDINATOR` - Orchestrates workflow

**Usage:**
```python
from examples.multi_agent_demo import run_demo
# See Researcher + Analyst cooperation
```

### 3. Docker Sandbox (`docker/`)

Secure, isolated tool execution.

**Key Features:**
- Resource limits (CPU, memory)
- Network isolation
- Read-only filesystems
- Container lifecycle management

**File:** `docker/sandboxed_executor.py`

---

## 🛡️ Safety Controls

All tool executions include safety guardrails:

| Control | Implementation |
|---------|---------------|
| Private IP Blocking | Blocks 192.168.x.x, 10.x.x.x, 172.16-31.x.x |
| Timeout Management | Prevents hanging processes (default: 300s) |
| Resource Limits | CPU/memory constraints in Docker |
| Read-only FS | Container filesystem isolation |
| Risk Levels | SQLMap: 0-3 (0=safe, 3=aggressive) |

**Important:** Never disable safety controls for production use.

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Specific test files
pytest tests/test_real_nuclei.py -v
pytest tests/test_sqlmap.py -v

# With coverage
pytest --cov=autonomous --cov=tools
```

### Test Structure

```
tests/
├── test_real_nuclei.py     # Real Nuclei execution tests
├── test_sqlmap.py          # SQLMap integration tests
├── unit/                   # Unit tests
├── integration/            # Integration tests
└── autonomous/             # Autonomous agent tests
```

---

## 🚀 Development Guidelines

### Adding a New Tool Integration

1. **Create file** in `tools/` or `autonomous/`
2. **Extend `BaseTool`** class
3. **Implement `execute()`** method with real subprocess
4. **Add safety checks** (IP validation, timeouts)
5. **Parse output** (XML/JSON/stdout)
6. **Add tests** in `tests/`
7. **Update documentation**

### Example Template:

```python
from autonomous.agent_loop import BaseTool, ToolResult

class NewTool(BaseTool):
    name = "new_tool"
    description = "Description of the tool"

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        # 1. Validate parameters
        target = parameters.get("target")
        if not self._is_valid_target(target):
            return ToolResult(success=False, error="Invalid target")

        # 2. Build command
        cmd = ["tool_name", "-flag", target]

        # 3. Execute with timeout
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="Timeout")

        # 4. Parse output
        data = self._parse_output(stdout.decode())

        return ToolResult(success=True, data=data)
```

### Code Style

- **Formatter**: Black (line-length: 127)
- **Imports**: isort with black profile
- **Types**: Use type hints where possible
- **Docs**: Google-style docstrings
- **Async**: Prefer async/await for I/O operations

---

## 📚 Important Documentation

| File | Purpose |
|------|---------|
| `IMPLEMENTATION_SUMMARY.md` | Complete feature overview (Phases A-E) |
| `README.md` | Main project documentation |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/API.md` | API reference |

---

## 🔐 Security Guidelines

### For AI Agents Working on This Codebase:

1. **Never commit API keys** - Use environment variables
2. **Keep safety controls** - Don't disable IP blocking
3. **Validate inputs** - Sanitize all user inputs
4. **Use timeouts** - Always set execution timeouts
5. **Test safely** - Use scanme.nmap.org for testing
6. **Docker isolation** - Use sandboxed executor when possible

### Pre-commit Checks

```bash
# API key validation
./scripts/check_api_keys.sh

# Security scanning
bandit -r . -ll
safety check -r requirements.txt
```

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Tool not found | Ensure tool is in PATH (nmap, sqlmap, nuclei) |
| Permission denied | Check Docker permissions or run with sudo |
| Timeout errors | Increase timeout in tool configuration |
| XML parsing fails | Validate tool output format |
| Import errors | Install requirements: `pip install -r requirements.txt` |

---

## 🎯 Quick Reference

### Running the Framework

```bash
# API server
uvicorn api.main:app --reload

# CLI mode
python zen_ai_pentest.py --interactive

# Docker
docker-compose up -d

# Multi-agent demo
python examples/multi_agent_demo.py
```

### Environment Variables

```bash
# Required for tool execution
NMAP_PATH=/usr/bin/nmap
SQLMAP_PATH=/usr/bin/sqlmap
NUCLEI_PATH=/usr/local/bin/nuclei

# AI Backends (Kimi AI recommended for best performance)
KIMI_API_KEY=your-kimi-api-key      # Recommended: https://platform.moonshot.cn
DEFAULT_BACKEND=kimi                 # Default AI provider
DEFAULT_MODEL=kimi-k2.5              # Default model

# Alternative Backends (optional)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# OPENROUTER_API_KEY=...

# Docker
DOCKER_HOST=unix:///var/run/docker.sock
```

> 💡 **Recommendation**: Kimi AI (Moonshot) provides excellent performance for security analysis tasks with long context support and tool reasoning capabilities.

---

## 📊 Project Status

**Current State: 100% Complete**

- ✅ Phase A: Nuclei Integration
- ✅ Phase B: SQLMap Integration
- ✅ Phase C: Multi-Agent System
- ✅ Phase D: Docker Sandbox
- ✅ Phase E: Documentation

**Last Updated**: 2025-02-14

---

## 🤝 Contributing

When making changes:
1. Follow the existing code style
2. Add tests for new features
3. Update relevant documentation
4. Ensure safety controls are maintained
5. Run pre-commit hooks before committing

---

---

## 📈 Repository Evolution (Chronological)

> **For AI Agents**: This timeline helps you understand the project's evolution and current state.

### Phase 1: Foundation (Early Development)
- **Initial Setup** - Basic project structure, FastAPI backend
- **Core Architecture** - Agent base classes, tool integration framework
- **First Tools** - Nmap integration, basic port scanning

### Phase 2: Real Tool Execution
- **Nuclei Integration** - Real vulnerability scanning with JSON parsing
- **SQLMap Integration** - SQL injection testing with safety controls
- **Docker Sandbox** - Isolated tool execution environment

### Phase 3: Multi-Agent System
- **ReAct Pattern** - Reason → Act → Observe → Reflect loop
- **Agent Orchestrator** - Workflow management for multiple agents
- **Memory System** - Short-term and long-term memory for agents

### Phase 4: Security & Risk Engine
- **Guardrails** - IP blocking, domain filtering, risk levels
- **Risk Engine** - CVSS/EPSS scoring, false positive reduction
- **Exploit Validator** - Sandboxed exploit validation

### Phase 5: Enterprise Features
- **CI/CD Integration** - GitHub Actions, GitLab CI, Jenkins
- **Reporting** - PDF/HTML/JSON report generation
- **Notifications** - Slack, Email, JIRA integrations

### Phase 6: AI Persona System
- **11 Personas** - Recon, Exploit, Report, Audit, Social, Network, Mobile, Red Team, ICS, Cloud, Crypto
- **Kimi AI Integration** - Native CLI and helper tools
- **Screenshot Analysis** - Visual vulnerability assessment

### Phase 7: Current State (v2.3.9)
- **40+ Tools** - Complete security toolkit integration
- **VPN Integration** - ProtonVPN, OpenVPN, WireGuard support
- **Benchmarking** - Performance testing and competitor comparison

---

## ⚖️ CRITICAL: Legal Guardrails for AI Agents

> **⚠️ MANDATORY**: You MUST follow these guidelines when assisting users with this framework.

### Legal Responsibility

1. **Explicit Authorization Required**
   - **ALWAYS** remind users they need explicit written authorization before scanning ANY system
   - Unauthorized scanning is **ILLEGAL** in most jurisdictions
   - Legal consequences include: criminal charges, civil lawsuits, fines, imprisonment

2. **User Responsibility**
   - **The USER is solely responsible** for their actions
   - AI assistants **CANNOT** be held legally liable
   - Document that the user acts with intent and full knowledge of consequences

3. **Jurisdiction-Specific Notes**
   - **Germany**: AI systems cannot be criminally prosecuted, only users
   - **USA**: CFAA (Computer Fraud and Abuse Act) violations carry heavy penalties
   - **EU**: GDPR violations + cybercrime laws apply
   - **Global**: Most countries have similar cybercrime legislation

### Required User Warnings

When assisting with this framework, you MUST include warnings like:

```
⚠️ LEGAL WARNING: Only scan systems you own or have EXPLICIT WRITTEN
permission to test. Unauthorized scanning is ILLEGAL and can result in:
- Criminal prosecution
- Civil liability
- Fines and imprisonment

You are SOLELY RESPONSIBLE for your actions.
```

### Ethical Guidelines

1. **Educational Context** - Emphasize this is for learning/authorized testing only
2. **Defense-Oriented** - Frame tools for defensive security (finding your own vulnerabilities)
3. **Bug Bounty** - Mention authorized programs (HackerOne, Bugcrowd) as legal outlets

---

## 📝 Optional: Prompt Logging

> **For Users**: Enable local prompt logging for accountability and session recovery.

### Enable Prompt Logging

```bash
# Set environment variable
export ZEN_LOG_PROMPTS=true
export ZEN_LOG_DIR=~/.zen-ai-pentest/logs

# Or in .env file
ZEN_LOG_PROMPTS=true
ZEN_LOG_DIR=~/.zen-ai-pentest/logs
```

### Log Format

```
~/.zen-ai-pentest/logs/
├── 2025-02-18/
│   ├── prompt_001_103052.txt
│   ├── prompt_002_103145.txt
│   └── response_001_103052.txt
```

Each log file contains:
- Timestamp
- User prompt
- AI response
- Tool calls made

### Benefits

1. **Accountability** - Track what was requested
2. **Session Recovery** - Restore previous states
3. **Debugging** - Review AI decision-making
4. **Legal Protection** - Documentation of authorized use

> **Note**: Logs are stored LOCALLY only. No data is sent to external servers.

---

*This document is for AI agents working on Zen-AI-Pentest. For human contributors, see README.md and CONTRIBUTING.md.*
