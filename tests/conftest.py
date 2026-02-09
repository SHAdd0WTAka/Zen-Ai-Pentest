"""
Pytest configuration and shared fixtures for Zen AI Pentest tests.

This module provides:
- Mock fixtures for external dependencies
- Test data fixtures
- Common testing utilities
"""

import asyncio
import os
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List

# Ensure we're in test mode
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")


# ==================== Event Loop Fixture ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ==================== Mock External Services ====================

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for LLM tests"""
    client = Mock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response from LLM"))]
    )
    return client


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession"""
    session = AsyncMock()
    response = AsyncMock()
    response.status = 200
    response.json.return_value = {"result": "success"}
    response.text.return_value = "test response"
    session.get.return_value.__aenter__ = AsyncMock(return_value=response)
    session.post.return_value.__aenter__ = AsyncMock(return_value=response)
    return session


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = AsyncMock()
    client.get.return_value = None
    client.set.return_value = True
    client.delete.return_value = True
    client.exists.return_value = 0
    client.flushdb.return_value = True
    return client


# ==================== Database Fixtures ====================

@pytest.fixture
def temp_db_path():
    """Create a temporary database file"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


# ==================== Test Data Fixtures ====================

@pytest.fixture
def sample_cve_data():
    """Sample CVE data for testing"""
    return {
        "id": "CVE-2023-1234",
        "severity": "HIGH",
        "cvss_score": 8.5,
        "description": "Test vulnerability for unit testing",
        "published": "2023-01-01T00:00:00Z",
        "modified": "2023-01-15T00:00:00Z",
        "references": ["https://example.com/cve-2023-1234"],
    }


@pytest.fixture
def sample_finding_data():
    """Sample security finding data"""
    return {
        "id": "finding-001",
        "title": "SQL Injection",
        "description": "SQL injection vulnerability in login form",
        "severity": "critical",
        "target": "https://example.com/login",
        "source": "sqlmap",
        "cvss_score": 9.8,
        "cve_id": "CVE-2023-1234",
        "evidence": {
            "payload": "' OR '1'='1",
            "response": "Database error",
        },
        "remediation": "Use parameterized queries",
        "discovered_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_scan_config():
    """Sample scan configuration"""
    return {
        "target": "scanme.nmap.org",
        "scan_type": "full",
        "ports": "1-65535",
        "intensity": "aggressive",
        "timeout": 3600,
        "options": {
            "service_detection": True,
            "os_detection": False,
            "script_scan": "default",
        },
    }


@pytest.fixture
def sample_user_data():
    """Sample user data"""
    return {
        "id": "user-001",
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_target_data():
    """Sample target data"""
    return {
        "id": "target-001",
        "name": "Test Target",
        "host": "192.168.1.1",
        "type": "server",
        "description": "Test server for scanning",
    }


# ==================== Orchestrator Fixtures ====================

@pytest.fixture
def mock_backend():
    """Mock LLM backend for orchestrator tests"""
    backend = Mock()
    backend.name = "mock_backend"
    backend.priority = 1
    backend.chat = AsyncMock(return_value="Mock response")
    backend.health_check = AsyncMock(return_value=True)
    return backend


@pytest.fixture
def mock_failing_backend():
    """Mock failing LLM backend"""
    backend = Mock()
    backend.name = "failing_backend"
    backend.priority = 2
    backend.chat = AsyncMock(side_effect=Exception("Backend failed"))
    backend.health_check = AsyncMock(return_value=False)
    return backend


# ==================== Plugin Fixtures ====================

@pytest.fixture
def temp_plugin_dir():
    """Create a temporary plugin directory"""
    temp_dir = tempfile.mkdtemp(prefix="test_plugins_")
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_plugin():
    """Mock plugin for testing"""
    plugin = Mock()
    plugin.NAME = "test_plugin"
    plugin.VERSION = "1.0.0"
    plugin.PLUGIN_TYPE = "scanner"
    plugin.initialize = AsyncMock(return_value=True)
    plugin.execute = AsyncMock(return_value={"status": "success"})
    plugin.shutdown = AsyncMock()
    plugin.validate_config = Mock(return_value=True)
    plugin.get_info.return_value = Mock(
        name="test_plugin",
        version="1.0.0",
        plugin_type="scanner",
    )
    return plugin


# ==================== Cache Fixtures ====================

@pytest.fixture
async def memory_cache():
    """Create a fresh memory cache"""
    from core.cache import MemoryCache
    cache = MemoryCache(max_size=100)
    yield cache
    await cache.clear()


@pytest.fixture
async def sqlite_cache(temp_db_path):
    """Create a fresh SQLite cache"""
    from core.cache import SQLiteCache
    cache = SQLiteCache(db_path=temp_db_path)
    yield cache
    await cache.clear()
    await cache.close()


# ==================== Rate Limiter Fixtures ====================

@pytest.fixture
def rate_limit_config():
    """Default rate limit configuration"""
    from core.rate_limiter import RateLimitConfig
    return RateLimitConfig(
        requests_per_second=10.0,
        burst_size=5,
        max_retries=3,
    )


@pytest.fixture
def circuit_breaker_config():
    """Default circuit breaker configuration"""
    from core.rate_limiter import CircuitBreakerConfig
    return CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        half_open_max_calls=3,
    )


# ==================== Container Fixtures ====================

@pytest.fixture
def fresh_container():
    """Create a fresh dependency injection container"""
    from core.container import Container
    return Container()


# ==================== Authentication Fixtures ====================

@pytest.fixture
def mock_token_payload():
    """Mock JWT token payload"""
    return {
        "sub": "user-001",
        "username": "testuser",
        "role": "user",
        "exp": datetime.utcnow().timestamp() + 3600,
        "type": "access",
    }


# ==================== File System Fixtures ====================

@pytest.fixture
def temp_directory():
    """Create a temporary directory for file operations"""
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="zen_test_")
    yield Path(temp_dir)
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_report_data():
    """Sample report data"""
    return {
        "id": "report-001",
        "name": "Test Security Report",
        "scan_id": "scan-001",
        "format": "pdf",
        "status": "completed",
        "findings": [
            {
                "title": "SQL Injection",
                "severity": "critical",
                "description": "Test finding",
            }
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }


# ==================== Async Helpers ====================

@pytest.fixture
def async_return():
    """Helper to create async return values"""
    def _async_return(value):
        async def _inner(*args, **kwargs):
            return value
        return _inner
    return _async_return


# ==================== Monkey Patches ====================

@pytest.fixture(autouse=True)
def mock_sleep():
    """Mock asyncio.sleep to speed up tests"""
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock:
        yield mock


# ==================== Custom Markers ====================

def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
    config.addinivalue_line("markers", "core: marks tests as core module tests")


# ==================== Test Result Hooks ====================

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on path"""
    for item in items:
        # Add core marker for core module tests
        if "test_core_" in item.nodeid:
            item.add_marker(pytest.mark.core)
        # Add api marker for API tests
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        # Add unit marker if no other markers
        if not any(mark.name in ["integration", "slow", "security"] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# ==================== Assertion Helpers ====================

class TestHelpers:
    """Helper methods for tests"""
    
    @staticmethod
    def assert_valid_uuid(value: str) -> bool:
        """Check if value is a valid UUID"""
        import uuid
        try:
            uuid.UUID(str(value))
            return True
        except ValueError:
            return False
    
    @staticmethod
    def assert_valid_iso_timestamp(value: str) -> bool:
        """Check if value is a valid ISO timestamp"""
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False


@pytest.fixture
def test_helpers():
    """Provide test helpers"""
    return TestHelpers
