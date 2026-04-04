"""
Pytest configuration and fixtures for Zen AI Pentest tests.
Merged with 100-Agent PoC testing infrastructure.
"""

import asyncio
import os
import random
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import pytest
import pytest_asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ADMIN_PASSWORD"] = "testpass"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["TESTING"] = "true"


# ============================================================================
# Session Fixtures
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment."""
    # Setup
    yield
    # Cleanup
    test_db = Path("./test.db")
    if test_db.exists():
        test_db.unlink()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Global test configuration for 100-Agent PoC."""
    return {
        "max_agents": 100,
        "agent_spawn_rate": 10,  # agents per second
        "agent_startup_timeout": 30,  # seconds
        "test_timeout": 300,  # seconds
        "memory_limit_mb": 5120,  # 5GB for 100 agents
        "cpu_limit_percent": 80,
        "cleanup_timeout": 10,
    }


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--agent-count",
        action="store",
        default=10,
        type=int,
        help="Number of agents to use in tests",
    )
    parser.addoption(
        "--stress-duration",
        action="store",
        default=60,
        type=int,
        help="Duration for stress tests in seconds",
    )
    parser.addoption(
        "--chaos-mode",
        action="store_true",
        default=False,
        help="Enable chaos testing mode",
    )


@pytest.fixture
def agent_count(request) -> int:
    """Get agent count from command line or marker."""
    # Check for marker override
    marker = request.node.get_closest_marker("agent_n")
    if marker:
        return marker.args[0] if marker.args else 10

    # Default from command line
    return request.config.getoption("--agent-count")


