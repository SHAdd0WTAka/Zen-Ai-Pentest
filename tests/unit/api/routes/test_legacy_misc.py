"""
Tests for api/routes/legacy_misc.py — legacy stats, notification, and rate-limit endpoints.

NOTE: Many dependencies are imported at function level. Patches target
source modules. The /health endpoint may be overridden by a different
router — test adjusts expectations accordingly.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

pytestmark = pytest.mark.usefixtures("test_client")


# ============================================================================
# STATS endpoints
# ============================================================================


class TestStatsOverview:
    def test_stats_overview_returns_counts(self, test_client, mock_db_session):
        mock_db_session.query.return_value.count.return_value = 5
        mock_db_session.query.return_value.filter.return_value.count.return_value = 3
        mock_db_session.query.return_value.group_by.return_value.all.return_value = [("critical", 2), ("high", 1)]
        with patch("api.routes.legacy_misc.calculate_trends", return_value=[]):
            with patch("api.routes.legacy_misc.get_tool_usage_stats", return_value=[]):
                response = test_client.get("/stats/overview")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_scans"] == 5
        assert data["total_findings"] == 5
        assert "severity_distribution" in data

    def test_stats_overview_fills_missing_severities(self, test_client, mock_db_session):
        mock_db_session.query.return_value.count.return_value = 0
        mock_db_session.query.return_value.filter.return_value.count.return_value = 0
        mock_db_session.query.return_value.group_by.return_value.all.return_value = []
        with patch("api.routes.legacy_misc.calculate_trends", return_value=[]):
            with patch("api.routes.legacy_misc.get_tool_usage_stats", return_value=[]):
                response = test_client.get("/stats/overview")
        assert response.status_code == status.HTTP_200_OK
        severities = {s["name"].lower() for s in response.json()["severity_distribution"]}
        for sev in ["critical", "high", "medium", "low", "info"]:
            assert sev in severities


class TestStatsTrends:
    def test_stats_trends_returns_list(self, test_client, mock_db_session):
        with patch(
            "api.routes.legacy_misc.calculate_trends",
            return_value=[{"date": "2025-01-01", "count": 3, "severity_breakdown": {}}],
        ):
            response = test_client.get("/stats/trends?days=7")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_stats_trends_default_days(self, test_client, mock_db_session):
        with patch("api.routes.legacy_misc.calculate_trends", return_value=[]):
            response = test_client.get("/stats/trends")
        assert response.status_code == status.HTTP_200_OK


class TestSeverityStats:
    def test_severity_stats_returns_list(self, test_client, mock_db_session):
        mock_db_session.query.return_value.group_by.return_value.all.return_value = [("critical", 3), ("low", 1)]
        response = test_client.get("/stats/severity")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_severity_stats_empty(self, test_client, mock_db_session):
        mock_db_session.query.return_value.group_by.return_value.all.return_value = []
        response = test_client.get("/stats/severity")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


class TestToolUsageStats:
    def test_tool_usage_returns_list(self, test_client, mock_db_session):
        with patch(
            "api.routes.legacy_misc.get_tool_usage_stats",
            return_value=[{"tool_name": "nmap", "execution_count": 5, "avg_duration": 10.5}],
        ):
            response = test_client.get("/stats/tools")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]["tool_name"] == "nmap"


# ============================================================================
# Helper: get_severity_color
# ============================================================================


class TestGetSeverityColor:
    def test_known_severities(self):
        from api.routes.legacy_misc import get_severity_color

        assert get_severity_color("critical") == "#ef4444"
        assert get_severity_color("high") == "#f97316"
        assert get_severity_color("medium") == "#eab308"
        assert get_severity_color("low") == "#22c55e"
        assert get_severity_color("info") == "#3b82f6"

    def test_case_insensitive(self):
        from api.routes.legacy_misc import get_severity_color

        assert get_severity_color("CRITICAL") == "#ef4444"

    def test_unknown_severity(self):
        from api.routes.legacy_misc import get_severity_color

        assert get_severity_color("unknown") == "#6b7280"


# ============================================================================
# Helper: calculate_trends
# ============================================================================


class TestCalculateTrends:
    def test_calculate_trends_no_db_returns_empty(self):
        from api.routes.legacy_misc import calculate_trends

        assert calculate_trends(db=None) == []

    def test_calculate_trends_returns_data(self):
        from api.routes.legacy_misc import calculate_trends

        mock_db = MagicMock()
        q1 = MagicMock()
        q1.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            ("2025-01-01", 3),
        ]
        q2 = MagicMock()
        q2.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("2025-01-01", "critical", 2),
        ]
        mock_db.query.side_effect = [q1, q2]
        with patch("database.models.DATABASE_URL", "sqlite:///test.db", create=True):
            result = calculate_trends(days=30, db=mock_db)
        assert len(result) == 1
        assert result[0]["date"] == "2025-01-01"
        assert result[0]["count"] == 3


class TestGetToolUsageStats:
    def test_no_db_returns_empty(self):
        from api.routes.legacy_misc import get_tool_usage_stats

        assert get_tool_usage_stats(db=None) == []

    def test_returns_usage_stats(self):
        from api.routes.legacy_misc import get_tool_usage_stats

        mock_db = MagicMock()
        q1 = MagicMock()
        q1.join.return_value.filter.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            ("nmap", 5),
        ]
        q2 = MagicMock()
        q2.join.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("nmap", 0.5),
        ]
        mock_db.query.side_effect = [q1, q2]
        result = get_tool_usage_stats(days=30, db=mock_db)
        assert len(result) == 1
        assert result[0]["tool_name"] == "nmap"
        assert result[0]["execution_count"] == 5


# ============================================================================
# NOTIFICATIONS / SLACK
# ============================================================================


class TestSlackNotification:
    def test_test_slack_success(self, test_client, auth_headers):
        mock_notifier = MagicMock()
        mock_notifier.send_message.return_value = True
        with (
            patch("notifications.slack.SlackNotifier", return_value=mock_notifier, create=True),
            patch("api.routes.legacy_settings._validate_slack_webhook_url", return_value="https://hooks.slack.com/valid"),
        ):
            response = test_client.post(
                "/notifications/slack/test?webhook_url=https://hooks.slack.com/valid",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    def test_test_slack_fails(self, test_client, auth_headers):
        mock_notifier = MagicMock()
        mock_notifier.send_message.return_value = False
        with (
            patch("notifications.slack.SlackNotifier", return_value=mock_notifier, create=True),
            patch("api.routes.legacy_settings._validate_slack_webhook_url", return_value="https://hooks.slack.com/valid"),
        ):
            response = test_client.post(
                "/notifications/slack/test?webhook_url=https://hooks.slack.com/valid",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestSlackScanComplete:
    def test_scan_complete_success(self, test_client, auth_headers, mock_db_session):
        mock_scan = MagicMock()
        mock_scan.id = 1
        mock_scan.target = "example.com"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_scan

        mock_finding = MagicMock()
        mock_finding.severity = "critical"
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_finding]

        mock_notifier = MagicMock()
        mock_notifier.send_scan_completed.return_value = True
        with (
            patch("notifications.slack.SlackNotifier", return_value=mock_notifier, create=True),
            patch("api.routes.legacy_settings._validate_slack_webhook_url", return_value="https://hooks.slack.com/valid"),
        ):
            response = test_client.post(
                "/notifications/slack/scan-complete?scan_id=1&webhook_url=https://hooks.slack.com/valid",
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    def test_scan_complete_not_found(self, test_client, auth_headers, mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        response = test_client.post(
            "/notifications/slack/scan-complete?scan_id=999&webhook_url=https://hooks.slack.com/test",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Rate Limiting Demo Endpoints
# ============================================================================


class TestHealthCheck:
    def test_health_returns_healthy(self, test_client):
        response = test_client.get("/health")
        assert response.status_code in (200, 429)
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "healthy"


class TestListScansV2:
    def test_list_scans_v2_with_auth(self, test_client, auth_headers):
        response = test_client.get("/api/scans", headers=auth_headers)
        assert response.status_code in (200, 429)
        if response.status_code == 200:
            data = response.json()
            assert "scans" in data
            assert "user" in data


class TestPublicStatus:
    def test_public_status_returns_operational(self, test_client):
        response = test_client.get("/api/public/status")
        assert response.status_code in (200, 429)
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "operational"
            assert "version" in data


class TestCustomLimitEndpoint:
    def test_custom_limit_endpoint(self, test_client):
        response = test_client.get("/api/custom-limit")
        assert response.status_code in (200, 429)
        if response.status_code == 200:
            data = response.json()
            assert data["limit"] == 50


class TestLegacyStyleEndpoint:
    def test_legacy_style_endpoint(self, test_client):
        response = test_client.get("/api/legacy-style")
        assert response.status_code in (200, 429)
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
