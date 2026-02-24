# Testing Guide

Umfassender Guide zum Testen von Zen-AI-Pentest.

## Test-Struktur

```
tests/
├── unit/              # Unit Tests
│   ├── core/
│   ├── agents/
│   └── tools/
├── integration/       # Integration Tests
├── e2e/              # End-to-End Tests
├── fixtures/         # Test Daten
└── conftest.py       # pytest Konfiguration
```

## Test-Typen

### 1. Unit Tests

Testen einzelne Funktionen/Klassen isoliert.

```python
# tests/unit/tools/test_nmap.py
import pytest
from unittest.mock import Mock, patch
from tools.nmap import NmapScanner

@pytest.fixture
def scanner():
    return NmapScanner(timeout=5)

@pytest.mark.asyncio
async def test_scan_single_port(scanner):
    """Test scanning a single port."""
    with patch("tools.nmap.asyncio.create_subprocess_exec") as mock_exec:
        mock_exec.return_value = Mock(
            communicate=Mock(return_value=(b"80/tcp open", b"")),
            returncode=0
        )

        result = await scanner.scan_port("127.0.0.1", 80)
        assert result["port"] == 80
        assert result["state"] == "open"

def test_parse_nmap_output():
    """Test XML output parsing."""
    xml_output = """<?xml version="1.0"?>
    <nmaprun>
        <host>
            <ports>
                <port portid="80">
                    <state state="open"/>
                </port>
            </ports>
        </host>
    </nmaprun>"""

    result = NmapScanner.parse_output(xml_output)
    assert 80 in result["open_ports"]
```

### 2. Integration Tests

Testen Zusammenspiel mehrerer Komponenten.

```python
# tests/integration/test_agent_workflow.py
import pytest
from agents.coordinator import AgentCoordinator
from agents.recon import ReconAgent

@pytest.mark.asyncio
async def test_full_recon_workflow():
    """Test complete reconnaissance workflow."""
    coordinator = AgentCoordinator()
    agent = ReconAgent()

    result = await coordinator.execute(agent, target="scanme.nmap.org")

    assert result["status"] == "completed"
    assert "subdomains" in result["data"]
    assert "ports" in result["data"]
```

### 3. End-to-End Tests

Testen komplette User-Journeys.

```python
# tests/e2e/test_api_scan.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_and_run_scan():
    """Test complete scan lifecycle via API."""
    # Login
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "test"
    })
    token = response.json()["access_token"]

    # Create scan
    response = client.post(
        "/api/v1/scans",
        headers={"Authorization": f"Bearer {token}"},
        json={"target": "scanme.nmap.org", "type": "recon"}
    )
    assert response.status_code == 201
    scan_id = response.json()["id"]

    # Get results
    response = client.get(
        f"/api/v1/scans/{scan_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

## Fixtures

### conftest.py

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from core.config import settings

# Database fixture
@pytest.fixture(scope="session")
def engine():
    return create_engine(settings.DATABASE_URL)

@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

# Mock fixtures
@pytest.fixture
def mock_openai():
    with patch("agents.llm.OpenAI") as mock:
        mock.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response"))]
        )
        yield mock
```

## Test-Befehle

### Alle Tests

```bash
pytest
```

### Mit Coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

### Spezifische Tests

```bash
# Einzelne Datei
pytest tests/unit/tools/test_nmap.py

# Einzelner Test
pytest tests/unit/tools/test_nmap.py::test_scan_single_port

# Pattern
pytest -k "test_scan"
```

### Parallel

```bash
pytest -n auto
```

### Mit Debugging

```bash
pytest --pdb
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb
```

## Mocking

### Tools mocken

```python
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mocked_tool():
    """Test with mocked nmap."""
    with patch("tools.nmap.NmapScanner.scan") as mock_scan:
        mock_scan.return_value = {
            "open_ports": [80, 443],
            "scan_time": 5.2
        }

        result = await run_scan("example.com")
        assert result["open_ports"] == [80, 443]
```

### LLM Responses mocken

```python
@pytest.fixture
def mock_llm_response():
    return {
        "content": """
        Based on the scan results:
        - Port 80: Open (Apache)
        - Port 443: Open (Nginx)

        Recommendations:
        1. Update Apache
        2. Enable HSTS
        """,
        "model": "kimi-k2.5"
    }
```

## Performance Tests

### Benchmarks

```python
# tests/benchmarks/test_scan_speed.py
import pytest
import time

@pytest.mark.benchmark
class TestScanPerformance:

    @pytest.mark.asyncio
    async def test_port_scan_speed(self):
        """Port scan should complete in < 10 seconds."""
        scanner = PortScanner()

        start = time.time()
        await scanner.scan("scanme.nmap.org", ports=[22, 80, 443])
        duration = time.time() - start

        assert duration < 10.0, f"Scan took {duration}s, expected < 10s"

    def test_memory_usage(self):
        """Memory usage should stay below 500MB."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Run scan
        run_large_scan()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        assert memory_increase < 500, f"Memory increased by {memory_increase}MB"
```

## Security Tests

### Input Validation

```python
def test_sql_injection_protection():
    """Test that inputs are properly sanitized."""
    malicious_input = "'; DROP TABLE users; --"

    with pytest.raises(ValueError):
        validate_target(malicious_input)

def test_xss_protection():
    """Test XSS prevention."""
    malicious = "<script>alert('xss')</script>"

    result = sanitize_input(malicious)
    assert "<script>" not in result
```

## CI Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Test-Daten

### Fixtures

```python
# tests/fixtures/scans.py
SAMPLE_SCAN_RESULT = {
    "target": "example.com",
    "open_ports": [80, 443],
    "technologies": ["nginx", "PHP"],
    "vulnerabilities": []
}

SAMPLE_VULNERABILITY = {
    "cve": "CVE-2021-44228",
    "severity": "critical",
    "description": "Log4j RCE"
}
```

## Tipps

### 1. Tests sollten unabhängig sein

```python
# ❌ Schlecht
def test_a():
    global data
    data = create_data()

def test_b():
    assert data is not None  # Abhängig von test_a

# ✅ Gut
@pytest.fixture
def data():
    return create_data()

def test_a(data):
    assert data.valid

def test_b(data):
    assert data.complete
```

### 2. Beschreibende Namen

```python
# ❌ Schlecht
def test1():
    pass

# ✅ Gut
def test_user_authentication_with_valid_credentials():
    pass
```

### 3. Ein Assert pro Test (ideal)

```python
# ❌ Schlecht
def test_user():
    user = create_user()
    assert user.name == "Test"
    assert user.email == "test@test.com"
    assert user.active

# ✅ Gut
def test_user_has_correct_name():
    assert create_user().name == "Test"

def test_user_has_correct_email():
    assert create_user().email == "test@test.com"
```
