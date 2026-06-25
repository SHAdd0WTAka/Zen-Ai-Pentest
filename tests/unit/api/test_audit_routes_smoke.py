"""Smoke tests for api/routes/audit.py"""

import pytest

from api.routes.audit import (
    LogEntryResponse,
    LogQueryRequest,
    SIEMHealthResponse,
    get_audit_logger,
    get_compliance_reporter,
    router,
)


class TestRouter:
    def test_prefix(self):
        assert router.prefix == "/api/v1/audit"

    def test_routes_exist(self):
        routes = [r.path for r in router.routes]
        assert "/api/v1/audit/logs" in routes
        assert "/api/v1/audit/integrity" in routes
        assert "/api/v1/audit/siem/health" in routes
        assert "/api/v1/audit/stats" in routes


class TestModels:
    def test_log_query_request(self):
        req = LogQueryRequest()
        assert req.limit == 100
        assert req.offset == 0

    def test_log_entry_response(self):
        from datetime import datetime

        entry = LogEntryResponse(
            id="1", timestamp=datetime.now(), level="info", category="system", event_type="login", message="test", hash="abc"
        )
        assert entry.level == "info"
        assert entry.hash == "abc"

    def test_siem_health_response(self):
        resp = SIEMHealthResponse(backends={"Splunk": True}, all_healthy=True)
        assert resp.all_healthy is True


class TestDependencies:
    def test_get_audit_logger(self):
        log = get_audit_logger()
        assert log is not None

    def test_get_compliance_reporter(self):
        rep = get_compliance_reporter()
        assert rep is not None
