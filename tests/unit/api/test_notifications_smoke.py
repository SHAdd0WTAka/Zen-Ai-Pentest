"""Smoke tests for api/routes/notifications.py"""

import pytest

from api.routes.notifications import (
    NotificationSettingsCreate,
    NotificationSettingsResponse,
    NotificationTestRequest,
    NotificationTestResponse,
    router,
)


class TestRouter:
    def test_prefix(self):
        assert router.prefix == "/notifications"

    def test_routes_exist(self):
        routes = [r.path for r in router.routes]
        assert "/notifications/settings" in routes
        assert "/notifications/test" in routes
        assert "/notifications/history" in routes
        assert "/notifications/stats" in routes


class TestNotificationSettingsCreate:
    def test_defaults(self):
        s = NotificationSettingsCreate()
        assert s.slack_enabled is False
        assert s.discord_enabled is False
        assert s.email_enabled is False
        assert s.notify_on_critical is True
        assert s.rate_limit_per_minute == 10


class TestNotificationSettingsResponse:
    def test_fields(self):
        resp = NotificationSettingsResponse(
            id=1,
            user_id=42,
            slack={"enabled": True, "channel": "#alerts", "configured": True},
            discord={"enabled": False, "configured": False},
            email={"enabled": True, "address": "a@b.com", "configured": True},
            telegram={"enabled": False, "configured": False},
            webhook={"enabled": False, "url": None, "configured": False},
            subscriptions={"scan_complete": True},
            rate_limit=10,
        )
        assert resp.user_id == 42
        assert resp.slack["enabled"] is True


class TestNotificationTestRequest:
    def test_valid(self):
        req = NotificationTestRequest(channel="slack")
        assert req.channel == "slack"

    def test_invalid_channel_raises(self):
        with pytest.raises(Exception):
            NotificationTestRequest(channel="invalid")


class TestNotificationTestResponse:
    def test_creation(self):
        resp = NotificationTestResponse(success=True, channel="email", message="ok")
        assert resp.success is True
        assert resp.channel == "email"
