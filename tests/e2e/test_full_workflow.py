"""
End-to-End Tests for Zen-AI-Pentest
=====================================

Comprehensive end-to-end tests covering complete pentest workflows:
1. Create target
2. Run reconnaissance
3. Run vulnerability scan
4. Generate report

Uses mocked external services for isolated testing.
Tests state transitions throughout the workflow.

Usage:
    pytest tests/e2e/test_full_workflow.py -v
    pytest tests/e2e/test_full_workflow.py -v --cov=. --cov-report=term-missing
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Dict, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root is in path
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ),
)

from database.models import Base

# Mark all tests in this file
pytestmark = [pytest.mark.e2e, pytest.mark.asyncio, pytest.mark.slow]


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a SQLite in-memory database engine for testing."""
    engine = create_engine(
        "sqlite:///./test_e2e.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    # Cleanup database file
    import os

    if os.path.exists("./test_e2e.db"):
        os.remove("./test_e2e.db")


@pytest.fixture(scope="function")
def client(test_db_engine):
    """Create a FastAPI TestClient with test database."""
    from api.main import app, get_db

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Set test environment
    os.environ["ADMIN_PASSWORD"] = "testpass123"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers with valid token."""
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_scan_tools():
    """Mock all external scan tools."""
    with (
        patch("api.main.run_scan_task") as mock_scan,
        patch("api.main.execute_tool_task") as mock_tool,
        patch("api.main.generate_report_task") as mock_report,
    ):

        mock_scan.return_value = None
        mock_tool.return_value = None
        mock_report.return_value = None

        yield {
            "scan": mock_scan,
            "tool": mock_tool,
            "report": mock_report,
        }


@pytest.fixture
def mock_external_services():
    """Mock all external services."""
    with (
        patch("api.main.redis") as mock_redis,
        patch("agents.react_agent.ReActAgent") as mock_agent,
    ):

        # Mock Redis
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.from_url.return_value = mock_redis_client

        # Mock ReActAgent
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = {
            "final_message": "Scan completed successfully",
            "iterations": 5,
            "findings": [
                {"tool": "nmap", "result": "Port 80 open"},
                {"tool": "nuclei", "result": "Vulnerability found"},
            ],
        }
        mock_agent.return_value = mock_agent_instance

        yield {
            "redis": mock_redis,
            "agent": mock_agent,
            "agent_instance": mock_agent_instance,
        }


# ============================================================================
# TEST CLASS: Complete Pentest Workflow
# ============================================================================


class TestCompletePentestWorkflow:
    """Test complete pentest workflow from target creation to report generation."""

    def test_full_workflow_success(
        self, client, auth_headers, mock_external_services
    ):
        """Test successful complete pentest workflow."""
        # Step 1: Create a target/scan
        scan_data = {
            "name": "E2E Test Scan",
            "target": "scanme.nmap.org",
            "scan_type": "comprehensive",
            "config": {
                "ports": "80,443,8080",
                "intensity": "medium",
                "modules": ["nmap", "nuclei", "sqlmap"],
            },
        }

        response = client.post("/scans", json=scan_data, headers=auth_headers)
        assert response.status_code == 200
        scan_result = response.json()
        scan_id = scan_result["id"]
        assert scan_result["status"] == "pending"

        # Step 2: Verify scan was created
        get_response = client.get(f"/scans/{scan_id}", headers=auth_headers)
        assert get_response.status_code == 200
        scan_details = get_response.json()
        assert scan_details["id"] == scan_id
        assert scan_details["target"] == "scanme.nmap.org"

        # Step 3: Add findings to the scan (simulating scan results)
        findings = [
            {
                "title": "Open SSH Port",
                "description": "Port 22 is open with SSH service",
                "severity": "info",
                "cvss_score": 0.0,
                "evidence": "nmap scan result: 22/tcp open ssh",
                "tool": "nmap",
                "target": "scanme.nmap.org",
                "port": 22,
                "service": "ssh",
            },
            {
                "title": "HTTP Security Headers Missing",
                "description": "X-Frame-Options header is not set",
                "severity": "medium",
                "cvss_score": 4.3,
                "evidence": "Header analysis shows missing X-Frame-Options",
                "tool": "nuclei",
                "target": "http://scanme.nmap.org",
                "port": 80,
                "service": "http",
            },
            {
                "title": "Potential SQL Injection",
                "description": "Parameter 'id' appears vulnerable to SQL injection",
                "severity": "critical",
                "cvss_score": 9.1,
                "evidence": "sqlmap detected boolean-based blind SQL injection",
                "tool": "sqlmap",
                "target": "http://scanme.nmap.org/page?id=1",
                "port": 80,
                "service": "http",
            },
        ]

        for finding in findings:
            finding_response = client.post(
                f"/scans/{scan_id}/findings",
                json=finding,
                headers=auth_headers,
            )
            assert finding_response.status_code == 200

        # Step 4: Verify findings were added
        findings_response = client.get(
            f"/scans/{scan_id}/findings", headers=auth_headers
        )
        assert findings_response.status_code == 200
        findings_list = findings_response.json()
        assert len(findings_list) == 3

        # Verify finding details
        severities = [f["severity"] for f in findings_list]
        assert "critical" in severities
        assert "medium" in severities
        assert "info" in severities

        # Step 5: Update scan status to running
        update_response = client.patch(
            f"/scans/{scan_id}",
            json={"status": "running"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        # Step 6: Mark scan as completed
        complete_response = client.patch(
            f"/scans/{scan_id}",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert complete_response.status_code == 200
        completed_scan = complete_response.json()
        assert completed_scan["status"] == "completed"

        # Step 7: Generate report
        report_data = {
            "scan_id": scan_id,
            "format": "pdf",
            "template": "executive",
        }

        with patch("api.main.generate_report_task") as mock_report_task:
            mock_report_task.return_value = None
            report_response = client.post(
                "/reports", json=report_data, headers=auth_headers
            )
            assert report_response.status_code == 200
            report_result = report_response.json()
            report_id = report_result["id"]
            assert report_result["status"] == "pending"

        # Step 8: List all reports
        reports_response = client.get("/reports", headers=auth_headers)
        assert reports_response.status_code == 200
        reports_list = reports_response.json()
        assert isinstance(reports_list, list)

        # Step 9: Verify workflow completion
        final_scan = client.get(
            f"/scans/{scan_id}", headers=auth_headers
        ).json()
        assert final_scan["status"] == "completed"

    def test_workflow_with_findings_filtering(self, client, auth_headers):
        """Test workflow with findings filtering by severity."""
        # Create scan
        scan_response = client.post(
            "/scans",
            json={
                "name": "Filter Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "vulnerability",
            },
            headers=auth_headers,
        )
        scan_id = scan_response.json()["id"]

        # Add findings with different severities
        severity_findings = [
            {
                "title": "Critical Issue",
                "severity": "critical",
                "description": "Critical",
            },
            {
                "title": "High Issue 1",
                "severity": "high",
                "description": "High 1",
            },
            {
                "title": "High Issue 2",
                "severity": "high",
                "description": "High 2",
            },
            {
                "title": "Medium Issue",
                "severity": "medium",
                "description": "Medium",
            },
            {"title": "Low Issue", "severity": "low", "description": "Low"},
        ]

        for finding in severity_findings:
            client.post(
                f"/scans/{scan_id}/findings",
                json=finding,
                headers=auth_headers,
            )

        # Filter by critical
        critical_response = client.get(
            f"/scans/{scan_id}/findings?severity=critical",
            headers=auth_headers,
        )
        critical_findings = critical_response.json()
        assert len(critical_findings) == 1
        assert all(f["severity"] == "critical" for f in critical_findings)

        # Filter by high
        high_response = client.get(
            f"/scans/{scan_id}/findings?severity=high",
            headers=auth_headers,
        )
        high_findings = high_response.json()
        assert len(high_findings) == 2

    def test_workflow_state_transitions(
        self, client, auth_headers, mock_external_services
    ):
        """Test state transitions throughout the workflow."""
        # Create scan
        scan_response = client.post(
            "/scans",
            json={
                "name": "State Transition Test",
                "target": "scanme.nmap.org",
                "scan_type": "network",
            },
            headers=auth_headers,
        )
        scan_id = scan_response.json()["id"]

        # Initial state: pending
        scan = client.get(f"/scans/{scan_id}", headers=auth_headers).json()
        assert scan["status"] == "pending"

        # Transition: pending -> running
        client.patch(
            f"/scans/{scan_id}",
            json={"status": "running"},
            headers=auth_headers,
        )
        scan = client.get(f"/scans/{scan_id}", headers=auth_headers).json()
        assert scan["status"] == "running"

        # Transition: running -> completed
        client.patch(
            f"/scans/{scan_id}",
            json={"status": "completed"},
            headers=auth_headers,
        )
        scan = client.get(f"/scans/{scan_id}", headers=auth_headers).json()
        assert scan["status"] == "completed"

    def test_workflow_with_multiple_scans(self, client, auth_headers):
        """Test workflow with multiple concurrent scans."""
        scan_ids = []

        # Create multiple scans
        for i in range(5):
            response = client.post(
                "/scans",
                json={
                    "name": f"Multi Scan {i}",
                    "target": f"target{i}.example.com",
                    "scan_type": "reconnaissance",
                },
                headers=auth_headers,
            )
            scan_ids.append(response.json()["id"])

        # Verify all scans exist
        list_response = client.get("/scans", headers=auth_headers)
        scans = list_response.json()
        scan_ids_from_list = [s["id"] for s in scans]

        for scan_id in scan_ids:
            assert scan_id in scan_ids_from_list

    def test_workflow_report_generation_formats(self, client, auth_headers):
        """Test report generation in different formats."""
        # Create scan with findings
        scan_response = client.post(
            "/scans",
            json={
                "name": "Report Format Test",
                "target": "scanme.nmap.org",
                "scan_type": "vulnerability",
            },
            headers=auth_headers,
        )
        scan_id = scan_response.json()["id"]

        # Add finding
        client.post(
            f"/scans/{scan_id}/findings",
            json={
                "title": "Test Finding",
                "severity": "high",
                "description": "Test",
            },
            headers=auth_headers,
        )

        # Test PDF report
        with patch("api.main.generate_report_task"):
            pdf_response = client.post(
                "/reports",
                json={
                    "scan_id": scan_id,
                    "format": "pdf",
                    "template": "default",
                },
                headers=auth_headers,
            )
            assert pdf_response.status_code == 200

        # Test HTML report
        with patch("api.main.generate_report_task"):
            html_response = client.post(
                "/reports",
                json={
                    "scan_id": scan_id,
                    "format": "html",
                    "template": "default",
                },
                headers=auth_headers,
            )
            assert html_response.status_code == 200


# ============================================================================
# TEST CLASS: Error Scenarios
# ============================================================================


class TestWorkflowErrorScenarios:
    """Test error scenarios in the workflow."""

    def test_workflow_invalid_target(self, client, auth_headers):
        """Test workflow with invalid target."""
        # This test may vary based on validation implementation
        response = client.post(
            "/scans",
            json={
                "name": "Invalid Target Test",
                "target": "not-a-valid-target-at-all!!!",
                "scan_type": "network",
            },
            headers=auth_headers,
        )
        # Should either accept and validate later or reject immediately
        assert response.status_code in [200, 400, 422]

    def test_workflow_add_finding_to_nonexistent_scan(
        self, client, auth_headers
    ):
        """Test adding finding to non-existent scan."""
        response = client.post(
            "/scans/99999/findings",
            json={
                "title": "Test Finding",
                "severity": "high",
                "description": "Test",
            },
            headers=auth_headers,
        )
        assert response.status_code in [404, 500]

    def test_workflow_generate_report_invalid_scan(self, client, auth_headers):
        """Test generating report for non-existent scan."""
        response = client.post(
            "/reports",
            json={
                "scan_id": 99999,
                "format": "pdf",
            },
            headers=auth_headers,
        )
        # Should handle gracefully
        assert response.status_code in [200, 404, 400]

    def test_workflow_unauthorized_access(self, client):
        """Test workflow steps without authorization."""
        # Try to create scan without auth
        response = client.post(
            "/scans",
            json={
                "name": "Unauthorized Test",
                "target": "scanme.nmap.org",
                "scan_type": "network",
            },
        )
        assert response.status_code == 403

        # Try to get scans without auth
        response = client.get("/scans")
        assert response.status_code == 403


# ============================================================================
# TEST CLASS: WebSocket Workflow
# ============================================================================


class TestWebSocketWorkflow:
    """Test workflow with WebSocket connections."""

    def test_websocket_scan_monitoring(
        self, client, auth_headers, mock_external_services
    ):
        """Test WebSocket connection for scan monitoring."""
        # Create scan
        scan_response = client.post(
            "/scans",
            json={
                "name": "WebSocket Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "network",
            },
            headers=auth_headers,
        )
        scan_id = scan_response.json()["id"]

        # Connect WebSocket
        with client.websocket_connect(f"/ws/scans/{scan_id}") as websocket:
            # Send ping
            websocket.send_json({"action": "ping"})

            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_notifications(self, client):
        """Test WebSocket connection for notifications."""
        with client.websocket_connect("/ws/notifications") as websocket:
            # Connection should be established
            websocket.send_text("ping")
            # No specific response expected


# ============================================================================
# TEST CLASS: Complex Workflow Scenarios
# ============================================================================


class TestComplexWorkflowScenarios:
    """Test complex workflow scenarios."""

    def test_full_reconnaissance_to_exploitation_workflow(
        self, client, auth_headers, mock_external_services
    ):
        """Test full workflow from recon to exploitation."""
        # Phase 1: Reconnaissance
        recon_scan = client.post(
            "/scans",
            json={
                "name": "Reconnaissance Phase",
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
                "config": {"modules": ["nmap", "subdomain_enum"]},
            },
            headers=auth_headers,
        ).json()

        # Add recon findings
        client.post(
            f"/scans/{recon_scan['id']}/findings",
            json={
                "title": "Subdomain Discovered",
                "severity": "info",
                "description": "Found api.example.com",
                "tool": "amass",
            },
            headers=auth_headers,
        )

        # Phase 2: Vulnerability Scanning
        vuln_scan = client.post(
            "/scans",
            json={
                "name": "Vulnerability Phase",
                "target": "api.example.com",
                "scan_type": "vulnerability",
                "config": {"modules": ["nuclei", "sqlmap"]},
            },
            headers=auth_headers,
        ).json()

        # Add vulnerability findings
        client.post(
            f"/scans/{vuln_scan['id']}/findings",
            json={
                "title": "SQL Injection",
                "severity": "critical",
                "description": "SQLi in API endpoint",
                "tool": "sqlmap",
            },
            headers=auth_headers,
        )

        # Phase 3: Generate comprehensive report
        with patch("api.main.generate_report_task"):
            report_response = client.post(
                "/reports",
                json={
                    "scan_id": vuln_scan["id"],
                    "format": "pdf",
                    "template": "technical",
                },
                headers=auth_headers,
            )
            assert report_response.status_code == 200

    def test_workflow_with_finding_updates(self, client, auth_headers):
        """Test workflow with finding updates and verification."""
        # Create scan
        scan = client.post(
            "/scans",
            json={
                "name": "Finding Update Test",
                "target": "scanme.nmap.org",
                "scan_type": "vulnerability",
            },
            headers=auth_headers,
        ).json()

        # Add finding
        finding = client.post(
            f"/scans/{scan['id']}/findings",
            json={
                "title": "Initial Finding",
                "severity": "medium",
                "description": "Initial description",
                "verified": 0,
            },
            headers=auth_headers,
        ).json()

        # Update finding
        update_response = client.patch(
            f"/findings/{finding['id']}",
            json={
                "severity": "high",
                "verified": 1,
                "remediation": "Apply patch XYZ",
            },
            headers=auth_headers,
        )
        assert update_response.status_code == 200

    def test_parallel_scan_workflow(self, client, auth_headers):
        """Test running multiple scans in parallel."""
        targets = ["target1.com", "target2.com", "target3.com"]
        scan_ids = []

        # Create scans for all targets
        for target in targets:
            scan = client.post(
                "/scans",
                json={
                    "name": f"Parallel Scan {target}",
                    "target": target,
                    "scan_type": "network",
                },
                headers=auth_headers,
            ).json()
            scan_ids.append(scan["id"])

        # Verify all scans were created
        assert len(scan_ids) == len(targets)

        # Add findings to each scan
        for scan_id in scan_ids:
            client.post(
                f"/scans/{scan_id}/findings",
                json={
                    "title": "Open Ports",
                    "severity": "info",
                    "description": "Ports 80, 443 open",
                },
                headers=auth_headers,
            )

        # Verify findings for each scan
        for scan_id in scan_ids:
            findings = client.get(
                f"/scans/{scan_id}/findings",
                headers=auth_headers,
            ).json()
            assert len(findings) >= 1


# ============================================================================
# TEST CLASS: Workflow Metrics
# ============================================================================


class TestWorkflowMetrics:
    """Test workflow metrics and statistics."""

    def test_scan_statistics(self, client, auth_headers):
        """Test scan statistics accumulation."""
        # Create scans with different statuses
        statuses = ["pending", "running", "completed", "failed"]

        for i, status in enumerate(statuses):
            scan = client.post(
                "/scans",
                json={
                    "name": f"Stats Scan {i}",
                    "target": f"stats{i}.example.com",
                    "scan_type": "network",
                },
                headers=auth_headers,
            ).json()

            if status != "pending":
                client.patch(
                    f"/scans/{scan['id']}",
                    json={"status": status},
                    headers=auth_headers,
                )

        # Get all scans
        scans = client.get("/scans", headers=auth_headers).json()

        # Count by status
        status_counts = {}
        for scan in scans:
            s = scan["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        # Should have at least one of each status
        for status in statuses:
            assert status in status_counts or status == "pending"

    def test_finding_severity_distribution(self, client, auth_headers):
        """Test finding severity distribution."""
        # Create scan
        scan = client.post(
            "/scans",
            json={
                "name": "Severity Distribution Test",
                "target": "scanme.nmap.org",
                "scan_type": "vulnerability",
            },
            headers=auth_headers,
        ).json()

        # Add findings with all severities
        severities = ["critical", "high", "medium", "low", "info"]
        for severity in severities:
            client.post(
                f"/scans/{scan['id']}/findings",
                json={
                    "title": f"{severity.capitalize()} Finding",
                    "severity": severity,
                    "description": f"Test {severity} finding",
                },
                headers=auth_headers,
            )

        # Get findings
        findings = client.get(
            f"/scans/{scan['id']}/findings",
            headers=auth_headers,
        ).json()

        # Verify distribution
        severity_counts = {}
        for finding in findings:
            s = finding["severity"]
            severity_counts[s] = severity_counts.get(s, 0) + 1

        for severity in severities:
            assert severity in severity_counts
            assert severity_counts[severity] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])
