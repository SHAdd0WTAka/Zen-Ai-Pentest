"""
Tests for api/routes/legacy_settings.py — legacy settings and integration routes.

NOTE: JIRA_CONFIG and get_jira_client are imported at function level from
integrations.jira_client. Patches target the source module.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

pytestmark = pytest.mark.usefixtures("test_client")


MOCK_JIRA_CONFIG = {
    "enabled": False,
    "base_url": None,
    "username": None,
    "api_token": None,
}

MOCK_JIRA_CONFIG_CONFIGURED = {
    "enabled": True,
    "base_url": "https://jira.example.com",
    "username": "bot",
    "api_token": "token",
}


# ============================================================================
# GET /settings/slack
# ============================================================================


class TestGetSlackSettings:
    def test_get_slack_settings_returns_status(self, test_client, auth_headers):
        with patch("api.routes.legacy_settings.SLACK_CONFIG", {"webhook_url": None, "enabled": False}):
            response = test_client.get("/settings/slack", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "enabled" in data
        assert "configured" in data
        assert data["configured"] is False

    def test_get_slack_settings_configured(self, test_client, auth_headers):
        with patch("api.routes.legacy_settings.SLACK_CONFIG", {"webhook_url": "https://hooks.slack.com/xxx", "enabled": True}):
            response = test_client.get("/settings/slack", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["enabled"] is True
        assert data["configured"] is True


# ============================================================================
# POST /settings/slack
# ============================================================================


class TestUpdateSlackSettings:
    def test_update_slack_settings_success(self, test_client, auth_headers):
        with patch("api.routes.legacy_settings._validate_slack_webhook_url", return_value="https://hooks.slack.com/valid"):
            response = test_client.post(
                "/settings/slack?webhook_url=https://hooks.slack.com/valid&enabled=true",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    def test_update_slack_settings_disabled(self, test_client, auth_headers):
        with patch("api.routes.legacy_settings._validate_slack_webhook_url", return_value="https://hooks.slack.com/valid"):
            response = test_client.post(
                "/settings/slack?webhook_url=https://hooks.slack.com/valid&enabled=false",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# GET /settings/jira
# ============================================================================


class TestGetJiraSettings:
    def test_get_jira_settings_not_configured(self, test_client, auth_headers):
        with patch("integrations.jira_client.JIRA_CONFIG", MOCK_JIRA_CONFIG, create=True):
            response = test_client.get("/settings/jira", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["configured"] is False

    def test_get_jira_settings_configured(self, test_client, auth_headers):
        with patch("integrations.jira_client.JIRA_CONFIG", MOCK_JIRA_CONFIG_CONFIGURED, create=True):
            response = test_client.get("/settings/jira", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["enabled"] is True
        assert data["configured"] is True
        assert data["base_url"] == "https://jira.example.com"


# ============================================================================
# POST /settings/jira
# ============================================================================


class TestUpdateJiraSettings:
    def test_update_jira_settings_success(self, test_client, auth_headers):
        with patch("integrations.jira_client.JIRA_CONFIG", MOCK_JIRA_CONFIG, create=True):
            response = test_client.post(
                "/settings/jira?base_url=https://jira.example.com&username=bot&api_token=abc123",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"


# ============================================================================
# POST /settings/jira/test
# ============================================================================


class TestTestJiraConnection:
    def test_jira_test_success(self, test_client, auth_headers):
        mock_client = MagicMock()
        mock_client.test_connection.return_value = True
        with patch("integrations.jira_client.get_jira_client", return_value=mock_client, create=True):
            response = test_client.post("/settings/jira/test", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    def test_jira_test_not_configured(self, test_client, auth_headers):
        with patch("integrations.jira_client.get_jira_client", return_value=None, create=True):
            response = test_client.post("/settings/jira/test", headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_jira_test_connection_fails(self, test_client, auth_headers):
        mock_client = MagicMock()
        mock_client.test_connection.return_value = False
        with patch("integrations.jira_client.get_jira_client", return_value=mock_client, create=True):
            response = test_client.post("/settings/jira/test", headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# GET /settings/jira/projects
# ============================================================================


class TestGetJiraProjects:
    def test_jira_projects_success(self, test_client, auth_headers):
        mock_client = MagicMock()
        mock_client.get_projects.return_value = [
            {"key": "PROJ", "name": "Project One"},
            {"key": "TEST", "name": "Test Project"},
        ]
        with patch("integrations.jira_client.get_jira_client", return_value=mock_client, create=True):
            response = test_client.get("/settings/jira/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["key"] == "PROJ"

    def test_jira_projects_not_configured(self, test_client, auth_headers):
        with patch("integrations.jira_client.get_jira_client", return_value=None, create=True):
            response = test_client.get("/settings/jira/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# POST /integrations/jira/create-ticket
# ============================================================================


class TestCreateJiraTicket:
    def test_create_ticket_success(self, test_client, auth_headers, mock_db_session):
        mock_finding = MagicMock()
        mock_finding.id = 1
        mock_finding.title = "Open port 22"
        mock_finding.description = "SSH port exposed"
        mock_finding.severity = "high"
        mock_finding.target = "example.com"
        mock_finding.tool = "nmap"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        mock_client = MagicMock()
        mock_client.create_finding_ticket.return_value = {"key": "PROJ-42"}
        mock_client.base_url = "https://jira.example.com"

        with patch("integrations.jira_client.get_jira_client", return_value=mock_client, create=True):
            response = test_client.post(
                "/integrations/jira/create-ticket?finding_id=1&project_key=PROJ",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["ticket_key"] == "PROJ-42"

    def test_create_ticket_jira_not_configured(self, test_client, auth_headers):
        with patch("integrations.jira_client.get_jira_client", return_value=None, create=True):
            response = test_client.post(
                "/integrations/jira/create-ticket?finding_id=1&project_key=PROJ",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_ticket_finding_not_found(self, test_client, auth_headers, mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_client = MagicMock()
        with patch("integrations.jira_client.get_jira_client", return_value=mock_client, create=True):
            response = test_client.post(
                "/integrations/jira/create-ticket?finding_id=999&project_key=PROJ",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_ticket_fails(self, test_client, auth_headers, mock_db_session):
        mock_finding = MagicMock(title="test", description="test", severity="low", target="t", tool="t")
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        mock_client = MagicMock()
        mock_client.create_finding_ticket.return_value = None

        with patch("integrations.jira_client.get_jira_client", return_value=mock_client, create=True):
            response = test_client.post(
                "/integrations/jira/create-ticket?finding_id=1&project_key=PROJ",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
