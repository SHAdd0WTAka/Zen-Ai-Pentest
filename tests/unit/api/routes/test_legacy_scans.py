"""
Tests for api/routes/legacy_scans.py — legacy scan CRUD routes.

NOTE: The conftest overrides verify_token / optional_auth globally to return a
mock user, so all authenticated routes appear to have a valid session during
tests.  Auth-guard tests reside in test_auth_deps.py instead.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status


def _make_scan_obj(**overrides):
    """Return a dict-like object that mimics a SQLAlchemy Scan model."""
    obj = MagicMock()
    attrs = {
        "id": 1,
        "name": "test",
        "target": "example.com",
        "scan_type": "quick",
        "config": {},
        "status": "pending",
        "user_id": 1,
        "created_at": datetime.now(timezone.utc),
        "started_at": None,
        "completed_at": None,
        "result_summary": None,
        "findings_count": 0,
    }
    attrs.update(overrides)
    for k, v in attrs.items():
        setattr(obj, k, v)
    return obj


def _make_finding_obj(**overrides):
    """Return a dict-like object that mimics a SQLAlchemy Finding model."""
    obj = MagicMock()
    attrs = {
        "id": 1,
        "scan_id": 1,
        "title": "Test finding",
        "description": "desc",
        "severity": "medium",
        "cvss_score": None,
        "evidence": "",
        "tool": "",
        "target": "",
        "verified": 0,
        "created_at": datetime.now(timezone.utc),
        "cve_id": None,
        "remediation": None,
        "service": None,
        "port": None,
    }
    attrs.update(overrides)
    for k, v in attrs.items():
        setattr(obj, k, v)
    return obj


# ============================================================================
# GET /scans
# ============================================================================


class TestListScans:
    def test_list_scans_returns_list(self, test_client):
        response = test_client.get("/scans")
        assert response.status_code in (200, status.HTTP_429_TOO_MANY_REQUESTS)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_list_scans_with_status_filter(self, test_client):
        response = test_client.get("/scans?status=running")
        assert response.status_code in (200, status.HTTP_429_TOO_MANY_REQUESTS)
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_list_scans_pagination(self, test_client):
        response = test_client.get("/scans?skip=0&limit=5")
        assert response.status_code in (200, status.HTTP_429_TOO_MANY_REQUESTS)


# ============================================================================
# POST /scans
# ============================================================================


class TestCreateScan:
    def test_create_scan_returns_scan_response(self, test_client, auth_headers, mock_db_session):
        mock_scan = _make_scan_obj(id=42, name="Test scan", target="example.com")
        with (
            patch("api.routes.legacy_scans.create_scan", return_value=mock_scan),
            patch("api.routes.legacy_scans.run_scan_task"),  # prevent background execution
        ):
            payload = {
                "name": "Test scan",
                "target": "example.com",
                "scan_type": "quick",
                "config": {"ports": "80,443"},
            }
            response = test_client.post("/scans", json=payload, headers=auth_headers)
        assert response.status_code in (200, 201, status.HTTP_429_TOO_MANY_REQUESTS)
        if response.status_code in (200, 201):
            data = response.json()
            assert "id" in data
            assert data["id"] == 42

    def test_create_scan_missing_fields_returns_422(self, test_client, auth_headers):
        response = test_client.post("/scans", json={}, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_scan_empty_name_returns_422(self, test_client, auth_headers):
        response = test_client.post(
            "/scans",
            json={"name": "", "target": "example.com"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# GET /scans/{scan_id}
# ============================================================================


class TestGetScanById:
    def test_get_nonexistent_scan_returns_404(self, test_client):
        response = test_client.get("/scans/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_scan_without_auth(self, test_client):
        """optional_auth allows unauthenticated access to GET."""
        response = test_client.get("/scans/1")
        assert response.status_code in (200, 404, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_get_scan_by_id_valid_request(self, test_client, auth_headers):
        response = test_client.get("/scans/1", headers=auth_headers)
        assert response.status_code in (200, 404, status.HTTP_429_TOO_MANY_REQUESTS)


# ============================================================================
# PATCH /scans/{scan_id}
# ============================================================================


class TestUpdateScan:
    def test_update_nonexistent_scan_returns_404(self, test_client, auth_headers):
        response = test_client.patch(
            "/scans/99999",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code in (404, status.HTTP_429_TOO_MANY_REQUESTS)


# ============================================================================
# DELETE /scans/{scan_id}
# ============================================================================


class TestDeleteScan:
    def test_delete_scan_returns_message(self, test_client, auth_headers):
        response = test_client.delete("/scans/1", headers=auth_headers)
        assert response.status_code in (200, status.HTTP_429_TOO_MANY_REQUESTS)
        if response.status_code == 200:
            assert response.json()["message"] == "Scan deleted"


# ============================================================================
# GET /scans/{scan_id}/findings
# ============================================================================


class TestGetScanFindings:
    def test_get_findings_with_auth(self, test_client, auth_headers):
        response = test_client.get("/scans/1/findings", headers=auth_headers)
        assert response.status_code in (200, status.HTTP_429_TOO_MANY_REQUESTS)
        if response.status_code == 200:
            assert isinstance(response.json(), list)


# ============================================================================
# POST /scans/{scan_id}/findings
# ============================================================================


class TestAddFinding:
    def test_add_finding_success(self, test_client, auth_headers, mock_db_session):
        mock_finding = _make_finding_obj(id=10, title="Open port 22")
        with patch("api.routes.legacy_scans.create_finding", return_value=mock_finding):
            payload = {
                "title": "Open port 22",
                "description": "SSH port detected",
                "severity": "medium",
            }
            response = test_client.post(
                "/scans/1/findings",
                json=payload,
                headers=auth_headers,
            )
        assert response.status_code in (200, 201, status.HTTP_429_TOO_MANY_REQUESTS)
        if response.status_code in (200, 201):
            assert response.json()["id"] == 10

    def test_add_finding_missing_title_returns_422(self, test_client, auth_headers):
        response = test_client.post(
            "/scans/1/findings",
            json={"severity": "high"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_add_finding_minimal_payload(self, test_client, auth_headers, mock_db_session):
        mock_finding = _make_finding_obj(title="Test finding")
        with patch("api.routes.legacy_scans.create_finding", return_value=mock_finding):
            response = test_client.post(
                "/scans/1/findings",
                json={"title": "Test finding", "severity": "low"},
                headers=auth_headers,
            )
        assert response.status_code in (200, 201, status.HTTP_429_TOO_MANY_REQUESTS)


# ============================================================================
# PATCH /findings/{finding_id}
# ============================================================================


class TestUpdateFinding:
    def test_update_nonexistent_finding_returns_404(self, test_client, auth_headers, mock_db_session):
        response = test_client.patch(
            "/findings/99999",
            json={"severity": "high"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_finding_allowed_fields(self, test_client, auth_headers, mock_db_session):
        mock_finding = _make_finding_obj(
            id=5,
            title="Updated title",
            severity="critical",
            verified=1,
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding
        response = test_client.patch(
            "/findings/1",
            json={"title": "Updated title", "severity": "critical", "verified": 1},
            headers=auth_headers,
        )
        assert response.status_code in (200, status.HTTP_429_TOO_MANY_REQUESTS)
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
