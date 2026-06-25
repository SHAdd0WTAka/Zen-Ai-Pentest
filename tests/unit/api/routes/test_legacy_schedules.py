"""
Tests for api/routes/legacy_schedules.py — legacy scheduled scan CRUD routes.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import status

pytestmark = pytest.mark.usefixtures("test_client")


def _sample_schedule(**overrides):
    base = {
        "id": 1,
        "name": "Weekly scan",
        "target": "example.com",
        "scan_type": "comprehensive",
        "frequency": "weekly",
        "schedule_time": "02:00",
        "schedule_day": 0,
        "enabled": True,
        "notification_email": None,
        "notification_slack": None,
        "last_run_at": None,
        "last_run_status": None,
        "next_run_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "created_by": "admin",
    }
    base.update(overrides)
    return base


# ============================================================================
# POST /schedules
# ============================================================================


class TestCreateSchedule:
    def test_create_schedule_success(self, test_client, auth_headers):
        response = test_client.post(
            "/schedules",
            json={
                "name": "Weekly scan",
                "target": "example.com",
                "scan_type": "comprehensive",
                "frequency": "weekly",
                "schedule_time": "02:00",
                "schedule_day": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["name"] == "Weekly scan"
        assert data["target"] == "example.com"
        assert data["frequency"] == "weekly"
        assert data["enabled"] is True

    def test_create_schedule_missing_name_returns_422(self, test_client, auth_headers):
        response = test_client.post(
            "/schedules",
            json={"target": "example.com", "frequency": "daily", "schedule_time": "02:00"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_schedule_invalid_time_format_returns_422(self, test_client, auth_headers):
        response = test_client.post(
            "/schedules",
            json={"name": "Test", "target": "example.com", "frequency": "daily", "schedule_time": "25:00"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# GET /schedules
# ============================================================================


class TestListSchedules:
    def test_list_schedules_returns_list(self, test_client, auth_headers):
        with patch("api.background.SCHEDULED_SCANS", [], create=True):
            response = test_client.get("/schedules", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_list_schedules_with_data(self, test_client, auth_headers):
        schedules = [_sample_schedule(id=1, name="Test1"), _sample_schedule(id=2, name="Test2")]
        with patch("api.background.SCHEDULED_SCANS", schedules, create=True):
            response = test_client.get("/schedules", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2


# ============================================================================
# GET /schedules/{schedule_id}
# ============================================================================


class TestGetSchedule:
    def test_get_schedule_found(self, test_client, auth_headers):
        schedules = [_sample_schedule(id=1, name="Test")]
        with patch("api.background.SCHEDULED_SCANS", schedules, create=True):
            response = test_client.get("/schedules/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == 1

    def test_get_schedule_not_found_returns_404(self, test_client, auth_headers):
        with patch("api.background.SCHEDULED_SCANS", [], create=True):
            response = test_client.get("/schedules/999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# PATCH /schedules/{schedule_id}
# ============================================================================


class TestUpdateSchedule:
    def test_update_schedule_name(self, test_client, auth_headers):
        schedules = [_sample_schedule(id=1, name="Old name", frequency="daily", schedule_time="02:00", schedule_day=None)]
        with patch("api.background.SCHEDULED_SCANS", schedules, create=True):
            response = test_client.patch(
                "/schedules/1",
                json={"name": "New name"},
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "New name"

    def test_update_schedule_not_found_returns_404(self, test_client, auth_headers):
        with patch("api.background.SCHEDULED_SCANS", [], create=True):
            response = test_client.patch(
                "/schedules/999",
                json={"name": "New name"},
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_schedule_frequency_recalculates_next_run(self, test_client, auth_headers):
        schedules = [_sample_schedule(id=1, name="Test", frequency="daily", schedule_time="02:00", schedule_day=None)]
        with (
            patch("api.background.SCHEDULED_SCANS", schedules, create=True),
            patch(
                "api.routes.legacy_schedules.calculate_next_run", return_value=datetime(2025, 6, 1, 2, 0, tzinfo=timezone.utc)
            ) as mock_calc,
        ):
            response = test_client.patch(
                "/schedules/1",
                json={"frequency": "weekly", "schedule_day": 2},
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_200_OK
        assert mock_calc.called


# ============================================================================
# DELETE /schedules/{schedule_id}
# ============================================================================


class TestDeleteSchedule:
    def test_delete_schedule_returns_message(self, test_client, auth_headers):
        schedules = [_sample_schedule(id=1, name="Test")]
        with patch("api.background.SCHEDULED_SCANS", schedules, create=True):
            response = test_client.delete("/schedules/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Schedule deleted"

    def test_delete_schedule_not_found_returns_404(self, test_client, auth_headers):
        with patch("api.background.SCHEDULED_SCANS", [], create=True):
            response = test_client.delete("/schedules/999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# POST /schedules/{schedule_id}/run
# ============================================================================


class TestRunScheduleNow:
    def test_run_schedule_triggers_scan(self, test_client, auth_headers):
        schedules = [_sample_schedule(id=1, name="Test", target="example.com")]
        with (
            patch("api.background.SCHEDULED_SCANS", schedules, create=True),
            patch("api.routes.legacy_schedules.execute_scheduled_scan"),
        ):
            response = test_client.post("/schedules/1/run", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Scan triggered"

    def test_run_schedule_not_found_returns_404(self, test_client, auth_headers):
        with patch("api.background.SCHEDULED_SCANS", [], create=True):
            response = test_client.post("/schedules/999/run", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
