"""
Tests for agent and report API routes.
Split from test_api_routes_all.py
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

pytest.skip(
    "Stale generated test suite (see issue notes); skipped until rewritten",
    allow_module_level=True,
)


@pytest.fixture
def test_agent_data():
    """Sample test agent data"""
    return {
        "id": str(uuid4()),
        "name": "Test Agent",
        "role": "recon",
        "status": "running",
        "current_task": "Scanning ports",
        "last_activity": datetime.now(timezone.utc),
        "messages_processed": 42,
        "errors_count": 0,
    }


@pytest.fixture
def test_report_data():
    """Sample test report data"""
    return {
        "id": str(uuid4()),
        "scan_id": str(uuid4()),
        "report_type": "executive",
        "format": "pdf",
        "status": "completed",
        "title": "Executive Report - Test Corp",
        "company_name": "Test Corp",
        "file_path": "/reports/test.pdf",
        "file_size": 1024000,
        "generated_at": datetime.now(timezone.utc),
        "total_findings": 10,
        "critical_count": 2,
        "high_count": 3,
        "medium_count": 4,
        "low_count": 1,
        "info_count": 0,
    }


# =============================================================================
# Helper Functions
# =============================================================================


def create_mock_user(user_id: str = None, role: str = "USER", is_active: bool = True):
    """Create a mock user object"""
    mock_user = MagicMock()
    mock_user.id = user_id or str(uuid4())
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.full_name = "Test User"
    mock_user.role = MagicMock()
    mock_user.role.value = 1 if role == "USER" else 2 if role == "ADMIN" else 3
    mock_user.role.name = role
    mock_user.is_active = is_active
    mock_user.created_at = datetime.now(timezone.utc)
    mock_user.hashed_password = "hashed_password"
    mock_user.to_response.return_value = {
        "id": str(mock_user.id),
        "username": mock_user.username,
        "email": mock_user.email,
        "full_name": mock_user.full_name,
        "role": role,
        "is_active": is_active,
        "created_at": mock_user.created_at,
    }
    mock_user.save = AsyncMock()
    mock_user.delete = AsyncMock()
    return mock_user


def create_mock_agent(agent_id: str = None, state: str = "running"):
    """Create a mock agent object"""
    mock_agent = MagicMock()
    mock_agent.id = agent_id or str(uuid4())
    mock_agent.name = f"Agent-{mock_agent.id[:8]}"
    mock_agent.role = MagicMock()
    mock_agent.role.value = "recon"
    mock_agent.state = MagicMock()
    mock_agent.state.value = state
    mock_agent.current_task = "Test task"
    mock_agent.last_activity = datetime.now(timezone.utc)
    mock_agent.messages_processed = 10
    mock_agent.errors_count = 0
    mock_agent.start = AsyncMock()
    mock_agent.stop = AsyncMock()
    return mock_agent


def create_mock_report(report_id: str = None):
    """Create a mock report object"""
    mock_report = MagicMock()
    mock_report.id = report_id or str(uuid4())
    mock_report.scan_id = str(uuid4())
    mock_report.report_type = MagicMock()
    mock_report.report_type.value = "executive"
    mock_report.report_format = MagicMock()
    mock_report.report_format.value = "pdf"
    mock_report.status = MagicMock()
    mock_report.status.value = "completed"
    mock_report.title = "Test Report"
    mock_report.company_name = "Test Corp"
    mock_report.file_path = "/reports/test.pdf"
    mock_report.file_size = 1024000
    mock_report.generated_at = datetime.now(timezone.utc)
    mock_report.total_findings = 10
    mock_report.critical_count = 2
    mock_report.high_count = 3
    mock_report.medium_count = 4
    mock_report.low_count = 1
    mock_report.info_count = 0
    return mock_report


@pytest.mark.unit
class TestAgentRoutes:
    """Tests for api/routes/agents.py - Agent Management Endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client with mocked agents"""

        from api.routes.agents import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/agents")

        with patch("api.routes.agents.agent_manager") as mock_manager:
            with patch("api.routes.agents.get_current_user") as mock_auth:
                mock_auth.return_value = create_mock_user(role="ADMIN")
                with patch("api.routes.agents.require_permissions") as mock_perms:
                    mock_perms.return_value = lambda: create_mock_user(role="ADMIN")
                    yield TestClient(app), mock_manager

    def test_list_agents_empty(self, client):
        """Test listing agents when none exist"""
        test_client, mock_manager = client
        mock_manager.get_all_agents.return_value = []

        response = test_client.get("/api/v1/agents/")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_agents_with_data(self, client):
        """Test listing agents with existing agents"""
        test_client, mock_manager = client

        mock_agent1 = create_mock_agent(state="running")
        mock_agent2 = create_mock_agent(state="idle")
        mock_manager.get_all_agents.return_value = [mock_agent1, mock_agent2]

        response = test_client.get("/api/v1/agents/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["status"] == "running"
        assert data[1]["status"] == "idle"

    def test_get_agent_success(self, client):
        """Test getting a specific agent"""
        test_client, mock_manager = client

        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id)
        mock_manager.get_agent.return_value = mock_agent

        response = test_client.get(f"/api/v1/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
        assert data["name"] == mock_agent.name

    def test_get_agent_not_found(self, client):
        """Test getting a non-existent agent"""
        test_client, mock_manager = client
        mock_manager.get_agent.return_value = None

        response = test_client.get(f"/api/v1/agents/{uuid4()}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_start_agent_success(self, client):
        """Test starting an agent"""
        test_client, mock_manager = client

        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id)
        mock_manager.get_agent.return_value = mock_agent
        mock_manager.start_agent = AsyncMock()

        response = test_client.post(f"/api/v1/agents/{agent_id}/start")

        assert response.status_code == 200
        assert "started" in response.json()["message"].lower()

    def test_start_agent_not_found(self, client):
        """Test starting a non-existent agent"""
        test_client, mock_manager = client
        mock_manager.get_agent.return_value = None

        response = test_client.post(f"/api/v1/agents/{uuid4()}/start")

        assert response.status_code == 404

    def test_stop_agent_success(self, client):
        """Test stopping an agent"""
        test_client, mock_manager = client

        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id)
        mock_manager.get_agent.return_value = mock_agent
        mock_manager.stop_agent = AsyncMock()

        response = test_client.post(f"/api/v1/agents/{agent_id}/stop")

        assert response.status_code == 200
        assert "stopped" in response.json()["message"].lower()

    def test_stop_agent_not_found(self, client):
        """Test stopping a non-existent agent"""
        test_client, mock_manager = client
        mock_manager.get_agent.return_value = None

        response = test_client.post(f"/api/v1/agents/{uuid4()}/stop")

        assert response.status_code == 404

    def test_assign_task_success(self, client):
        """Test assigning a task to an agent"""
        test_client, mock_manager = client

        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id, state="running")
        mock_manager.get_agent.return_value = mock_agent
        mock_manager.assign_task = AsyncMock(return_value="task-123")

        response = test_client.post(
            f"/api/v1/agents/{agent_id}/task",
            json={
                "agent_id": agent_id,
                "task_type": "port_scan",
                "parameters": {"target": "example.com"},
                "priority": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-123"
        assert "assigned" in data["message"].lower()

    def test_assign_agent_not_running(self, client):
        """Test assigning task to non-running agent"""
        test_client, mock_manager = client

        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id, state="stopped")
        mock_manager.get_agent.return_value = mock_agent

        response = test_client.post(
            f"/api/v1/agents/{agent_id}/task",
            json={
                "agent_id": agent_id,
                "task_type": "port_scan",
                "parameters": {},
            },
        )

        assert response.status_code == 400
        assert "not running" in response.json()["detail"].lower()

    def test_send_message_success(self, client):
        """Test sending a message to an agent"""
        test_client, mock_manager = client

        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id)
        mock_manager.get_agent.return_value = mock_agent
        mock_manager.send_message_to_agent = AsyncMock(return_value={"status": "received"})

        response = test_client.post(
            f"/api/v1/agents/{agent_id}/message",
            json={"agent_id": agent_id, "message": "Hello", "context": {}},
        )

        assert response.status_code == 200
        data = response.json()
        assert "sent" in data["message"].lower()
        assert data["response"]["status"] == "received"

    def test_get_agent_logs(self, client):
        """Test getting agent logs"""
        test_client, mock_manager = client

        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id)
        mock_manager.get_agent.return_value = mock_agent
        mock_manager.get_agent_logs = AsyncMock(return_value=[{"level": "info", "msg": "test"}])

        response = test_client.get(f"/api/v1/agents/{agent_id}/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert len(data["logs"]) == 1

    def test_broadcast_message(self, client):
        """Test broadcasting message to all agents"""
        test_client, mock_manager = client
        mock_manager.broadcast = AsyncMock()

        response = test_client.post(
            "/api/v1/agents/broadcast",
            params={"message": "System maintenance in 5 minutes"},
        )

        assert response.status_code == 200
        assert "broadcast sent" in response.json()["message"].lower()

    def test_get_system_status(self, client):
        """Test getting agent system status"""
        test_client, mock_manager = client

        mock_agent1 = create_mock_agent(state="running")
        mock_agent2 = create_mock_agent(state="idle")
        mock_agent3 = create_mock_agent(state="error")
        mock_manager.get_all_agents.return_value = [
            mock_agent1,
            mock_agent2,
            mock_agent3,
        ]
        mock_manager.shared_context = {"key1": "value1"}
        mock_manager.message_history = [{"msg": 1}, {"msg": 2}]

        response = test_client.get("/api/v1/agents/system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] == 3
        assert data["active_agents"] == 1
        assert data["idle_agents"] == 1
        assert data["error_agents"] == 1
        assert "shared_context_keys" in data
        assert data["message_queue_size"] == 2


# =============================================================================


@pytest.mark.unit
class TestReportRoutes:
    """Tests for api/routes/reports.py - Report Management Endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client with mocked reports"""

        from api.routes.reports import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/reports")

        with patch("api.routes.reports.SessionLocal") as mock_session:
            with patch("api.routes.reports.Report") as mock_report_class:
                mock_db = MagicMock()
                mock_session.return_value = mock_db
                yield TestClient(app), mock_db, mock_report_class

    def test_generate_executive_report(self, client):
        """Test generating executive report"""
        test_client, mock_db, _ = client

        with patch("api.routes.reports.ReportGenerator") as mock_gen:
            mock_gen.return_value.generate_executive_report = MagicMock()

            response = test_client.post(
                "/api/v1/reports/executive",
                json={
                    "scan_id": str(uuid4()),
                    "company_name": "Test Corp",
                    "pentest_start": "2024-01-01",
                    "pentest_end": "2024-01-15",
                    "format": "pdf",
                },
            )

        assert response.status_code == 202
        data = response.json()
        assert data["report_type"] == "executive"
        assert data["status"] == "generating"

    def test_generate_technical_report(self, client):
        """Test generating technical report"""
        test_client, mock_db, _ = client

        with patch("api.routes.reports.ReportGenerator") as mock_gen:
            mock_gen.return_value.generate_technical_report = MagicMock()

            response = test_client.post(
                "/api/v1/reports/technical",
                json={
                    "scan_id": str(uuid4()),
                    "include_evidence": True,
                    "include_remediation": True,
                    "format": "pdf",
                },
            )

        assert response.status_code == 202
        data = response.json()
        assert data["report_type"] == "technical"

    def test_generate_compliance_report(self, client):
        """Test generating compliance report"""
        test_client, mock_db, _ = client

        with patch("api.routes.reports.ReportGenerator") as mock_gen:
            mock_gen.return_value.generate_compliance_report = MagicMock()

            response = test_client.post(
                "/api/v1/reports/compliance",
                json={
                    "scan_id": str(uuid4()),
                    "framework": "owasp_top_10",
                    "format": "pdf",
                },
            )

        assert response.status_code == 202
        data = response.json()
        assert data["report_type"] == "compliance"
        assert "owasp" in data["title"].lower()

    def test_list_reports_empty(self, client):
        """Test listing reports when none exist"""
        test_client, mock_db, _ = client

        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        response = test_client.get("/api/v1/reports/")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_reports_with_data(self, client):
        """Test listing reports with data"""
        test_client, mock_db, _ = client

        mock_report = create_mock_report()
        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [mock_report]
        mock_db.query.return_value = mock_query

        response = test_client.get("/api/v1/reports/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Report"

    def test_list_reports_with_filters(self, client):
        """Test listing reports with filters"""
        test_client, mock_db, _ = client

        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        response = test_client.get("/api/v1/reports/?scan_id=test123&report_type=executive&status=completed")

        assert response.status_code == 200

    def test_list_reports_pagination(self, client):
        """Test listing reports with pagination"""
        test_client, mock_db, _ = client

        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        response = test_client.get("/api/v1/reports/?page=2&page_size=20")

        assert response.status_code == 200
        # Offset should be (page-1) * page_size = 20

    def test_get_report_success(self, client):
        """Test getting a specific report"""
        test_client, mock_db, _ = client

        report_id = str(uuid4())
        mock_report = create_mock_report(report_id=report_id)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        response = test_client.get(f"/api/v1/reports/{report_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id

    def test_get_report_not_found(self, client):
        """Test getting a non-existent report"""
        test_client, mock_db, _ = client
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = test_client.get(f"/api/v1/reports/{uuid4()}")

        assert response.status_code == 404

    def test_download_report_success(self, client, tmp_path):
        """Test downloading a report file"""
        test_client, mock_db, _ = client

        report_id = str(uuid4())
        mock_report = create_mock_report(report_id=report_id)
        mock_report.title = "Test Report"
        mock_report.report_format.value = "pdf"

        # Create a temporary file
        test_file = tmp_path / "test_report.pdf"
        test_file.write_text("PDF content")
        mock_report.file_path = str(test_file)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        response = test_client.get(f"/api/v1/reports/{report_id}/download")

        assert response.status_code == 200

    def test_download_report_not_found(self, client):
        """Test downloading a non-existent report"""
        test_client, mock_db, _ = client
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = test_client.get(f"/api/v1/reports/{uuid4()}/download")

        assert response.status_code == 404

    def test_download_report_file_not_exists(self, client):
        """Test downloading when file doesn't exist"""
        test_client, mock_db, _ = client

        report_id = str(uuid4())
        mock_report = create_mock_report(report_id=report_id)
        mock_report.file_path = "/nonexistent/file.pdf"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        response = test_client.get(f"/api/v1/reports/{report_id}/download")

        assert response.status_code == 404

    def test_delete_report_success(self, client, tmp_path):
        """Test deleting a report"""
        test_client, mock_db, _ = client

        report_id = str(uuid4())
        mock_report = create_mock_report(report_id=report_id)

        # Create a temporary file
        test_file = tmp_path / "test_report.pdf"
        test_file.write_text("PDF content")
        mock_report.file_path = str(test_file)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        response = test_client.delete(f"/api/v1/reports/{report_id}")

        assert response.status_code == 204

    def test_delete_report_not_found(self, client):
        """Test deleting a non-existent report"""
        test_client, mock_db, _ = client
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = test_client.delete(f"/api/v1/reports/{uuid4()}")

        assert response.status_code == 404

    def test_get_report_statistics(self, client):
        """Test getting report statistics"""
        test_client, mock_db, _ = client

        # Mock count
        mock_db.query.return_value.count.return_value = 10
        # Mock group by queries
        mock_db.query.return_value.group_by.return_value.all.side_effect = [
            [
                (MagicMock(value="executive"), 5),
                (MagicMock(value="technical"), 5),
            ],  # by type
            [
                (MagicMock(value="pdf"), 8),
                (MagicMock(value="html"), 2),
            ],  # by format
        ]
        # Mock recent reports
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        response = test_client.get("/api/v1/reports/stats/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_reports"] == 10

    def test_list_report_templates(self, client):
        """Test listing available report templates"""
        test_client, _, _ = client

        response = test_client.get("/api/v1/reports/templates/list")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) >= 3


