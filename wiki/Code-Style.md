# Code Style Guide

Dieser Guide definiert die Coding Standards für Zen-AI-Pentest.

## Allgemeine Prinzipien

- **PEP 8** - Python Style Guide
- **DRY** - Don't Repeat Yourself
- **KISS** - Keep It Simple, Stupid
- **Explicit is better than implicit**

## Formatierung

### Black

Wir verwenden **Black** für automatische Formatierung:

```bash
# Einzelne Datei
black myfile.py

# Alle Dateien
black .

# Check (ohne Änderung)
black --check .
```

**Konfiguration:**
```toml
# pyproject.toml
[tool.black]
line-length = 79
target-version = ['py311']
```

### Zeilenlänge

- **Maximum:** 79 Zeichen
- **Docstrings:** 72 Zeichen

### Imports

**Reihenfolge:**
1. Standard Library
2. Third Party
3. Local/Application

**Beispiel:**
```python
# Standard Library
import os
import sys
from pathlib import Path

# Third Party
import yaml
from fastapi import FastAPI

# Local
from core.config import settings
from agents.base import BaseAgent
```

**isort** verwenden:
```bash
isort .
```

## Docstrings

### Google Style

```python
def scan_target(target: str, ports: list[int] = None) -> dict:
    """Scan a target for open ports and vulnerabilities.

    Args:
        target: The target hostname or IP address.
        ports: List of ports to scan. Defaults to common ports.

    Returns:
        Dictionary containing scan results with keys:
        - open_ports: List of open ports
        - vulnerabilities: List of found vulnerabilities
        - scan_time: Duration in seconds

    Raises:
        ValueError: If target is invalid or unreachable.
        ConnectionError: If target refuses connection.

    Example:
        >>> result = scan_target("example.com", [80, 443])
        >>> print(result["open_ports"])
        [80, 443]
    """
```

### PEP 257

- Triple double quotes: `"""`
- Erste Zeile: Kurze Zusammenfassung
- Zweite Zeile: Leer
- Details folgen

## Typisierung

### Type Hints

**Immer verwenden:**

```python
from typing import Optional, List, Dict, Union

def process_scan(
    target: str,
    ports: List[int],
    timeout: Optional[int] = None
) -> Dict[str, Union[List[int], str]]:
    """Process a scan request."""
    pass
```

### mypy

```bash
# Type Checking
mypy .

# Strict Mode
mypy --strict .
```

## Naming Conventions

| Element | Konvention | Beispiel |
|---------|-----------|----------|
| Module | snake_case | `scan_engine.py` |
| Klassen | PascalCase | `ScanEngine` |
| Funktionen | snake_case | `run_scan()` |
| Variablen | snake_case | `scan_result` |
| Konstanten | UPPER_CASE | `MAX_TIMEOUT` |
| Private | _leading_underscore | `_internal_method()` |

## Kommentare

### Gute Kommentare

```python
# Berechne CVSS Score basierend auf Impact und Exploitability
cvss = (impact * 0.6) + (exploitability * 0.4)

# Warte auf Docker Container Start (max 30 Sekunden)
for _ in range(30):
    if container.is_running():
        break
    time.sleep(1)
```

### Schlechte Kommentare

```python
# Berechne CVSS
cvss = (impact * 0.6) + (exploitability * 0.4)

# Loop
for _ in range(30):
    pass
```

## Fehlerbehandlung

### Exceptions

```python
# Spezifische Exceptions fangen
try:
    result = scan_target(target)
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise ScanError(f"Cannot connect to {target}")
except TimeoutError:
    logger.warning(f"Scan timeout for {target}")
    return {"status": "timeout"}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Levels
logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")
```

## Tests

### pytest

```python
# test_scanner.py
import pytest
from modules.scanner import PortScanner

@pytest.fixture
def scanner():
    return PortScanner(timeout=5)

@pytest.mark.asyncio
async def test_scan_opens_ports(scanner):
    """Test that scanner finds open ports."""
    result = await scanner.scan("127.0.0.1", ports=[22, 80])
    assert isinstance(result, dict)
    assert "open_ports" in result

@pytest.mark.parametrize("port,expected", [
    (22, True),
    (99999, False),
])
def test_port_validation(scanner, port, expected):
    """Test port number validation."""
    assert scanner.is_valid_port(port) == expected
```

## Security

### Nie in Code einchecken

```python
# ❌ FALSCH
API_KEY = "sk-1234567890abcdef"

# ✅ RICHTIG
from core.config import settings
API_KEY = settings.api_key
```

### Input Validierung

```python
from pydantic import BaseModel, validator

class ScanRequest(BaseModel):
    target: str
    ports: List[int]

    @validator("target")
    def validate_target(cls, v):
        if not v or len(v) > 253:
            raise ValueError("Invalid target")
        return v

    @validator("ports")
    def validate_ports(cls, v):
        if not all(0 < p < 65536 for p in v):
            raise ValueError("Invalid port number")
        return v
```

## Pre-commit

Alle Checks müssen passing sein:

```bash
# Vor Commit
pre-commit run --all-files

# Einzelne Hooks
pre-commit run black
pre-commit run flake8
pre-commit run mypy
```

## Linting

### flake8

```bash
flake8 . --max-line-length=79 --max-complexity=10
```

### bandit (Security)

```bash
bandit -r . -f json -o bandit-report.json
```

## Ressourcen

- [PEP 8](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black Documentation](https://black.readthedocs.io/)
