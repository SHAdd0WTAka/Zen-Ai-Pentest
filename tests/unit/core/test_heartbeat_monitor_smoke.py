"""Smoke tests for core/heartbeat_monitor.py"""

import pytest

from core.heartbeat_monitor import DeviceSession, HeartbeatMonitor, MobileHeartbeatClient, create_heartbeat_monitor


class TestDeviceSession:
    def test_creation(self):
        from datetime import datetime, timezone

        session = DeviceSession(
            device_id="test-device",
            session_id="test-session",
            connected_at=datetime.now(timezone.utc),
            last_heartbeat=datetime.now(timezone.utc),
        )
        assert session.device_id == "test-device"
        assert session.session_id == "test-session"
        assert session.is_active is True


class TestHeartbeatMonitor:
    def test_init(self):
        monitor = HeartbeatMonitor()
        assert monitor._sessions == {}

    def test_get_app(self):
        monitor = HeartbeatMonitor()
        app = monitor.get_app()
        assert app.title == "Dead Man's Switch Heartbeat Monitor"

    def test_generate_challenge(self):
        monitor = HeartbeatMonitor()
        challenge = monitor._generate_challenge()
        assert isinstance(challenge, str)
        assert len(challenge) > 0


class TestMobileHeartbeatClient:
    def test_init(self):
        client = MobileHeartbeatClient(
            server_url="http://localhost:9999",
            device_id="phone-1",
            session_id="session-1",
        )
        assert client.server_url == "http://localhost:9999"
        assert client.device_id == "phone-1"
        assert client._running is False

    def test_stop(self):
        client = MobileHeartbeatClient(
            server_url="http://localhost:9999",
            device_id="phone-1",
            session_id="session-1",
        )
        client._running = True
        client.stop()
        assert client._running is False


class TestCreateHeartbeatMonitor:
    def test_returns_monitor(self):
        monitor = create_heartbeat_monitor()
        assert isinstance(monitor, HeartbeatMonitor)
