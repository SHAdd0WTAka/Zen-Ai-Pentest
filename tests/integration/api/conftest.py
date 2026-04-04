"""
Pytest configuration and shared fixtures for API integration tests
"""

import os
import sys

import pytest

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "auth: marks tests as authentication tests")
    config.addinivalue_line("markers", "scan: marks tests as scan endpoint tests")
    config.addinivalue_line("markers", "finding: marks tests as finding endpoint tests")
    config.addinivalue_line("markers", "report: marks tests as report endpoint tests")
    config.addinivalue_line("markers", "dashboard: marks tests as dashboard endpoint tests")
    config.addinivalue_line("markers", "websocket: marks tests as websocket tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test name patterns
        if "auth" in item.nodeid.lower():
            item.add_marker(pytest.mark.auth)
        if "scan" in item.nodeid.lower():
            item.add_marker(pytest.mark.scan)
        if "finding" in item.nodeid.lower():
            item.add_marker(pytest.mark.finding)
        if "report" in item.nodeid.lower():
            item.add_marker(pytest.mark.report)
        if "dashboard" in item.nodeid.lower():
            item.add_marker(pytest.mark.dashboard)
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        if "security" in item.nodeid.lower():
            item.add_marker(pytest.mark.security)
        if "websocket" in item.nodeid.lower() or "ws" in item.nodeid.lower():
            item.add_marker(pytest.mark.websocket)
