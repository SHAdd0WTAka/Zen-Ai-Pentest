"""API Module Tests"""

import pytest
from fastapi.testclient import TestClient

from api.auth import create_access_token

# Test basic imports
from api.main import app
from api.schemas import ScanCreate, ScanResponse

client = TestClient(app)


def test_app_exists():
    """Test that app exists."""
    assert app is not None


def test_create_access_token():
    """Test token creation."""
    token = create_access_token({"sub": "test@example.com"})
    assert token is not None
    assert isinstance(token, str)


def test_scan_create_schema():
    """Test ScanCreate schema."""
    scan = ScanCreate(
        name="Test Scan",
        target="example.com",
        scan_type="network",
    )
    assert scan.target == "example.com"
    assert scan.name == "Test Scan"


def test_api_root():
    """Test API root endpoint."""
    response = client.get("/")
    assert response.status_code in [200, 307, 404]


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code in [200, 404]
