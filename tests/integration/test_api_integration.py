#!/usr/bin/env python3
"""
Integration Tests für Zen-AI-Pentest API
======================================
End-to-End Tests für API-Endpunkte und Workflows
"""

import os
import sys
from unittest.mock import Mock, patch

import httpx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.asyncio]


class TestAPIAuthentication:
    """Integration Tests für API-Authentifizierung"""

    @pytest.fixture
    async def client(self):
        """Fixture für HTTP-Client"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            yield client

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, client):
        """Test: Login mit gültigen Credentials"""
        response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, client):
        """Test: Login mit ungültigen Credentials wird abgelehnt"""
        response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})

        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_access_protected_endpoint_without_token(self, client):
        """Test: Geschützte Endpoints ohne Token sind nicht zugänglich"""
        response = await client.get("/api/v1/scans")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_token(self, client):
        """Test: Geschützte Endpoints mit Token sind zugänglich"""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        token = login_response.json()["access_token"]

        # Zugriff mit Token
        response = await client.get("/api/v1/scans", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200


class TestScanWorkflow:
    """Integration Tests für kompletten Scan-Workflow"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # Login
            login_response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
            token = login_response.json()["access_token"]
            client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_create_scan(self, authenticated_client):
        """Test: Scan erstellen"""
        response = await authenticated_client.post(
            "/api/v1/scans",
            json={
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
                "modules": ["nmap", "subdomain_enum"],
                "options": {"nmap_args": "-sV -sC", "threads": 10},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "scan_id" in data
        assert data["status"] == "queued"

    @pytest.mark.asyncio
    async def test_get_scan_status(self, authenticated_client):
        """Test: Scan-Status abrufen"""
        # Scan erstellen
        create_response = await authenticated_client.post(
            "/api/v1/scans", json={"target": "scanme.nmap.org", "scan_type": "reconnaissance"}
        )
        scan_id = create_response.json()["scan_id"]

        # Status abrufen
        response = await authenticated_client.get(f"/api/v1/scans/{scan_id}")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data
        assert "start_time" in data

    @pytest.mark.asyncio
    async def test_list_scans(self, authenticated_client):
        """Test: Liste aller Scans abrufen"""
        response = await authenticated_client.get("/api/v1/scans")

        assert response.status_code == 200
        data = response.json()
        assert "scans" in data
        assert isinstance(data["scans"], list)

    @pytest.mark.asyncio
    async def test_stop_scan(self, authenticated_client):
        """Test: Scan stoppen"""
        # Scan erstellen
        create_response = await authenticated_client.post(
            "/api/v1/scans", json={"target": "scanme.nmap.org", "scan_type": "reconnaissance"}
        )
        scan_id = create_response.json()["scan_id"]

        # Scan stoppen
        response = await authenticated_client.post(f"/api/v1/scans/{scan_id}/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_get_scan_results(self, authenticated_client):
        """Test: Scan-Ergebnisse abrufen"""
        # Scan erstellen
        create_response = await authenticated_client.post(
            "/api/v1/scans", json={"target": "scanme.nmap.org", "scan_type": "vulnerability"}
        )
        scan_id = create_response.json()["scan_id"]

        # Ergebnisse abrufen
        response = await authenticated_client.get(f"/api/v1/scans/{scan_id}/results")

        assert response.status_code == 200
        data = response.json()
        assert "findings" in data
        assert "summary" in data


class TestAgentWorkflow:
    """Integration Tests für Agent-Workflow"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            login_response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
            token = login_response.json()["access_token"]
            client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_register_agent(self, authenticated_client):
        """Test: Agent registrieren"""
        response = await authenticated_client.post(
            "/api/v1/agents/register",
            json={
                "name": "recon_agent_1",
                "capabilities": ["nmap", "subdomain_enum", "whois"],
                "priority": 1,
                "max_concurrent_tasks": 3,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "agent_id" in data
        assert data["status"] == "registered"

    @pytest.mark.asyncio
    async def test_list_agents(self, authenticated_client):
        """Test: Liste aller Agents abrufen"""
        response = await authenticated_client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)

    @pytest.mark.asyncio
    async def test_assign_task_to_agent(self, authenticated_client):
        """Test: Task an Agent zuweisen"""
        # Agent registrieren
        agent_response = await authenticated_client.post(
            "/api/v1/agents/register", json={"name": "test_agent", "capabilities": ["vuln_scan"]}
        )
        agent_id = agent_response.json()["agent_id"]

        # Task zuweisen
        response = await authenticated_client.post(
            f"/api/v1/agents/{agent_id}/tasks",
            json={"type": "vuln_scan", "target": "example.com", "priority": "high", "options": {"scan_depth": "normal"}},
        )

        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "assigned"

    @pytest.mark.asyncio
    async def test_get_agent_status(self, authenticated_client):
        """Test: Agent-Status abrufen"""
        # Agent registrieren
        agent_response = await authenticated_client.post(
            "/api/v1/agents/register", json={"name": "status_test_agent", "capabilities": ["recon"]}
        )
        agent_id = agent_response.json()["agent_id"]

        # Status abrufen
        response = await authenticated_client.get(f"/api/v1/agents/{agent_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert "active_tasks" in data
        assert "capabilities" in data


class TestReportWorkflow:
    """Integration Tests für Reporting-Workflow"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            login_response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
            token = login_response.json()["access_token"]
            client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_generate_report(self, authenticated_client):
        """Test: Report generieren"""
        # Scan erstellen und abschließen
        scan_response = await authenticated_client.post(
            "/api/v1/scans", json={"target": "scanme.nmap.org", "scan_type": "vulnerability"}
        )
        scan_id = scan_response.json()["scan_id"]

        # Report generieren
        response = await authenticated_client.post(
            "/api/v1/reports", json={"scan_id": scan_id, "format": "pdf", "template": "executive", "include_evidence": True}
        )

        assert response.status_code == 201
        data = response.json()
        assert "report_id" in data
        assert "download_url" in data

    @pytest.mark.asyncio
    async def test_list_reports(self, authenticated_client):
        """Test: Liste aller Reports abrufen"""
        response = await authenticated_client.get("/api/v1/reports")

        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert isinstance(data["reports"], list)

    @pytest.mark.asyncio
    async def test_download_report(self, authenticated_client):
        """Test: Report herunterladen"""
        # Report erstellen
        report_response = await authenticated_client.post("/api/v1/reports", json={"scan_id": "test-scan-id", "format": "pdf"})
        report_id = report_response.json()["report_id"]

        # Report herunterladen
        response = await authenticated_client.get(f"/api/v1/reports/{report_id}/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestWebhookIntegration:
    """Integration Tests für Webhook-Integration"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            login_response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
            token = login_response.json()["access_token"]
            client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_register_webhook(self, authenticated_client):
        """Test: Webhook registrieren"""
        response = await authenticated_client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/webhook",
                "events": ["scan.complete", "finding.critical"],
                "secret": "webhook_secret_123",
                "active": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "webhook_id" in data

    @pytest.mark.asyncio
    async def test_webhook_delivery(self, authenticated_client):
        """Test: Webhook wird bei Events ausgeliefert"""
        # Webhook registrieren
        webhook_response = await authenticated_client.post(
            "/api/v1/webhooks", json={"url": "https://httpbin.org/post", "events": ["scan.complete"], "active": True}
        )
        webhook_response.json()["webhook_id"]

        # Scan erstellen und abschließen
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = Mock(status_code=200)

            await authenticated_client.post("/api/v1/scans", json={"target": "scanme.nmap.org", "scan_type": "reconnaissance"})

            # Webhook sollte aufgerufen worden sein
            mock_post.assert_called()


class TestSIEMIntegration:
    """Integration Tests für SIEM-Integration"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            login_response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
            token = login_response.json()["access_token"]
            client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_configure_siem(self, authenticated_client):
        """Test: SIEM-Integration konfigurieren"""
        response = await authenticated_client.post(
            "/api/v1/integrations/siem",
            json={
                "type": "splunk",
                "host": "splunk.example.com",
                "port": 8088,
                "token": "splunk-hec-token",
                "index": "security",
                "enabled": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "configured"

    @pytest.mark.asyncio
    async def test_send_finding_to_siem(self, authenticated_client):
        """Test: Finding an SIEM senden"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = Mock(status_code=200)

            response = await authenticated_client.post(
                "/api/v1/findings/send-to-siem",
                json={"finding_id": "finding-123", "siem_config": {"type": "splunk", "host": "splunk.example.com"}},
            )

            assert response.status_code == 200
            mock_post.assert_called()


class TestComplianceWorkflow:
    """Integration Tests für Compliance-Workflow"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            login_response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
            token = login_response.json()["access_token"]
            client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_compliance_scan(self, authenticated_client):
        """Test: Compliance-Scan durchführen"""
        response = await authenticated_client.post(
            "/api/v1/compliance/scans",
            json={
                "target": "internal-network",
                "framework": "ISO27001",
                "controls": ["A.12.6", "A.14.2"],
                "options": {"evidence_collection": True},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "scan_id" in data
        assert data["framework"] == "ISO27001"

    @pytest.mark.asyncio
    async def test_compliance_report(self, authenticated_client):
        """Test: Compliance-Report generieren"""
        # Compliance-Scan durchführen
        scan_response = await authenticated_client.post(
            "/api/v1/compliance/scans", json={"target": "internal-network", "framework": "NIST_800_53"}
        )
        scan_id = scan_response.json()["scan_id"]

        # Report generieren
        response = await authenticated_client.post(
            "/api/v1/compliance/reports", json={"scan_id": scan_id, "format": "pdf", "include_remediation": True}
        )

        assert response.status_code == 201
        data = response.json()
        assert "report_id" in data


class TestErrorHandling:
    """Integration Tests für Fehlerbehandlung"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            login_response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
            token = login_response.json()["access_token"]
            client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_invalid_scan_target(self, authenticated_client):
        """Test: Ungültiges Scan-Ziel wird abgelehnt"""
        response = await authenticated_client.post(
            "/api/v1/scans", json={"target": "not-a-valid-target!!!", "scan_type": "reconnaissance"}
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_rate_limiting(self, authenticated_client):
        """Test: Rate-Limiting funktioniert"""
        # Mehrere Anfragen schnell hintereinander
        responses = []
        for _ in range(100):
            response = await authenticated_client.get("/api/v1/scans")
            responses.append(response.status_code)

        # Einige sollten 429 (Too Many Requests) sein
        assert 429 in responses

    @pytest.mark.asyncio
    async def test_not_found(self, authenticated_client):
        """Test: 404 für nicht-existierende Ressourcen"""
        response = await authenticated_client.get("/api/v1/scans/nonexistent-id")

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api", "--cov-report=term-missing"])
