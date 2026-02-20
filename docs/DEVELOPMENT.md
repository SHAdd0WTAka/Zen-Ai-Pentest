# Development Guide

> **Complete guide for developing Zen-AI-Pentest**

---

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Adding New Tools](#adding-new-tools)
- [Adding New Agents](#adding-new-agents)
- [Code Style Guide](#code-style-guide)
- [Debugging Tips](#debugging-tips)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Common Development Tasks](#common-development-tasks)
- [Troubleshooting](#troubleshooting)

---

## Development Environment Setup

### Prerequisites

- **Python**: 3.11 or higher
- **Docker**: 20.10+ (for containerized development)
- **Git**: 2.30+
- **PostgreSQL**: 14+ (or use Docker)
- **Redis**: 6+ (optional, for caching)

### Option 1: Local Development

```bash
# 1. Clone the repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Copy environment file
cp .env.example .env

# 6. Edit .env with your settings
# Required: DATABASE_URL, SECRET_KEY, KIMI_API_KEY (optional)

# 7. Initialize database
python scripts/init_db.py

# 8. Run the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker Development

```bash
# 1. Clone and enter repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# 2. Start development environment
docker-compose -f docker-compose.yml up -d

# 3. View logs
docker-compose logs -f api

# 4. Run commands inside container
docker-compose exec api bash
```

### Option 3: VS Code Dev Container

```bash
# 1. Open in VS Code
code .

# 2. Press F1 → "Dev Containers: Reopen in Container"
# 3. VS Code will build and open in container automatically
```

---

## Project Structure

```
zen-ai-pentest/
├── agents/                    # AI Agent implementations
│   ├── react_agent.py        # Core ReAct agent
│   ├── agent_base.py         # Base agent classes
│   └── agent_orchestrator.py # Multi-agent orchestration
├── api/                       # FastAPI Backend
│   ├── main.py               # Application entry point
│   ├── auth.py               # Authentication routes
│   ├── routes/               # API route handlers
│   ├── schemas.py            # Pydantic models
│   └── websocket.py          # WebSocket handlers
├── autonomous/               # Autonomous agent system
│   ├── agent_loop.py         # ReAct loop implementation
│   ├── sqlmap_integration.py # SQLMap with safety
│   ├── exploit_validator.py  # Safe exploit validation
│   └── memory.py             # Agent memory system
├── tools/                    # Security tool integrations
│   ├── nmap_integration.py
│   ├── nuclei_integration.py
│   └── ...
├── risk_engine/              # Risk analysis engine
│   ├── cvss.py
│   ├── epss.py
│   └── false_positive_engine.py
├── database/                 # Database models
│   ├── models.py
│   └── migrations/
├── tests/                    # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
└── docker/                   # Docker configurations
```

---

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_react_agent.py -v

# Run specific test
pytest tests/unit/test_react_agent.py::test_agent_creation -v
```

### Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Security tests
pytest tests/security/ -v

# Exclude slow tests
pytest -m "not slow"

# Run only slow tests
pytest -m "slow"
```

For detailed testing information, see [TESTING.md](TESTING.md).

---

## Adding New Tools

### Step 1: Create Tool File

Create a new file in `tools/` directory:

```python
# tools/my_tool_integration.py

import asyncio
import subprocess
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ToolResult:
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0

class MyToolIntegration:
    """Integration for My Security Tool.
    
    Description of what this tool does.
    
    Safety Level: 1 (SAFE) to 3 (AGGRESSIVE)
    """
    
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.name = "my_tool"
        self.description = "Description of the tool"
        self.safety_level = 1  # 0=SAFE, 1=NORMAL, 2=ELEVATED, 3=AGGRESSIVE
    
    async def execute(self, target: str, **options) -> ToolResult:
        """Execute the tool against a target.
        
        Args:
            target: Target URL/IP to scan
            **options: Additional tool-specific options
            
        Returns:
            ToolResult with scan results
        """
        # 1. Validate target (safety check)
        if not self._validate_target(target):
            return ToolResult(
                success=False, 
                error="Invalid target or private IP blocked"
            )
        
        # 2. Build command
        cmd = self._build_command(target, options)
        
        # 3. Execute with timeout
        try:
            start_time = asyncio.get_event_loop().time()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # 4. Parse output
            if process.returncode == 0:
                data = self._parse_output(stdout.decode())
                return ToolResult(
                    success=True,
                    data=data,
                    execution_time=execution_time
                )
            else:
                return ToolResult(
                    success=False,
                    error=stderr.decode(),
                    execution_time=execution_time
                )
                
        except asyncio.TimeoutError:
            process.kill()
            return ToolResult(
                success=False,
                error=f"Tool execution timed out after {self.timeout}s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def _validate_target(self, target: str) -> bool:
        """Validate target is safe to scan."""
        # Block private IPs
        private_prefixes = ('10.', '192.168.', '172.16.', '172.17.', 
                           '172.18.', '172.19.', '172.20.', '172.21.',
                           '172.22.', '172.23.', '172.24.', '172.25.',
                           '172.26.', '172.27.', '172.28.', '172.29.',
                           '172.30.', '172.31.', '127.', '0.0.0.0', '::1')
        
        for prefix in private_prefixes:
            if target.startswith(prefix):
                return False
        
        # Block localhost variants
        localhost_names = ('localhost', '.local', '.internal')
        for name in localhost_names:
            if name in target.lower():
                return False
        
        return True
    
    def _build_command(self, target: str, options: Dict) -> list:
        """Build command arguments."""
        cmd = ['my-tool', target]
        
        if options.get('verbose'):
            cmd.append('-v')
        
        if 'threads' in options:
            cmd.extend(['-t', str(options['threads'])])
        
        return cmd
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse tool output into structured data."""
        # Implement parsing logic
        results = []
        
        for line in output.split('\n'):
            if 'FINDING:' in line:
                results.append({
                    'type': 'finding',
                    'details': line.split('FINDING:')[1].strip()
                })
        
        return {
            'findings': results,
            'raw_output': output
        }


# Synchronous wrapper for convenience
def scan_sync(target: str, **options) -> Dict[str, Any]:
    """Synchronous wrapper for the tool."""
    tool = MyToolIntegration()
    result = asyncio.run(tool.execute(target, **options))
    
    if result.success:
        return result.data
    else:
        raise RuntimeError(result.error)
```

### Step 2: Register Tool

Add to `tools/tool_registry.py`:

```python
from tools.my_tool_integration import MyToolIntegration

# In ToolRegistry class
def _register_default_tools(self):
    # ... existing tools ...
    self.register_tool("my_tool", MyToolIntegration)
```

### Step 3: Add API Endpoint

Add to `api/routes/tools.py`:

```python
@router.post("/tools/my-tool")
async def execute_my_tool(
    request: MyToolRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute My Tool against a target."""
    tool = MyToolIntegration()
    result = await tool.execute(
        target=request.target,
        verbose=request.verbose,
        threads=request.threads
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    return result.data
```

### Step 4: Write Tests

Create `tests/test_my_tool.py`:

```python
import pytest
from tools.my_tool_integration import MyToolIntegration

class TestMyToolIntegration:
    """Tests for My Tool integration."""
    
    @pytest.fixture
    def tool(self):
        return MyToolIntegration(timeout=30)
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_target(self, tool):
        """Test execution with valid target."""
        result = await tool.execute("scanme.nmap.org")
        assert result.success is True
        assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_block_private_ip(self, tool):
        """Test that private IPs are blocked."""
        result = await tool.execute("192.168.1.1")
        assert result.success is False
        assert "private" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_block_localhost(self, tool):
        """Test that localhost is blocked."""
        result = await tool.execute("localhost")
        assert result.success is False
```

---

## Adding New Agents

### Step 1: Create Agent Class

```python
# agents/my_agent.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class AgentConfig:
    """Configuration for the agent."""
    max_iterations: int = 10
    timeout: int = 3600
    use_memory: bool = True
    risk_level: int = 1

class MyAgent:
    """My Custom Agent for specific tasks.
    
    This agent specializes in [describe purpose].
    """
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.state = AgentState.IDLE
        self.memory: List[Dict] = []
        self.iteration = 0
    
    async def run(
        self, 
        objective: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute agent workflow.
        
        Args:
            objective: The goal to achieve
            context: Additional context information
            
        Returns:
            Results dictionary
        """
        self.state = AgentState.PLANNING
        
        try:
            # 1. Plan actions
            plan = await self._plan(objective, context)
            
            # 2. Execute plan
            self.state = AgentState.EXECUTING
            results = []
            
            for action in plan:
                result = await self._execute_action(action)
                results.append(result)
                
                # Update memory
                if self.config.use_memory:
                    self._update_memory(action, result)
                
                # Check if objective achieved
                if await self._objective_achieved(objective, results):
                    break
                
                self.iteration += 1
                if self.iteration >= self.config.max_iterations:
                    break
            
            # 3. Reflect and finalize
            self.state = AgentState.REFLECTING
            final_result = await self._reflect(results)
            
            self.state = AgentState.COMPLETED
            return final_result
            
        except Exception as e:
            self.state = AgentState.ERROR
            return {
                "success": False,
                "error": str(e),
                "state": self.state.value
            }
    
    async def _plan(
        self, 
        objective: str, 
        context: Dict
    ) -> List[Dict[str, Any]]:
        """Create action plan."""
        # Implement planning logic
        return [
            {"action": "step1", "params": {}},
            {"action": "step2", "params": {}}
        ]
    
    async def _execute_action(
        self, 
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single action."""
        # Implement action execution
        return {"action": action, "result": "success"}
    
    def _update_memory(
        self, 
        action: Dict, 
        result: Dict
    ):
        """Update agent memory."""
        self.memory.append({
            "iteration": self.iteration,
            "action": action,
            "result": result
        })
    
    async def _objective_achieved(
        self, 
        objective: str, 
        results: List[Dict]
    ) -> bool:
        """Check if objective is achieved."""
        # Implement completion check
        return False
    
    async def _reflect(
        self, 
        results: List[Dict]
    ) -> Dict[str, Any]:
        """Reflect on results and generate final output."""
        return {
            "success": True,
            "objective": "completed",
            "results": results,
            "iterations": self.iteration,
            "memory": self.memory
        }
```

### Step 2: Register with Orchestrator

```python
# agents/agent_orchestrator.py

from agents.my_agent import MyAgent, AgentConfig

class AgentOrchestrator:
    def __init__(self):
        self.agent_types = {
            # ... existing agents ...
            "my_agent": (MyAgent, AgentConfig),
        }
```

### Step 3: Add API Routes

```python
# api/routes/agents.py

from agents.my_agent import MyAgent, AgentConfig

@router.post("/agents/my-agent/run")
async def run_my_agent(
    request: MyAgentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Run My Custom Agent."""
    config = AgentConfig(
        max_iterations=request.max_iterations,
        risk_level=request.risk_level
    )
    
    agent = MyAgent(config)
    
    # Run in background for long tasks
    if request.async_execution:
        background_tasks.add_task(
            agent.run,
            objective=request.objective,
            context=request.context
        )
        return {"status": "started", "agent_id": generate_id()}
    
    # Run synchronously
    result = await agent.run(
        objective=request.objective,
        context=request.context
    )
    
    return result
```

---

## Code Style Guide

### Python Style

We follow PEP 8 with some modifications:

```python
# Line length: 127 characters (not 79)
# Use Black formatter

# Imports: grouped and sorted
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import httpx
from fastapi import FastAPI

# Local
from tools.nmap_integration import NmapScanner


# Class naming: PascalCase
class MyClassName:
    """Docstring with description.
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    """
    
    # Constants: UPPER_CASE
    MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 30
    
    def __init__(self, param1: str, param2: int = 10):
        """Initialize the class.
        
        Args:
            param1: First parameter
            param2: Second parameter (default: 10)
        """
        self.param1 = param1  # Public attribute
        self._param2 = param2  # Private attribute
    
    async def process(
        self,
        data: Dict[str, Any],
        options: Optional[Dict] = None
    ) -> List[Dict]:
        """Process data with options.
        
        Args:
            data: Input data dictionary
            options: Optional processing options
            
        Returns:
            List of processed results
            
        Raises:
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        results = []
        for key, value in data.items():
            processed = await self._process_item(key, value)
            results.append(processed)
        
        return results
    
    async def _process_item(self, key: str, value: Any) -> Dict:
        """Process a single item (private method)."""
        return {"key": key, "value": value}
```

### Type Hints

Always use type hints:

```python
from typing import Dict, List, Optional, Union, Any

def process_data(
    data: Dict[str, Any],
    filters: Optional[List[str]] = None,
    max_items: int = 100
) -> List[Dict[str, Union[str, int]]]:
    """Process data with optional filters."""
    ...
```

### Error Handling

```python
# Use specific exceptions
try:
    result = await process_data(data)
except ValueError as e:
    logger.warning(f"Invalid data: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except asyncio.TimeoutError:
    logger.error("Processing timed out")
    raise HTTPException(status_code=504, detail="Timeout")
except Exception as e:
    logger.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal error")
```

### Documentation

Use Google-style docstrings:

```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[Dict] = None
) -> Dict[str, Any]:
    """Short description of function.
    
    Longer description explaining behavior, edge cases,
    and any important implementation details.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        param3: Optional third parameter (default: None)
        
    Returns:
        Dictionary containing results with structure:
        {
            "status": "success" | "error",
            "data": {...},
            "metadata": {...}
        }
        
    Raises:
        ValueError: When param1 is invalid
        RuntimeError: When processing fails
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["status"])
        'success'
    """
```

---

## Debugging Tips

### Enable Debug Logging

```python
# In your code or .env
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Or set in .env
LOG_LEVEL=DEBUG
```

### Debug Mode in FastAPI

```bash
# Start with reload and debug
uvicorn api.main:app --reload --log-level debug
```

### Using pdb

```python
import pdb; pdb.set_trace()  # Set breakpoint

# Common commands:
# n - next line
# s - step into
# c - continue
# p variable - print variable
# l - list source
```

### Async Debugging

```python
import asyncio

# Enable asyncio debug mode
asyncio.get_event_loop().set_debug(True)

# Or set environment variable
PYTHONASYNCIODEBUG=1
```

### Memory Debugging

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# ... your code ...

# Get snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

### Database Debugging

```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or in SQLAlchemy
echo=True  # When creating engine
```

---

## Pre-commit Hooks

### Setup

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Configuration

See `.pre-commit-config.yaml` for configured hooks:

- **ruff** - Linting and formatting
- **black** - Code formatting
- **isort** - Import sorting
- **bandit** - Security scanning
- **mypy** - Type checking

---

## Common Development Tasks

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Background Tasks

```python
from fastapi import BackgroundTasks

@router.post("/tasks")
async def create_task(
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(long_running_function, arg1, arg2)
    return {"status": "started"}
```

### Testing with Fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}

# Use in tests
def test_endpoint(client, auth_headers):
    response = client.get("/scans", headers=auth_headers)
    assert response.status_code == 200
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Ensure you're in project root and venv is activated |
| Database connection | Check DATABASE_URL in .env |
| Permission denied | Add user to docker group: `sudo usermod -aG docker $USER` |
| Port already in use | Find and kill process: `sudo lsof -i :8000` |
| Tests failing | Check test database is initialized: `pytest --fixtures` |

### Getting Help

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [SUPPORT.md](../SUPPORT.md)
3. Join our [Discord](https://discord.gg/zJZUJwK9AC)
4. Open an issue on GitHub

---

<p align="center">
  <b>Happy coding! 🚀</b><br>
  <sub>For questions, see <a href="../CONTRIBUTING.md">CONTRIBUTING.md</a></sub>
</p>
