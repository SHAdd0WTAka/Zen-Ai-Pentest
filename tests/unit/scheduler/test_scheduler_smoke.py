"""Smoke tests for api/routes/scheduler.py"""

from datetime import datetime

import pytest

from api.routes.scheduler import (
    CreateScheduledScanRequest,
    CronPresetsResponse,
    ExecutionHistoryResponse,
    NotificationConfig,
    ScanConfig,
    ScheduleConfig,
    ScheduledScanResponse,
    SchedulerStatisticsResponse,
    UpdateScheduledScanRequest,
    execution_to_dict,
    schedule_to_dict,
)


class TestScheduleConfig:
    def test_once_schedule(self):
        sc = ScheduleConfig(type="once", run_at=datetime(2026, 6, 25, 12, 0))
        assert sc.type == "once"

    def test_recurring_cron(self):
        sc = ScheduleConfig(type="recurring", cron="0 2 * * *")
        assert sc.cron == "0 2 * * *"

    def test_interval(self):
        sc = ScheduleConfig(type="interval", interval_minutes=30)
        assert sc.interval_minutes == 30

    def test_default_timezone(self):
        sc = ScheduleConfig(type="once")
        assert sc.timezone == "UTC"


class TestNotificationConfig:
    def test_defaults(self):
        nc = NotificationConfig()
        assert nc.on_completion is True
        assert nc.on_success is False

    def test_custom(self):
        nc = NotificationConfig(email="test@example.com", slack_webhook="https://hooks.slack.com/xxx")
        assert nc.email == "test@example.com"


class TestScanConfig:
    def test_defaults(self):
        sc = ScanConfig()
        assert sc.depth == "normal"
        assert sc.timeout == 3600

    def test_custom(self):
        sc = ScanConfig(tools=["nmap", "gobuster"], ports="80,443", depth="deep")
        assert sc.tools == ["nmap", "gobuster"]


class TestCreateScheduledScanRequest:
    def test_minimal(self):
        req = CreateScheduledScanRequest(
            name="test-scan",
            target="example.com",
            scan_type="vulnerability",
            schedule=ScheduleConfig(type="once", run_at=datetime(2026, 6, 25, 12, 0)),
        )
        assert req.name == "test-scan"
        assert req.priority == 5


class TestResponseModels:
    def test_scheduled_scan_response_fields(self):
        fields = list(ScheduledScanResponse.model_fields.keys())
        assert "id" in fields
        assert "name" in fields
        assert "status" in fields

    def test_execution_history_response_fields(self):
        fields = list(ExecutionHistoryResponse.model_fields.keys())
        assert "scheduled_scan_id" in fields
        assert "celery_task_id" in fields

    def test_scheduler_statistics_response_fields(self):
        fields = list(SchedulerStatisticsResponse.model_fields.keys())
        assert "total_scheduled" in fields
        assert "success_rate" in fields

    def test_cron_presets_response(self):
        resp = CronPresetsResponse(presets={"daily": "0 0 * * *"}, descriptions={"daily": "Daily"})
        assert resp.presets["daily"] == "0 0 * * *"


class TestHelperFunctions:
    def test_schedule_to_dict(self):
        class MockScan:
            id = 1
            name = "test"
            description = ""
            target = "example.com"
            scan_type = "vulnerability"
            schedule_type = "once"
            cron_expression = None
            interval_minutes = None
            next_run = None
            last_run = None
            timezone = "UTC"
            priority = 5
            status = "active"
            is_active = True
            max_retries = 3
            retry_count = 0
            notifications = {}
            created_by = None
            created_at = datetime(2026, 1, 1)
            updated_at = datetime(2026, 1, 1)

        d = schedule_to_dict(MockScan())
        assert d["name"] == "test"
        assert d["status"] == "active"

    def test_execution_to_dict(self):
        class MockExec:
            id = 1
            scheduled_scan_id = 1
            scan_id = None
            started_at = datetime(2026, 1, 1)
            completed_at = None
            status = "running"
            result_summary = None
            error_message = None
            findings_count = 0
            critical_count = 0
            high_count = 0
            medium_count = 0
            low_count = 0
            celery_task_id = None

        d = execution_to_dict(MockExec())
        assert d["status"] == "running"
        assert d["findings_count"] == 0
