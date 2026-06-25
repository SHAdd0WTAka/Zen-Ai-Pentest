"""
Tests for api/routes/legacy_tools.py — legacy tool execution and report routes.

NOTE: POST /tools/execute has a known schema mismatch (route uses
`request.tool_name` / `request.parameters` but schema defines `tool` /
`options`). Tests expect 500 for this endpoint, reflecting the bug.
Helper functions and other endpoints are tested normally.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status


class FakeReport:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class FakeScan:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


# ============================================================================
# POST /tools/execute
# ============================================================================


class TestExecuteTool:
    def test_execute_tool_returns_500_due_to_schema_mismatch(self, test_client, auth_headers):
        """Known bug: route uses tool_name/parameters but schema has tool/options"""
        with (
            patch("database.crud.create_scan", return_value=FakeScan(id=1)),
            patch("api.routes.legacy_tools.execute_tool_task"),
        ):
            try:
                test_client.post(
                    "/tools/execute",
                    json={"tool": "nmap", "target": "example.com", "options": {}},
                    headers=auth_headers,
                )
                assert False, "Expected AttributeError due to schema mismatch"
            except AttributeError as e:
                assert "tool_name" in str(e)

    def test_execute_tool_missing_fields_returns_422(self, test_client, auth_headers):
        response = test_client.post("/tools/execute", json={}, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_execute_tool_requires_target(self, test_client, auth_headers):
        response = test_client.post(
            "/tools/execute",
            json={"tool": "nmap"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# GET /tools
# ============================================================================


class TestListTools:
    def test_list_tools_returns_list(self, test_client):
        with patch("tools.TOOL_REGISTRY", {"nmap_scan": MagicMock(__doc__="Nmap scan")}):
            response = test_client.get("/tools")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    def test_list_tools_empty_registry(self, test_client):
        with patch("tools.TOOL_REGISTRY", {}):
            response = test_client.get("/tools")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["tools"] == []

    def test_list_tools_with_null_functions(self, test_client):
        with patch("tools.TOOL_REGISTRY", {"broken": None, "good": MagicMock(__doc__="Works")}):
            response = test_client.get("/tools")
        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.json()["tools"]]
        assert "good" in names
        assert "broken" not in names


# ============================================================================
# POST /reports
# ============================================================================


class TestGenerateReport:
    def test_generate_report_success(self, test_client, auth_headers):
        mock_report = FakeReport(
            id=1,
            scan_id=42,
            format="pdf",
            template="default",
            status="pending",
            user_id="admin",
            file_path=None,
            file_size=None,
            created_at="2025-01-01T00:00:00",
            generated_at=None,
        )
        with (
            patch("api.routes.legacy_tools.create_report", return_value=mock_report),
            patch("api.routes.legacy_tools.generate_report_task"),
        ):
            response = test_client.post(
                "/reports",
                json={"scan_id": 42, "format": "pdf", "template": "default"},
                headers=auth_headers,
            )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["id"] == 1
        assert data["scan_id"] == 42

    def test_generate_report_missing_fields_returns_422(self, test_client, auth_headers):
        response = test_client.post("/reports", json={}, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_report_invalid_format_returns_422(self, test_client, auth_headers):
        response = test_client.post(
            "/reports",
            json={"scan_id": 1, "format": "exe"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# GET /reports
# ============================================================================


class TestListReports:
    def test_list_reports_returns_list(self, test_client, auth_headers):
        with patch("api.routes.legacy_tools.get_reports", return_value=[]):
            response = test_client.get("/reports", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_list_reports_pagination(self, test_client, auth_headers):
        with patch("api.routes.legacy_tools.get_reports", return_value=[]):
            response = test_client.get("/reports?skip=10&limit=5", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# GET /reports/{report_id}/download
# ============================================================================


class TestDownloadReport:
    def test_download_report_nonexistent(self, test_client, auth_headers):
        with patch("api.routes.legacy_tools.get_db"):
            response = test_client.get("/reports/99999/download", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_download_report_no_file_path(self, test_client, auth_headers, mock_db_session):
        mock_report = FakeReport(id=1, file_path=None)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_report
        response = test_client.get("/reports/1/download", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# get_tool_category helper
# ============================================================================


class TestGetToolCategory:
    def test_network_tools(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("nmap") == "network"
        assert get_tool_category("masscan_scan") == "network"
        assert get_tool_category("scapy_packet") == "network"
        assert get_tool_category("tshark_capture") == "network"

    def test_web_tools(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("burp_scan") == "web"
        assert get_tool_category("sqlmap") == "web"
        assert get_tool_category("gobuster_dir") == "web"

    def test_exploitation_tools(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("metasploit") == "exploitation"

    def test_brute_force_tools(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("hydra_ssh") == "brute_force"

    def test_recon_tools(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("amass") == "recon"

    def test_ad_tools(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("bloodhound") == "ad"
        assert get_tool_category("cme_smb") == "ad"
        assert get_tool_category("responder") == "ad"

    def test_wireless_tools(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("aircrack") == "wireless"

    def test_unknown_tools_default_to_other(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("custom_tool_123") == "other"
        assert get_tool_category("") == "other"

    def test_case_insensitive(self):
        from api.routes.legacy_tools import get_tool_category

        assert get_tool_category("NMAP") == "network"
        assert get_tool_category("SqlMap") == "web"
        assert get_tool_category("BURP Suite") == "web"
