# Testing Guide

This document describes the testing framework and how to run tests for Zen-AI-Pentest.

## Test Framework

We use **pytest** as our primary testing framework with the following plugins:
- `pytest-cov` - Code coverage
- `pytest-asyncio` - Async test support

## Test Structure

```
tests/
├── conftest.py              # pytest configuration and fixtures
├── unit/                    # Unit tests
│   ├── test_react_agent.py
│   ├── test_tool_registry.py
│   └── ...
├── integration/             # Integration tests
│   ├── test_api.py
│   └── ...
├── autonomous/              # Autonomous agent tests
├── risk_engine/             # Risk engine tests
└── cloud/                   # Cloud provider tests
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

### Run Specific Test File

```bash
pytest tests/unit/test_react_agent.py -v
```

### Run Only Unit Tests

```bash
pytest tests/unit/ -v
```

### Run Only Integration Tests

```bash
pytest tests/integration/ -v
```

### Run Tests Without Slow Tests

```bash
pytest -m "not slow"
```

## Test Categories

We use markers to categorize tests:

- `unit` - Fast unit tests
- `integration` - Integration tests requiring external resources
- `slow` - Tests that take longer than 10 seconds
- `security` - Security-related tests

## Writing Tests

### Basic Test Structure

```python
def test_feature():
    """Test description."""
    # Arrange
    input_data = "test"

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_feature():
    result = await async_function()
    assert result is not None
```

### Fixtures

```python
import pytest

@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

## Continuous Integration

All tests run automatically via GitHub Actions on:
- Every push to `main`, `master`, or `develop`
- Every pull request
- Python versions: 3.11, 3.12, 3.13

## Code Coverage

We track code coverage via Codecov. Current coverage: **3%** (work in progress).

Target: **50%** minimum for Silver badge compliance.

## Security Testing

Security tests include:
- Bandit static analysis
- Safety dependency checking
- Custom security test cases

Run security tests:
```bash
bandit -r . -ll
safety check
```

## Test Data

Test data is stored in `tests/data/` and should:
- Not contain real credentials
- Use example.com for test URLs
- Be as small as possible

## Reporting Test Failures

If you encounter test failures:
1. Check if it's an environment issue
2. Run with verbose output: `pytest -v --tb=long`
3. Report issues with full traceback

---

For more information, see our [Contributing Guide](../CONTRIBUTING.md).