# =============================================================================


@pytest.mark.unit
class TestAdditionalAgentTests:
    """Additional agent tests"""

    @pytest.fixture
    def client(self):
        from api.routes.agents import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/agents")

        with patch("api.routes.agents.agent_manager") as mock_manager:
            with patch("api.routes.agents.get_current_user") as mock_auth:
                with patch("api.routes.agents.require_permissions") as mock_perms:
                    mock_auth.return_value = create_mock_user(role="ADMIN")
                    mock_perms.return_value = lambda: create_mock_user(role="ADMIN")
                    yield TestClient(app), mock_manager

    def test_list_agents_single_agent(self, client):
        """Test listing with single agent"""
        test_client, mock_manager = client
        mock_agent = create_mock_agent()
        mock_manager.get_all_agents.return_value = [mock_agent]

        response = test_client.get("/api/v1/agents/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_agents_many_agents(self, client):
        """Test listing with many agents"""
        test_client, mock_manager = client
        mock_manager.get_all_agents.return_value = [create_mock_agent() for _ in range(50)]

        response = test_client.get("/api/v1/agents/")
        assert response.status_code == 200
        assert len(response.json()) == 50

    def test_agent_task_invalid_priority(self, client):
        """Test task assignment with invalid priority"""
        test_client, mock_manager = client
        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id, state="running")
        mock_manager.get_agent.return_value = mock_agent

        response = test_client.post(
            f"/api/v1/agents/{agent_id}/task",
            json={"agent_id": agent_id, "task_type": "scan", "priority": 100},
        )
        assert response.status_code in [200, 422]

    def test_agent_message_empty(self, client):
        """Test sending empty message"""
        test_client, mock_manager = client
        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id)
        mock_manager.get_agent.return_value = mock_agent
        mock_manager.send_message_to_agent = AsyncMock(return_value={})

        response = test_client.post(
            f"/api/v1/agents/{agent_id}/message",
            json={"agent_id": agent_id, "message": "", "context": {}},
        )
        assert response.status_code == 200

    def test_agent_logs_limit_zero(self, client):
        """Test getting logs with limit 0"""
        test_client, mock_manager = client
        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id)
        mock_manager.get_agent.return_value = mock_agent
        mock_manager.get_agent_logs = AsyncMock(return_value=[])

        response = test_client.get(f"/api/v1/agents/{agent_id}/logs?limit=0")
        assert response.status_code == 200

    def test_agent_logs_large_limit(self, client):
        """Test getting logs with large limit"""
        test_client, mock_manager = client
        agent_id = str(uuid4())
        mock_agent = create_mock_agent(agent_id=agent_id)
        mock_manager.get_agent.return_value = mock_agent
        mock_manager.get_agent_logs = AsyncMock(return_value=[{"log": "test"}] * 1000)

        response = test_client.get(f"/api/v1/agents/{agent_id}/logs?limit=10000")
        assert response.status_code == 200


