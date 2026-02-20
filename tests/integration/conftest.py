"""
Integration Test Configuration

Fixtures and configuration for integration tests.
"""

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_task_callback():
    """Mock task callback for testing"""

    async def callback(task_data):
        await asyncio.sleep(0.01)  # Simulate work
        return {"status": "completed", "results": {"findings": []}, "execution_time": 0.01}

    return callback


@pytest.fixture
def sample_vulnerability_data():
    """Sample vulnerability data for testing"""
    return {
        "id": "CVE-2024-1234",
        "title": "Test Vulnerability",
        "severity": "high",
        "cvss_score": 8.5,
        "description": "Test vulnerability for integration testing",
        "affected_component": "test-service",
        "remediation": "Update to latest version",
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "type": "vulnerability_scan",
        "target": "test.example.com",
        "options": {"ports": "80,443,8080", "scan_type": "quick"},
    }


@pytest.fixture
def sample_cron_schedules():
    """Sample cron schedules for testing"""
    return {"daily": "0 2 * * *", "hourly": "0 * * * *", "weekly": "0 0 * * 0", "every_5_minutes": "*/5 * * * *"}


# Markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test location
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
