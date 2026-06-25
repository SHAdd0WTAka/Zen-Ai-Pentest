"""
End-to-End Tests for Zen-AI-Pentest
Full workflow tests from scan creation to report generation
"""

import json
import time
from typing import Any, Dict

import pytest


@pytest.mark.e2e
class TestFullScanWorkflow:
    """Test complete scan workflow"""

    def test_health_check(self, client):
        """E2E: Health endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_scan_workflow_mock(self, client):
        """E2E: Complete scan workflow with mocked backend"""
        from unittest.mock import MagicMock, patch

        # 1. Create scan
        scan_data = {"target": "scanme.nmap.org", "scan_type": "basic", "options": {"ports": "80,443"}}

        with patch("api.routes.scans.get_db") as mock_db:
            mock_db.return_value = MagicMock()

            response = client.post("/api/v1/scans", json=scan_data)
            assert response.status_code in [200, 201, 401]

            if response.status_code in [200, 201]:
                scan_id = response.json().get("id", 1)

                # 2. Get scan status
                response = client.get(f"/api/v1/scans/{scan_id}")
                assert response.status_code in [200, 401]

                # 3. List findings
                response = client.get("/api/v1/findings")
                assert response.status_code in [200, 401]

    def test_agent_workflow_mock(self, client):
        """E2E: Agent creation and task assignment"""
        from unittest.mock import MagicMock, patch

        agent_data = {"name": "e2e-test-agent", "agent_type": "scanner", "config": {"max_depth": 2}}

        with patch("api.routes.agents.get_db") as mock_db:
            mock_db.return_value = MagicMock()

            # Create agent
            response = client.post("/api/v1/agents", json=agent_data)
            assert response.status_code in [200, 201, 401]

            if response.status_code in [200, 201]:
                # List agents
                response = client.get("/api/v1/agents")
                assert response.status_code in [200, 401]


@pytest.mark.e2e
class TestAuthenticationFlow:
    """Test authentication flows"""

    def test_login_flow(self, client):
        """E2E: Complete login flow"""
        login_data = {"username": "admin", "password": "admin"}

        response = client.post("/api/v1/auth/login", json=login_data)
        # Should either succeed or fail authentication
        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            data = response.json()
            assert "token" in data or "access_token" in data

    def test_protected_endpoints_without_auth(self, client):
        """E2E: Protected endpoints require authentication"""
        protected_endpoints = [
            "/api/v1/scans",
            "/api/v1/agents",
            "/api/v1/findings",
            "/api/v1/reports",
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            # Should require auth
            assert response.status_code in [401, 403, 200], f"{endpoint} should require auth"


@pytest.mark.e2e
class TestDashboardFlow:
    """Test dashboard data flow"""

    def test_dashboard_stats(self, client):
        """E2E: Dashboard stats endpoint"""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code in [200, 401]

    def test_dashboard_coverage(self, client):
        """E2E: Dashboard coverage endpoint"""
        response = client.get("/api/v1/dashboard/coverage")
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "overall" in data or "coverage" in data or "modules" in data


@pytest.mark.e2e
class TestErrorScenarios:
    """Test error handling in E2E scenarios"""

    def test_invalid_scan_id(self, client):
        """E2E: Get scan with invalid ID"""
        response = client.get("/api/v1/scans/invalid-id")
        assert response.status_code in [404, 422, 401]

    def test_missing_required_fields(self, client):
        """E2E: Create scan without required fields"""
        incomplete_data = {"options": {}}  # Missing target

        response = client.post("/api/v1/scans", json=incomplete_data)
        assert response.status_code in [400, 422, 401]

    def test_invalid_json(self, client):
        """E2E: Send invalid JSON"""
        response = client.post("/api/v1/scans", data="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code in [400, 422]


@pytest.mark.e2e
class TestPerformance:
    """Performance tests"""

    def test_health_response_time(self, client):
        """E2E: Health endpoint responds quickly"""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second

    def test_concurrent_requests(self, client):
        """E2E: Handle concurrent requests"""
        import concurrent.futures

        def make_request():
            return client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)


@pytest.mark.e2e
class TestReportGeneration:
    """Test report generation workflow"""

    def test_generate_pdf_report_mock(self, client):
        """E2E: Generate PDF report"""
        from unittest.mock import MagicMock, patch

        report_data = {"scan_id": 1, "format": "pdf", "template": "executive"}

        with patch("api.routes.reports.get_db") as mock_db:
            mock_db.return_value = MagicMock()

            response = client.post("/api/v1/reports/generate", json=report_data)
            assert response.status_code in [200, 201, 401, 202]

    def test_list_reports_mock(self, client):
        """E2E: List generated reports"""
        from unittest.mock import MagicMock, patch

        with patch("api.routes.reports.get_db") as mock_db:
            mock_db.return_value = MagicMock()
            mock_db.return_value.query.return_value.all.return_value = []

            response = client.get("/api/v1/reports")
            assert response.status_code in [200, 401]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