# ============================================================================
# Event Loop Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_event_loop():
    """Provide a clean async event loop for each test."""
    loop = asyncio.get_event_loop()
    yield loop


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="function")
def temp_cache_dir(temp_dir):
    """Create a temporary cache directory."""
    cache_dir = os.path.join(temp_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


@pytest.fixture(scope="function")
def temp_db_path(temp_dir):
    """Create a temporary database path."""
    return os.path.join(temp_dir, "test.db")


# ============================================================================
# Mock Agent Fixtures (100-Agent PoC)
# ============================================================================


@dataclass
class MockAgent:
    """Mock agent for testing."""

    agent_id: str
    name: str
    status: str = "idle"
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    created_at: float = field(default_factory=time.time)

    async def start(self) -> bool:
        """Start the agent."""
        self.status = "running"
        return True

    async def stop(self) -> bool:
        """Stop the agent."""
        self.status = "stopped"
        return True

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task."""
        self.tasks_completed += 1
        return {"agent_id": self.agent_id, "task": task, "status": "completed"}

    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            "agent_id": self.agent_id,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "uptime": time.time() - self.created_at,
        }


@pytest.fixture
def mock_agent_factory() -> Callable[[], MockAgent]:
    """Factory for creating mock agents."""
    counter = 0

    def _create_agent() -> MockAgent:
        nonlocal counter
        counter += 1
        return MockAgent(
            agent_id=f"agent_{uuid.uuid4().hex[:8]}",
            name=f"test_agent_{counter}",
        )

    return _create_agent


@pytest.fixture
async def single_agent(mock_agent_factory) -> MockAgent:
    """Create a single mock agent."""
    agent = mock_agent_factory()
    await agent.start()
    yield agent
    await agent.stop()


@pytest.fixture
async def ten_agents(mock_agent_factory) -> List[MockAgent]:
    """Create 10 mock agents."""
    agents = [mock_agent_factory() for _ in range(10)]
    for agent in agents:
        await agent.start()
    yield agents
    for agent in agents:
        await agent.stop()


@pytest.fixture
async def fifty_agents(mock_agent_factory) -> List[MockAgent]:
    """Create 50 mock agents."""
    agents = [mock_agent_factory() for _ in range(50)]
    for agent in agents:
        await agent.start()
    yield agents
    for agent in agents:
        await agent.stop()


@pytest.fixture
async def hundred_agents(mock_agent_factory) -> List[MockAgent]:
    """Create 100 mock agents - the main fixture for PoC testing."""
    agents = [mock_agent_factory() for _ in range(100)]

    # Start agents with rate limiting
    batch_size = 10
    for i in range(0, len(agents), batch_size):
        batch = agents[i : i + batch_size]
        await asyncio.gather(*[agent.start() for agent in batch])
        await asyncio.sleep(0.1)  # Rate limiting

    yield agents

    # Cleanup with timeout
    for agent in agents:
        try:
            await asyncio.wait_for(agent.stop(), timeout=5.0)
        except asyncio.TimeoutError:
            pass


@pytest.fixture
async def agent_pool(mock_agent_factory, agent_count) -> List[MockAgent]:
    """Create a variable-sized pool of agents."""
    agents = [mock_agent_factory() for _ in range(agent_count)]

    # Start all agents concurrently
    await asyncio.gather(*[agent.start() for agent in agents])

    yield agents

    # Cleanup
    await asyncio.gather(*[agent.stop() for agent in agents])


# ============================================================================
# Mock Orchestrator Fixtures
# ============================================================================


@dataclass
class MockOrchestrator:
    """Mock orchestrator for managing multiple agents."""

    max_agents: int = 100
    agents: Dict[str, MockAgent] = field(default_factory=dict)
    task_queue: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    async def spawn_agent(self, agent_factory: Callable) -> MockAgent:
        """Spawn a new agent."""
        if len(self.agents) >= self.max_agents:
            raise RuntimeError(f"Max agents ({self.max_agents}) reached")

        agent = agent_factory()
        await agent.start()
        self.agents[agent.agent_id] = agent
        return agent

    async def spawn_agents(self, agent_factory: Callable, count: int) -> List[MockAgent]:
        """Spawn multiple agents concurrently."""
        tasks = [self.spawn_agent(agent_factory) for _ in range(count)]
        return await asyncio.gather(*tasks)

    async def terminate_agent(self, agent_id: str) -> bool:
        """Terminate a specific agent."""
        if agent_id not in self.agents:
            return False
        agent = self.agents.pop(agent_id)
        await agent.stop()
        return True

    async def terminate_all(self) -> None:
        """Terminate all agents."""
        await asyncio.gather(*[self.terminate_agent(agent_id) for agent_id in list(self.agents.keys())])

    async def distribute_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Distribute a task to all agents."""
        results = await asyncio.gather(
            *[agent.execute_task(task) for agent in self.agents.values()],
            return_exceptions=True,
        )
        return [r for r in results if not isinstance(r, Exception)]

    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all agents."""
        agent_metrics = await asyncio.gather(*[agent.get_metrics() for agent in self.agents.values()])
        return {
            "total_agents": len(self.agents),
            "agent_metrics": agent_metrics,
            "queue_size": len(self.task_queue),
        }


@pytest.fixture
async def orchestrator() -> MockOrchestrator:
    """Create a mock orchestrator."""
    orch = MockOrchestrator(max_agents=100)
    yield orch
    await orch.terminate_all()


@pytest.fixture
async def orchestrator_with_agents(orchestrator, mock_agent_factory) -> MockOrchestrator:
    """Create an orchestrator pre-populated with agents."""
    await orchestrator.spawn_agents(mock_agent_factory, 10)
    yield orchestrator


# ============================================================================
# Mock Cache Fixtures
# ============================================================================


class MockCache:
    """Mock cache implementation for testing."""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._ttl and time.time() > self._ttl[key]:
            del self._data[key]
            del self._ttl[key]
            self._misses += 1
            return None

        if key in self._data:
            self._hits += 1
            return self._data[key]

        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        self._data[key] = value
        if ttl:
            self._ttl[key] = time.time() + ttl
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._data:
            del self._data[key]
            if key in self._ttl:
                del self._ttl[key]
            return True
        return False

    async def clear(self) -> bool:
        """Clear all cache entries."""
        self._data.clear()
        self._ttl.clear()
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        return {
            "size": len(self._data),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }


@pytest.fixture
async def cache() -> MockCache:
    """Create a mock cache."""
    c = MockCache()
    yield c
    await c.clear()


@pytest.fixture
async def populated_cache(cache) -> MockCache:
    """Create a cache with test data."""
    for i in range(100):
        await cache.set(f"key_{i}", f"value_{i}", ttl=3600)
    return cache


# ============================================================================
# Mock Database Fixtures
# ============================================================================


class MockDatabase:
    """Mock database for testing."""

    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._transactions: List[Dict[str, Any]] = []

    async def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert data into table."""
        if table not in self._data:
            self._data[table] = {}

        record_id = str(uuid.uuid4())
        self._data[table][record_id] = {**data, "id": record_id}
        return record_id

    async def get(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Get record by ID."""
        return self._data.get(table, {}).get(record_id)

    async def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update record."""
        if table in self._data and record_id in self._data[table]:
            self._data[table][record_id].update(data)
            return True
        return False

    async def delete(self, table: str, record_id: str) -> bool:
        """Delete record."""
        if table in self._data and record_id in self._data[table]:
            del self._data[table][record_id]
            return True
        return False

    async def query(self, table: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Query records with filters."""
        records = list(self._data.get(table, {}).values())
        if filters:
            records = [r for r in records if all(r.get(k) == v for k, v in filters.items())]
        return records


@pytest.fixture
async def database() -> MockDatabase:
    """Create a mock database."""
    db = MockDatabase()
    yield db


@pytest.fixture
async def populated_database(database) -> MockDatabase:
    """Create a database with test data."""
    # Insert agent records
    for i in range(100):
        await database.insert(
            "agents",
            {
                "name": f"agent_{i}",
                "status": "active",
                "created_at": time.time(),
            },
        )
    return database


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_target() -> Dict[str, Any]:
    """Create a sample scan target."""
    return {
        "host": "example.com",
        "port": 443,
        "protocol": "https",
        "path": "/api",
    }


@pytest.fixture
def sample_scan_config() -> Dict[str, Any]:
    """Create a sample scan configuration."""
    return {
        "scan_type": "full",
        "depth": 3,
        "threads": 10,
        "timeout": 30,
        "modules": ["portscan", "vulnscan", "webscan"],
    }


@pytest.fixture
def sample_task() -> Dict[str, Any]:
    """Create a sample task."""
    return {
        "task_id": str(uuid.uuid4()),
        "type": "port_scan",
        "target": "192.168.1.1",
        "ports": [80, 443, 8080],
        "priority": 1,
    }


@pytest.fixture
def generate_tasks() -> Callable[[int], List[Dict[str, Any]]]:
    """Factory for generating test tasks."""

    def _generate(count: int) -> List[Dict[str, Any]]:
        return [
            {
                "task_id": str(uuid.uuid4()),
                "type": random.choice(["port_scan", "vuln_scan", "web_scan"]),
                "target": f"192.168.1.{random.randint(1, 255)}",
                "priority": random.randint(1, 5),
            }
            for _ in range(count)
        ]

    return _generate


# ============================================================================
# Resource Monitoring Fixtures
# ============================================================================


@dataclass
class ResourceMonitor:
    """Monitor system resources during tests."""

    measurements: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, label: str, **metrics):
        """Record a resource measurement."""
        self.measurements.append({"timestamp": time.time(), "label": label, **metrics})

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all measurements."""
        if not self.measurements:
            return {}

        return {
            "total_measurements": len(self.measurements),
            "duration": self.measurements[-1]["timestamp"] - self.measurements[0]["timestamp"],
            "measurements": self.measurements,
        }


@pytest.fixture
def resource_monitor() -> ResourceMonitor:
    """Create a resource monitor."""
    return ResourceMonitor()


# ============================================================================
# Chaos Testing Fixtures
# ============================================================================


class ChaosEngine:
    """Engine for introducing chaos in tests."""

    def __init__(self):
        self.failures: List[str] = []
        self.network_partitions: Set[str] = set()

    async def fail_random_agents(self, agents: List[MockAgent], count: int) -> List[str]:
        """Randomly fail a number of agents."""
        to_fail = random.sample(agents, min(count, len(agents)))
        failed_ids = []
        for agent in to_fail:
            agent.status = "failed"
            failed_ids.append(agent.agent_id)
            self.failures.append(agent.agent_id)
        return failed_ids

    async def introduce_network_partition(self, agent_ids: List[str]):
        """Introduce network partition for agents."""
        for agent_id in agent_ids:
            self.network_partitions.add(agent_id)

    async def clear_network_partition(self, agent_ids: Optional[List[str]] = None):
        """Clear network partitions."""
        if agent_ids:
            for agent_id in agent_ids:
                self.network_partitions.discard(agent_id)
        else:
            self.network_partitions.clear()

    async def simulate_memory_pressure(self, agents: List[MockAgent], pressure_mb: float):
        """Simulate memory pressure on agents."""
        for agent in agents:
            agent.memory_usage += pressure_mb / len(agents)


@pytest.fixture
def chaos_engine() -> ChaosEngine:
    """Create a chaos engine."""
    return ChaosEngine()


# ============================================================================
# Performance Benchmark Fixtures
# ============================================================================


@pytest.fixture
def benchmark():
    """Simple benchmark fixture for timing operations."""

    class Benchmark:
        def __init__(self):
            self.results: List[Dict[str, float]] = []

        async def measure(self, name: str, coro) -> Any:
            """Measure execution time of a coroutine."""
            start = time.perf_counter()
            result = await coro
            elapsed = time.perf_counter() - start
            self.results.append({"name": name, "elapsed": elapsed})
            return result

        def get_report(self) -> str:
            """Get benchmark report."""
            lines = ["Benchmark Results:", "-" * 40]
            for r in self.results:
                lines.append(f"  {r['name']}: {r['elapsed']:.4f}s")
            return "\n".join(lines)

    return Benchmark()


# ============================================================================
# API Test Client Fixtures (Bestehende Fixtures)
# ============================================================================


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient

    from api.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers(test_client):
    """Get authentication headers with valid token."""
    response = test_client.post("/token", data={"username": "admin", "password": "testpass"})
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically cleanup after each test."""
    yield
    # Cleanup logic runs after each test
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
