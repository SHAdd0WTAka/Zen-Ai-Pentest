"""Tests for Zen-AI-Pentest Bridge"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_bridge_health():
    """Test bridge health endpoint"""
    with patch("app.routers.bridge.zen_bridge.health_check", new_callable=AsyncMock, return_value={"status": "ok"}):
        response = client.get("/api/v1/bridge/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_bridge_scan():
    """Test triggering a scan"""
    with patch("app.routers.bridge.zen_bridge.create_scan", new_callable=AsyncMock, return_value={"id": "scan-123"}):
        response = client.post(
            "/api/v1/bridge/scan",
            json={
                "target": "example.com",
                "scan_type": "full",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["scan_id"] == "scan-123"


def test_bridge_scan_error():
    """Test scan error handling"""
    with patch(
        "app.routers.bridge.zen_bridge.create_scan", new_callable=AsyncMock, side_effect=Exception("Connection failed")
    ):
        response = client.post(
            "/api/v1/bridge/scan",
            json={
                "target": "example.com",
                "scan_type": "full",
            },
        )
        assert response.status_code == 500


def test_bridge_get_scan():
    """Test getting scan status"""
    with patch(
        "app.routers.bridge.zen_bridge.get_scan", new_callable=AsyncMock, return_value={"id": "scan-123", "status": "running"}
    ):
        response = client.get("/api/v1/bridge/scan/scan-123")
        assert response.status_code == 200
        assert response.json()["id"] == "scan-123"


def test_bridge_get_scan_not_found():
    """Test scan not found"""
    with patch("app.routers.bridge.zen_bridge.get_scan", new_callable=AsyncMock, side_effect=Exception("Not found")):
        response = client.get("/api/v1/bridge/scan/scan-123")
        assert response.status_code == 404


def test_bridge_get_scan_results():
    """Test getting scan results"""
    with patch("app.routers.bridge.zen_bridge.get_scan_results", new_callable=AsyncMock, return_value={"findings": []}):
        response = client.get("/api/v1/bridge/scan/scan-123/results")
        assert response.status_code == 200


def test_bridge_list_scans():
    """Test listing scans"""
    with patch("app.routers.bridge.zen_bridge.list_scans", new_callable=AsyncMock, return_value=[{"id": "scan-1"}]):
        response = client.get("/api/v1/bridge/scans")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["scans"]) == 1


def test_bridge_run_tool():
    """Test running a tool"""
    with patch("app.routers.bridge.zen_bridge.run_tool", new_callable=AsyncMock, return_value={"output": "pwned"}):
        response = client.post(
            "/api/v1/bridge/tool/run",
            json={
                "tool_name": "nmap",
                "target": "example.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"


def test_bridge_run_tool_error():
    """Test tool run error"""
    with patch("app.routers.bridge.zen_bridge.run_tool", new_callable=AsyncMock, side_effect=Exception("Tool failed")):
        response = client.post(
            "/api/v1/bridge/tool/run",
            json={
                "tool_name": "nmap",
                "target": "example.com",
            },
        )
        assert response.status_code == 500


def test_bridge_list_tools():
    """Test listing tools"""
    with patch("app.routers.bridge.zen_bridge.get_tools", new_callable=AsyncMock, return_value=["nmap", "zap"]):
        response = client.get("/api/v1/bridge/tools")
        assert response.status_code == 200
        assert response.json()["tools"] == ["nmap", "zap"]


def test_bridge_generate_report():
    """Test generating a report"""
    with patch(
        "app.routers.bridge.zen_bridge.generate_report", new_callable=AsyncMock, return_value={"url": "http://report.pdf"}
    ):
        response = client.post("/api/v1/bridge/report/generate/scan-123?format=pdf")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