@pytest.mark.unit
class TestAdditionalFindingTests:
    pass


@pytest.mark.unit
class TestAdditionalReportTests:
    """Additional report tests"""

    @pytest.fixture
    def client(self):
        from api.routes.reports import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/reports")

        with patch("api.routes.reports.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            yield TestClient(app), mock_db

    def test_generate_report_all_compliance_frameworks(self, client):
        """Test generating compliance reports for all frameworks"""
        test_client, mock_db = client

        frameworks = ["owasp", "iso27001", "pci_dss", "nist_csf"]
        for framework in frameworks:
            with patch("api.routes.reports.ReportGenerator") as mock_gen:
                mock_gen.return_value.generate_compliance_report = MagicMock()
                response = test_client.post(
                    "/api/v1/reports/compliance",
                    json={"scan_id": str(uuid4()), "framework": framework},
                )
                assert response.status_code == 202

    def test_list_reports_invalid_page(self, client):
        """Test listing reports with invalid page"""
        test_client, mock_db = client
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        response = test_client.get("/api/v1/reports/?page=0")
        assert response.status_code in [200, 422]

    def test_list_reports_large_page_size(self, client):
        """Test listing reports with large page size"""
        test_client, mock_db = client
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        response = test_client.get("/api/v1/reports/?page_size=1000")
        assert response.status_code in [200, 422]

    def test_download_report_no_path(self, client):
        """Test downloading report without file path"""
        test_client, mock_db = client
        report_id = str(uuid4())
        mock_report = create_mock_report(report_id=report_id)
        mock_report.file_path = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report

        response = test_client.get(f"/api/v1/reports/{report_id}/download")
