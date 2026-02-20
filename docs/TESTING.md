# Comprehensive Testing Guide

> **Complete guide for testing Zen-AI-Pentest**

---

## Table of Contents

- [Test Structure Overview](#test-structure-overview)
- [Test Types](#test-types)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Coverage](#test-coverage)
- [Mocking Guide](#mocking-guide)
- [Test Fixtures](#test-fixtures)
- [Security Testing](#security-testing)
- [Performance Testing](#performance-testing)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting Tests](#troubleshooting-tests)

---

## Test Structure Overview

```
tests/
├── conftest.py                     # pytest configuration and fixtures
├── __init__.py
│
├── unit/                          # Unit tests (fast, isolated)
│   ├── analysis_bot/
│   ├── app/
│   ├── audit/
│   ├── core/
│   ├── dashboard/
│   ├── orchestrator/
│   ├── risk_engine/
│   ├── safety/
│   ├── scheduler/
│   └── utils/
│
├── integration/                   # Integration tests (external deps)
│   ├── conftest.py
│   ├── test_api_integration.py
│   ├── test_database_integration.py
│   └── test_full_workflow.py
│
├── e2e/                          # End-to-end tests
│   └── test_api_endpoints.py
│
├── security/                     # Security tests
│   ├── test_auth.py
│   ├── test_dast.py
│   ├── test_input_validation.py
│   └── test_sast.py
│
├── autonomous/                   # Autonomous agent tests
│   ├── test_exploit_validator.py
│   └── test_react.py
│
├── risk_engine/                  # Risk engine tests
│   └── test_scorer.py
│
├── auth/                         # Authentication tests
│   ├── test_jwt_handler.py
│   ├── test_mfa.py
│   ├── test_password_hasher.py
│   └── test_rbac.py
│
└── agent_comm/                   # Agent communication tests
    └── test_models.py
```

---

## Test Types

### 1. Unit Tests

Unit tests test individual components in isolation. They should be:
- **Fast**: Run in milliseconds
- **Isolated**: No external dependencies
- **Deterministic**: Same result every time

```python
# tests/unit/core/test_models.py
import pytest
from core.models import Scan, Finding

class TestScanModel:
    """Tests for Scan model."""
    
    def test_scan_creation(self):
        """Test creating a new scan."""
        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web"
        )
        
        assert scan.name == "Test Scan"
        assert scan.target == "example.com"
        assert scan.status == "pending"
    
    def test_scan_status_transitions(self):
        """Test scan status can be updated."""
        scan = Scan(name="Test", target="example.com")
        
        scan.status = "running"
        assert scan.status == "running"
        
        scan.status = "completed"
        assert scan.status == "completed"
    
    def test_scan_validation(self):
        """Test scan validates required fields."""
        with pytest.raises(ValueError):
            Scan(name="", target="")  # Empty values should fail
```

### 2. Integration Tests

Integration tests verify that multiple components work together:

```python
# tests/integration/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestAPIIntegration:
    """Integration tests for API."""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        return response.json()["access_token"]
    
    def test_create_scan_and_get_findings(self, auth_token):
        """Test creating a scan and retrieving findings."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create scan
        scan_response = client.post(
            "/scans",
            headers=headers,
            json={
                "name": "Integration Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "network"
            }
        )
        assert scan_response.status_code == 201
        scan_id = scan_response.json()["id"]
        
        # Get scan details
        get_response = client.get(f"/scans/{scan_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Integration Test Scan"
```

### 3. E2E Tests

End-to-end tests verify complete workflows:

```python
# tests/e2e/test_api_endpoints.py
import pytest
import time
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestEndToEndWorkflow:
    """E2E tests for complete workflows."""
    
    def test_complete_scan_workflow(self):
        """Test a complete scan from start to finish."""
        # 1. Login
        auth_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create scan
        scan_response = client.post(
            "/scans",
            headers=headers,
            json={
                "name": "E2E Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "quick"
            }
        )
        scan_id = scan_response.json()["id"]
        
        # 3. Wait for completion (with timeout)
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = client.get(
                f"/scans/{scan_id}",
                headers=headers
            )
            status = status_response.json()["status"]
            
            if status in ["completed", "failed"]:
                break
            
            time.sleep(5)
        
        # 4. Verify results
        assert status == "completed"
        
        findings = client.get(
            f"/scans/{scan_id}/findings",
            headers=headers
        ).json()
        
        assert isinstance(findings, list)
```

### 4. Security Tests

Security tests verify security controls:

```python
# tests/security/test_input_validation.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestInputValidation:
    """Tests for input validation and security."""
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection is blocked."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; DELETE FROM scans",
        ]
        
        for malicious in malicious_inputs:
            response = client.post(
                "/auth/login",
                json={
                    "username": malicious,
                    "password": "password"
                }
            )
            # Should not crash or expose data
            assert response.status_code in [400, 401, 422]
    
    def test_xss_prevention(self):
        """Test that XSS is blocked."""
        xss_payload = "<script>alert('xss')</script>"
        
        response = client.post(
            "/scans",
            headers={"Authorization": "Bearer valid_token"},
            json={
                "name": xss_payload,
                "target": "example.com"
            }
        )
        
        # Response should not contain unescaped script
        assert "<script>" not in response.text
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with very verbose output
pytest -vv

# Run specific test file
pytest tests/unit/core/test_models.py

# Run specific test class
pytest tests/unit/core/test_models.py::TestScanModel

# Run specific test method
pytest tests/unit/core/test_models.py::TestScanModel::test_scan_creation

# Run tests matching pattern
pytest -k "test_scan"

# Run tests excluding pattern
pytest -k "not slow"
```

### Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Security tests
pytest tests/security/ -v

# E2E tests
pytest tests/e2e/ -v

# Autonomous agent tests
pytest tests/autonomous/ -v
```

### Coverage Commands

```bash
# Run with coverage
pytest --cov=. --cov-report=term

# Generate HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Generate XML report (for CI)
pytest --cov=. --cov-report=xml

# Show missing lines
pytest --cov=. --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=. --cov-fail-under=80
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (auto-detect cores)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

---

## Writing Tests

### Test Structure (Arrange-Act-Assert)

```python
def test_example():
    """Test description following AAA pattern."""
    # Arrange - Setup
    input_data = {"key": "value"}
    expected_output = {"result": "success"}
    
    # Act - Execute
    result = process_data(input_data)
    
    # Assert - Verify
    assert result == expected_output
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_process("data")
    assert result is not None

@pytest.mark.asyncio
async def test_async_with_fixture(async_client):
    """Test using async fixture."""
    response = await async_client.get("/scans")
    assert response.status_code == 200
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("192.168.1.1", False),    # Private IP blocked
    ("10.0.0.1", False),       # Private IP blocked
    ("scanme.nmap.org", True), # Public allowed
    ("8.8.8.8", True),         # Public allowed
])
def test_ip_validation(input, expected):
    """Test IP validation with various inputs."""
    result = validate_target(input)
    assert result == expected

@pytest.mark.parametrize("severity,expected_color", [
    ("critical", "red"),
    ("high", "orange"),
    ("medium", "yellow"),
    ("low", "blue"),
    ("info", "gray"),
])
def test_severity_colors(severity, expected_color):
    """Test severity color mapping."""
    assert get_severity_color(severity) == expected_color
```

### Test Classes

```python
import pytest

class TestToolIntegration:
    """Tests for tool integration."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for all tests in class."""
        self.tool = ToolIntegration()
        yield
        # Teardown
        self.tool.cleanup()
    
    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        assert self.tool is not None
        assert self.tool.timeout == 300
    
    def test_tool_execution(self):
        """Test tool executes successfully."""
        result = self.tool.run("example.com")
        assert result.success is True
```

### Fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from api.main import app, get_db

# Database fixture
@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db_engine):
    """Create database session."""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

# API client fixture
@pytest.fixture
def client(db_session):
    """Create test client with test DB."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

# Authentication fixture
@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Sample data fixtures
@pytest.fixture
def sample_scan_data():
    """Return sample scan data."""
    return {
        "name": "Test Scan",
        "target": "example.com",
        "scan_type": "web"
    }

@pytest.fixture
def sample_finding_data():
    """Return sample finding data."""
    return {
        "title": "Test Finding",
        "severity": "high",
        "description": "Test description"
    }
```

---

## Test Coverage

### Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| Core modules | 85% |
| API endpoints | 80% |
| Tool integrations | 75% |
| Security/guardrails | 100% |
| Database models | 80% |
| Risk engine | 90% |

### Coverage Configuration

```ini
# .coveragerc
[run]
source = .
omit = 
    tests/*
    venv/*
    */site-packages/*
    */__pycache__/*
    scripts/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = htmlcov
```

### Checking Coverage

```bash
# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Example output:
# Name                           Stmts   Miss  Cover   Missing
# ------------------------------------------------------------
# api/main.py                       50      5    90%   45-50
# tools/nmap.py                    100     20    80%   30-50, 80-90
# ------------------------------------------------------------
# TOTAL                           1000    100    90%
```

---

## Mocking Guide

### Basic Mocking

```python
from unittest.mock import Mock, patch, MagicMock
import pytest

def test_with_mock():
    """Test using mocks."""
    # Create mock
    mock_tool = Mock()
    mock_tool.execute.return_value = {"status": "success"}
    
    # Use mock
    result = mock_tool.execute("target")
    assert result["status"] == "success"
    mock_tool.execute.assert_called_once_with("target")
```

### Patching

```python
from unittest.mock import patch
import pytest

# Patch at module level
@patch("tools.nmap_integration.subprocess.run")
def test_nmap_with_mock(mock_run):
    """Test nmap with mocked subprocess."""
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = b"<xml>test</xml>"
    
    from tools.nmap_integration import NmapScanner
    scanner = NmapScanner()
    result = scanner.scan("example.com")
    
    assert result is not None
    mock_run.assert_called_once()

# Patch multiple
@patch("tools.nmap_integration.subprocess.run")
@patch("tools.nmap_integration.parse_xml")
def test_nmap_with_multiple_mocks(mock_parse, mock_run):
    """Test with multiple mocks."""
    mock_run.return_value.returncode = 0
    mock_parse.return_value = {"ports": [80, 443]}
    
    from tools.nmap_integration import NmapScanner
    scanner = NmapScanner()
    result = scanner.scan("example.com")
    
    assert result["ports"] == [80, 443]
```

### Async Mocking

```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
@patch("tools.nmap_integration.async_subprocess")
async def test_async_tool(mock_subprocess):
    """Test async tool with mocking."""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"output", b"")
    mock_process.returncode = 0
    
    mock_subprocess.create_subprocess_exec.return_value = mock_process
    
    from tools.nmap_integration import NmapScanner
    scanner = NmapScanner()
    result = await scanner.scan_async("example.com")
    
    assert result is not None
```

### Mocking External APIs

```python
from unittest.mock import patch, Mock
import pytest
import httpx

@pytest.fixture
def mock_kimi_response():
    """Create mock Kimi API response."""
    return {
        "choices": [{
            "message": {
                "content": "Analysis complete"
            }
        }]
    }

@patch("httpx.AsyncClient.post")
async def test_kimi_integration(mock_post, mock_kimi_response):
    """Test Kimi API integration with mock."""
    mock_post.return_value = Mock(
        status_code=200,
        json=Mock(return_value=mock_kimi_response)
    )
    
    from backends.kimi_backend import KimiBackend
    backend = KimiBackend()
    result = await backend.analyze("test data")
    
    assert "Analysis" in result
```

---

## Test Fixtures

### Fixture Scopes

```python
import pytest

@pytest.fixture(scope="function")
def function_fixture():
    """Runs once per test function (default)."""
    print("Setup function")
    yield "data"
    print("Teardown function")

@pytest.fixture(scope="class")
def class_fixture():
    """Runs once per test class."""
    print("Setup class")
    yield "class_data"
    print("Teardown class")

@pytest.fixture(scope="module")
def module_fixture():
    """Runs once per module."""
    print("Setup module")
    yield "module_data"
    print("Teardown module")

@pytest.fixture(scope="session")
def session_fixture():
    """Runs once per test session."""
    print("Setup session")
    yield "session_data"
    print("Teardown session")
```

### Factory Fixtures

```python
import pytest
from database.models import Scan, Finding

@pytest.fixture
def create_scan(db_session):
    """Factory fixture for creating scans."""
    def _create_scan(**kwargs):
        scan = Scan(
            name=kwargs.get("name", "Test Scan"),
            target=kwargs.get("target", "example.com"),
            status=kwargs.get("status", "pending")
        )
        db_session.add(scan)
        db_session.commit()
        return scan
    return _create_scan

# Usage
def test_with_scan(create_scan):
    """Test using factory fixture."""
    scan = create_scan(name="Custom Scan", target="test.com")
    assert scan.name == "Custom Scan"
```

### Temporary Files

```python
import pytest
import tempfile
import os

@pytest.fixture
def temp_file():
    """Create temporary file."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

def test_file_processing(temp_file):
    """Test file processing with temp file."""
    with open(temp_file, 'w') as f:
        f.write("test data")
    
    result = process_file(temp_file)
    assert result is not None
```

---

## Security Testing

### SAST (Static Analysis)

```bash
# Run Bandit
bandit -r . -ll -ii

# Run with configuration
bandit -r . -c bandit.yaml

# Generate report
bandit -r . -f json -o bandit-report.json
```

### DAST (Dynamic Analysis)

```python
# tests/security/test_dast.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestDAST:
    """Dynamic application security tests."""
    
    def test_authentication_required(self):
        """Test endpoints require authentication."""
        protected_endpoints = [
            "/scans",
            "/findings",
            "/reports",
            "/tools/execute"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_rate_limiting(self):
        """Test rate limiting is enforced."""
        # Make many requests quickly
        for _ in range(150):
            response = client.get("/health")
        
        # Should be rate limited
        assert response.status_code == 429
    
    def test_sql_injection_prevention(self):
        """Test SQL injection protection."""
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.post(
            "/auth/login",
            json={
                "username": malicious_input,
                "password": malicious_input
            }
        )
        
        # Should not crash or succeed
        assert response.status_code in [400, 401, 422]
```

### Dependency Checking

```bash
# Run safety check
safety check -r requirements.txt

# Run with full report
safety check -r requirements.txt --json

# Check specific package
safety check -i 12345  # Ignore specific vulnerability
```

---

## Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Login on start."""
        response = self.client.post("/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        self.token = response.json()["access_token"]
    
    @task(10)
    def get_scans(self):
        """Get scans list."""
        self.client.get(
            "/scans",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(5)
    def create_scan(self):
        """Create new scan."""
        self.client.post(
            "/scans",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Load Test Scan",
                "target": "example.com",
                "scan_type": "quick"
            }
        )
    
    @task(1)
    def health_check(self):
        """Check health."""
        self.client.get("/health")
```

Run with:
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Benchmark Tests

```python
# tests/unit/utils/test_helpers.py
import pytest
import time

class TestPerformance:
    """Performance tests."""
    
    def test_scan_creation_performance(self, client, auth_headers):
        """Test scan creation completes in reasonable time."""
        start = time.time()
        
        response = client.post(
            "/scans",
            headers=auth_headers,
            json={
                "name": "Perf Test",
                "target": "example.com"
            }
        )
        
        elapsed = time.time() - start
        
        assert response.status_code == 201
        assert elapsed < 1.0  # Should complete in under 1 second
```

---

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run linting
      run: |
        ruff check .
        black --check .
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Troubleshooting Tests

### Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Ensure `__init__.py` exists in test directories |
| Database locked | Use separate test database, not SQLite in-memory |
| Async tests fail | Install `pytest-asyncio`, use `@pytest.mark.asyncio` |
| Fixtures not found | Check `conftest.py` is in correct directory |
| Slow tests | Use `-m "not slow"` to exclude, or optimize fixtures |

### Debug Mode

```bash
# Run with debugger on failure
pytest --pdb

# Run with full traceback
pytest --tb=long

# Run with local variables in traceback
pytest --tb=long --showlocals

# Capture output even on success
pytest -s

# Capture log output
pytest --log-cli-level=DEBUG
```

### Test Isolation

```python
# Ensure test isolation with fresh fixtures
@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test."""
    # Clear caches
    cache.clear()
    # Reset singletons
    ToolRegistry.reset()
    yield
```

---

<p align="center">
  <b>Write tests, not bugs! 🧪</b><br>
  <sub>See <a href="../CONTRIBUTING.md">CONTRIBUTING.md</a> for coverage requirements</sub>
</p>
