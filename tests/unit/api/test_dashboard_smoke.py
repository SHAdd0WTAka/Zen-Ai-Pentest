"""Smoke tests for api/routes/dashboard.py"""

import pytest

from api.routes.dashboard import DashboardStatusResponse, EventBroadcastRequest, SystemStatusResponse, get_dashboard, router


class TestRouter:
    def test_prefix(self):
        assert router.prefix == "/api/v1/dashboard"

    def test_routes_exist(self):
        routes = [r.path for r in router.routes]
        assert "/api/v1/dashboard/status" in routes
        assert "/api/v1/dashboard/system" in routes
        assert "/api/v1/dashboard/data" in routes
        assert "/api/v1/dashboard/metrics" in routes
        assert "/api/v1/dashboard/health" in routes


class TestDashboardStatusResponse:
    def test_defaults(self):
        resp = DashboardStatusResponse(running=True, started_at=None, websocket_connections=0, buffered_events=0)
        assert resp.running is True
        assert resp.websocket_connections == 0


class TestSystemStatusResponse:
    def test_creation(self):
        resp = SystemStatusResponse(status="ok", dashboard="running", websocket="active", metrics="healthy")
        assert resp.status == "ok"
        assert resp.metrics == "healthy"


class TestEventBroadcastRequest:
    def test_defaults(self):
        req = EventBroadcastRequest(type="scan.update")
        assert req.type == "scan.update"
        assert req.data == {}
        assert req.priority == 3


class TestGetDashboard:
    def test_get_dashboard(self):
        dash = get_dashboard()
        assert dash is not None
