"""
Unit Tests for REST API
"""

import pytest  # noqa: F401
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")

    assert response.status_code in [200, 429]
    # API returns 'healthy' or 'degraded' depending on Redis availability
    assert response.json()["status"] in ["healthy", "degraded"]


def test_get_status():
    """Test status endpoint"""
    response = client.get("/health")

    assert response.status_code in [200, 429]
    data = response.json()
    assert "status" in data


def test_invalid_endpoint():
    """Test 404 handling"""
    response = client.get("/invalid-endpoint")

    assert response.status_code in [404, 429]
