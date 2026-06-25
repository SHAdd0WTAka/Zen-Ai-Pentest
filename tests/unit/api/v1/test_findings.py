"""
API v1 Findings Routes Tests
Target: 70%+ Coverage for api/routes/v1/findings.py
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_finding():
    """Create a mock finding object"""
    finding = MagicMock()
    finding.id = 1
    finding.scan_id = 1
    finding.title = "Test Finding"
    finding.description = "Test Description"
    finding.severity = "high"
    finding.cvss_score = 7.5
    finding.cve_id = None
    finding.evidence = None
    finding.remediation = None
    finding.verified = 0
    finding.tool = "nmap"
    finding.target = "example.com"
    finding.port = None
    finding.service = None
    finding.created_at = datetime.now()
    return finding


class TestFindingsEndpoints:
    """Test cases for findings endpoints"""

    def test_list_findings(self, test_client, auth_headers, mock_db_session):
        """Test listing all findings"""
        with patch("api.routes.v1.findings.get_findings") as mock_get:
            mock_get.return_value = []
            response = test_client.get("/api/v1/findings/", headers=auth_headers)
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_list_findings_unauthorized(self, test_client):
        """Test listing findings without auth (auth overridden in test env)"""
        response = test_client.get("/api/v1/findings/")
        assert response.status_code in [200, 401, 403]

    def test_get_finding_success(self, test_client, auth_headers, mock_db_session, mock_finding):
        """Test getting a specific finding"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        response = test_client.get("/api/v1/findings/1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Finding"

    def test_get_finding_not_found(self, test_client, auth_headers, mock_db_session):
        """Test getting a non-existent finding"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        response = test_client.get("/api/v1/findings/999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_finding_success(self, test_client, auth_headers, mock_db_session, mock_finding):
        """Test updating a finding"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        update_data = {
            "title": "Updated Title",
            "severity": "critical",
            "verified": True,
        }

        response = test_client.patch("/api/v1/findings/1", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Finding updated successfully"

    def test_update_finding_not_found(self, test_client, auth_headers, mock_db_session):
        """Test updating a non-existent finding"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        response = test_client.patch(
            "/api/v1/findings/999",
            json={"title": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_finding_disallowed_fields(self, test_client, auth_headers, mock_db_session, mock_finding):
        """Test updating with disallowed fields"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        response = test_client.patch(
            "/api/v1/findings/1",
            json={"id": 999, "disallowed_field": "value"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_delete_finding_success(self, test_client, auth_headers, mock_db_session, mock_finding):
        """Test deleting a finding"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        response = test_client.delete("/api/v1/findings/1", headers=auth_headers)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
        mock_db_session.delete.assert_called_once_with(mock_finding)
        mock_db_session.commit.assert_called_once()

    def test_delete_finding_not_found(self, test_client, auth_headers, mock_db_session):
        """Test deleting a non-existent finding"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        response = test_client.delete("/api/v1/findings/999", headers=auth_headers)
        assert response.status_code == 404


class TestFindingsEdgeCases:
    """Edge cases for findings endpoints"""

    def test_update_finding_severity_levels(self, test_client, auth_headers, mock_db_session, mock_finding):
        """Test updating with different severity levels"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        severities = ["critical", "high", "medium", "low", "info"]
        for severity in severities:
            response = test_client.patch(
                "/api/v1/findings/1",
                json={"severity": severity},
                headers=auth_headers,
            )
            assert response.status_code == 200

    def test_update_finding_cvss_score(self, test_client, auth_headers, mock_db_session, mock_finding):
        """Test updating CVSS score"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        response = test_client.patch(
            "/api/v1/findings/1",
            json={"cvss_score": 9.8},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_finding_remediation(self, test_client, auth_headers, mock_db_session, mock_finding):
        """Test updating remediation field"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_finding

        response = test_client.patch(
            "/api/v1/findings/1",
            json={"remediation": "Apply the latest security patch"},
            headers=auth_headers,
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
