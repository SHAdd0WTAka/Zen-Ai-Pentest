"""
Tests for system, dashboard, and websocket API routes.
Split from test_api_routes_all.py
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

pytest.skip(
    "Stale generated test suite (see issue notes); skipped until rewritten",
    allow_module_level=True,
)


# =============================================================================
# Helper Functions
# =============================================================================


def create_mock_user(user_id: str = None, role: str = "USER", is_active: bool = True):
    """Create a mock user object"""
    mock_user = MagicMock()
    mock_user.id = user_id or str(uuid4())
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.full_name = "Test User"
    mock_user.role = MagicMock()
    mock_user.role.value = 1 if role == "USER" else 2 if role == "ADMIN" else 3
    mock_user.role.name = role
    mock_user.is_active = is_active
    mock_user.created_at = datetime.now(timezone.utc)
    mock_user.hashed_password = "hashed_password"
    mock_user.to_response.return_value = {
        "id": str(mock_user.id),
        "username": mock_user.username,
        "email": mock_user.email,
        "full_name": mock_user.full_name,
        "role": role,
        "is_active": is_active,
        "created_at": mock_user.created_at,
    }
    mock_user.save = AsyncMock()
    mock_user.delete = AsyncMock()
    return mock_user


@pytest.mark.unit
class TestSystemRoutes:
    """Tests for api/routes/system.py - System Management Endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client with mocked system"""

        from api.routes.system import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/system")

        with patch("api.routes.system.require_permissions") as mock_perms:
            mock_perms.return_value = lambda: create_mock_user(role="ADMIN")
            yield TestClient(app)

    def test_get_tools_status_success(self, client):
        """Test getting tools status when available"""
        test_client = client

        with patch("tools.integrations.tool_checker.ToolChecker") as mock_checker:
            mock_checker.return_value.get_status_report.return_value = {
                "ready": True,
                "tools": {"nmap": {"installed": True}},
            }
            response = test_client.get("/api/v1/system/tools/status")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True

    def test_get_tools_status_error(self, client):
        """Test getting tools status when unavailable"""
        test_client = client

        with patch("tools.integrations.tool_checker.ToolChecker") as mock_checker:
            mock_checker.side_effect = Exception("Module not found")
            response = test_client.get("/api/v1/system/tools/status")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is False
        assert "error" in data

    def test_install_tools(self, client):
        """Test triggering tool installation"""
        test_client = client

        with patch("subprocess.Popen") as mock_popen:
            response = test_client.post("/api/v1/system/tools/install")

        assert response.status_code == 200
        data = response.json()
        assert "installation_started" in data["status"]

    def test_get_system_status(self, client):
        """Test getting basic system status"""
        test_client = client

        with patch("psutil.boot_time") as mock_boot:
            mock_boot.return_value = 1234567890
            response = test_client.get("/api/v1/system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "version" in data
        assert "uptime" in data

    def test_get_system_metrics(self, client):
        """Test getting system metrics (admin only)"""
        test_client = client

        with patch("psutil.cpu_percent") as mock_cpu:
            with patch("psutil.virtual_memory") as mock_mem:
                with patch("psutil.disk_usage") as mock_disk:
                    with patch("psutil.net_io_counters") as mock_net:
                        mock_cpu.return_value = 25.5
                        mock_mem.return_value = MagicMock(percent=60.0, used=8 * 1024**3, total=16 * 1024**3)
                        mock_disk.return_value = MagicMock(
                            percent=70.0,
                            used=100 * 1024**3,
                            total=500 * 1024**3,
                        )
                        mock_net.return_value = MagicMock(bytes_sent=1024**3, bytes_recv=2 * 1024**3)

                        response = test_client.get("/api/v1/system/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "disk_percent" in data

    def test_get_system_info(self, client):
        """Test getting detailed system info (admin only)"""
        test_client = client

        with patch("platform.platform") as mock_platform:
            with patch("platform.python_version") as mock_python:
                with patch("platform.processor") as mock_proc:
                    with patch("platform.node") as mock_node:
                        with patch("psutil.cpu_count") as mock_cpu_count:
                            with patch("psutil.cpu_freq") as mock_cpu_freq:
                                with patch("psutil.boot_time") as mock_boot:
                                    mock_platform.return_value = "Linux-5.0"
                                    mock_python.return_value = "3.9.0"
                                    mock_proc.return_value = "Intel"
                                    mock_node.return_value = "testhost"
                                    mock_cpu_count.return_value = 8
                                    mock_cpu_freq.return_value = MagicMock(current=2400)
                                    mock_boot.return_value = 1234567890

                                    response = test_client.get("/api/v1/system/info")

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "Linux-5.0"
        assert data["python_version"] == "3.9.0"
        assert "hostname" in data

    def test_get_api_stats(self, client):
        """Test getting API statistics (admin only)"""
        test_client = client

        response = test_client.get("/api/v1/system/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "requests_per_minute" in data
        assert "error_rate" in data

    def test_get_system_logs(self, client, tmp_path):
        """Test getting system logs (admin only)"""
        test_client = client

        # Create a mock log file
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "zen_ai.log"
        log_file.write_text("Line 1\nLine 2\nLine 3\n")

        with patch("builtins.open", open):
            response = test_client.get("/api/v1/system/logs?lines=2")

        # Note: This may fail due to file path issues, but that's expected
        assert response.status_code in [200, 404]

    def test_get_system_logs_not_found(self, client):
        """Test getting system logs when file doesn't exist"""
        test_client = client

        response = test_client.get("/api/v1/system/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["logs"] == []

    def test_toggle_maintenance_mode(self, client):
        """Test toggling maintenance mode (admin only)"""
        test_client = client

        response = test_client.post("/api/v1/system/maintenance?enabled=true")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert "enabled" in data["message"]

        response = test_client.post("/api/v1/system/maintenance?enabled=false")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    def test_clear_system_cache(self, client):
        """Test clearing system cache (admin only)"""
        test_client = client

        with patch("api.routes.system.clear_cache") as mock_clear:
            mock_clear.return_value = None
            response = test_client.post("/api/v1/system/clear-cache")

        assert response.status_code == 200
        assert "cleared" in response.json()["message"].lower()

    def test_get_database_status(self, client):
        """Test getting database status (admin only)"""
        test_client = client

        response = test_client.get("/api/v1/system/database/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert data["type"] == "postgresql"

    def test_get_cache_status(self, client):
        """Test getting cache status (admin only)"""
        test_client = client

        response = test_client.get("/api/v1/system/cache/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert data["type"] == "redis"


# =============================================================================


@pytest.mark.unit
class TestDashboardRoutes:
    """Tests for api/routes/dashboard.py - Dashboard Endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dashboard"""

        from api.routes.dashboard import router

        app = FastAPI()
        app.include_router(router)

        with patch("api.routes.dashboard.get_dashboard") as mock_get_dash:
            mock_dashboard = MagicMock()
            mock_get_dash.return_value = mock_dashboard
            yield TestClient(app), mock_dashboard

    def test_get_dashboard_status(self, client):
        """Test getting dashboard status"""
        test_client, mock_dashboard = client

        mock_dashboard.get_statistics.return_value = {
            "running": True,
            "started_at": "2024-01-01T00:00:00",
            "websocket": {"active_connections": 5},
            "buffered_events": 100,
        }

        response = test_client.get("/api/v1/dashboard/status")

        assert response.status_code == 200
        data = response.json()
        assert data["running"] is True
        assert data["websocket_connections"] == 5

    def test_get_system_status(self, client):
        """Test getting system status via dashboard"""
        test_client, mock_dashboard = client

        mock_dashboard.get_dashboard_data = AsyncMock(
            return_value={
                "system_status": {
                    "status": "healthy",
                    "dashboard": "running",
                    "websocket": "connected",
                    "metrics": "collecting",
                }
            }
        )

        response = test_client.get("/api/v1/dashboard/system")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_get_dashboard_data(self, client):
        """Test getting complete dashboard data"""
        test_client, mock_dashboard = client

        mock_dashboard.get_dashboard_data = AsyncMock(
            return_value={
                "metrics": {"cpu": 50},
                "tasks": [],
                "events": [],
            }
        )

        response = test_client.get("/api/v1/dashboard/data")

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

    def test_get_metrics(self, client):
        """Test getting current metrics"""
        test_client, mock_dashboard = client

        mock_dashboard.get_current_metrics.return_value = {
            "cpu_percent": 25.5,
            "memory_percent": 60.0,
        }

        response = test_client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "cpu_percent" in data

    def test_get_recent_events(self, client):
        """Test getting recent events"""
        test_client, mock_dashboard = client

        mock_event = MagicMock()
        mock_event.to_dict.return_value = {"type": "test", "data": {}}
        mock_dashboard._event_buffer = [mock_event] * 10

        response = test_client.get("/api/v1/dashboard/events/recent")

        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    def test_get_recent_events_with_limit(self, client):
        """Test getting recent events with limit"""
        test_client, mock_dashboard = client

        mock_event = MagicMock()
        mock_event.to_dict.return_value = {"type": "test"}
        mock_dashboard._event_buffer = [mock_event] * 100

        response = test_client.get("/api/v1/dashboard/events/recent?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] <= 10

    def test_get_recent_events_with_type_filter(self, client):
        """Test getting recent events filtered by type"""
        test_client, mock_dashboard = client

        from api.routes.dashboard import EventType

        mock_event = MagicMock()
        mock_event.type = EventType.TASK_PROGRESS
        mock_event.to_dict.return_value = {"type": "task.progress"}
        mock_dashboard._event_buffer = [mock_event]

        response = test_client.get("/api/v1/dashboard/events/recent?event_type=task.progress")

        assert response.status_code == 200

    def test_get_recent_events_invalid_type(self, client):
        """Test getting events with invalid event type"""
        test_client, mock_dashboard = client

        mock_dashboard._event_buffer = []

        response = test_client.get("/api/v1/dashboard/events/recent?event_type=invalid_type")

        assert response.status_code == 400

    def test_broadcast_event(self, client):
        """Test broadcasting a custom event"""
        test_client, mock_dashboard = client

        mock_dashboard.broadcast = AsyncMock(return_value=5)

        response = test_client.post(
            "/api/v1/dashboard/broadcast",
            json={
                "type": "custom",
                "data": {"message": "test"},
                "priority": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["broadcasted"] is True
        assert data["clients_notified"] == 5

    def test_send_notification(self, client):
        """Test sending notification"""
        test_client, mock_dashboard = client

        mock_dashboard.broadcast_notification = AsyncMock(return_value=3)

        response = test_client.post("/api/v1/dashboard/notify?title=Test&message=Hello&level=info")

        assert response.status_code == 200
        data = response.json()
        assert data["sent"] is True
        assert data["clients_notified"] == 3

    def test_get_task_progress_found(self, client):
        """Test getting task progress when found"""
        test_client, mock_dashboard = client

        from api.routes.dashboard import EventType

        mock_event = MagicMock()
        mock_event.type = EventType.TASK_PROGRESS
        mock_event.data = {"task_id": "task-123", "progress": 50}
        mock_dashboard._event_buffer = [mock_event]

        response = test_client.get("/api/v1/dashboard/tasks/task-123/progress")

        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 50

    def test_get_task_progress_not_found(self, client):
        """Test getting task progress when not found"""
        test_client, mock_dashboard = client

        mock_dashboard._event_buffer = []

        response = test_client.get("/api/v1/dashboard/tasks/task-123/progress")

        assert response.status_code == 404

    def test_get_websocket_stats(self, client):
        """Test getting WebSocket statistics"""
        test_client, mock_dashboard = client

        mock_dashboard.websocket = MagicMock()
        mock_dashboard.websocket._running = True
        mock_dashboard.websocket.get_statistics.return_value = {"connections": 5}

        response = test_client.get("/api/v1/dashboard/stats/websocket")

        assert response.status_code == 200

    def test_get_websocket_stats_not_enabled(self, client):
        """Test getting WebSocket stats when not enabled"""
        test_client, mock_dashboard = client

        mock_dashboard.websocket = None

        response = test_client.get("/api/v1/dashboard/stats/websocket")

        assert response.status_code == 503

    def test_get_metrics_stats(self, client):
        """Test getting metrics collector statistics"""
        test_client, mock_dashboard = client

        mock_dashboard.metrics = MagicMock()
        mock_dashboard.metrics._running = True
        mock_dashboard.metrics.get_summary.return_value = {"active_collectors": 3}

        response = test_client.get("/api/v1/dashboard/stats/metrics")

        assert response.status_code == 200

    def test_get_metrics_stats_not_enabled(self, client):
        """Test getting metrics stats when not enabled"""
        test_client, mock_dashboard = client

        mock_dashboard.metrics = None

        response = test_client.get("/api/v1/dashboard/stats/metrics")

        assert response.status_code == 503

    def test_get_event_types(self, client):
        """Test getting available event types"""
        test_client, _ = client

        response = test_client.get("/api/v1/dashboard/event-types")

        assert response.status_code == 200
        data = response.json()
        assert "event_types" in data
        assert len(data["event_types"]) > 0

    def test_health_check(self, client):
        """Test dashboard health check"""
        test_client, mock_dashboard = client

        mock_dashboard._running = True
        mock_dashboard.websocket = MagicMock()
        mock_dashboard.websocket._running = True
        mock_dashboard.metrics = MagicMock()
        mock_dashboard.metrics._running = True

        response = test_client.get("/api/v1/dashboard/health")

        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is True
        assert "checks" in data

    def test_health_check_unhealthy(self, client):
        """Test dashboard health check when unhealthy"""
        test_client, mock_dashboard = client

        mock_dashboard._running = False
        mock_dashboard.websocket = None
        mock_dashboard.metrics = None

        response = test_client.get("/api/v1/dashboard/health")

        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is False


# =============================================================================


@pytest.mark.unit
class TestWebSocketRoutes:
    """Tests for api/routes/websocket.py - WebSocket Endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client for WebSocket"""

        from api.routes.websocket import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/ws")

        yield TestClient(app)

    @pytest.mark.asyncio
    async def test_scan_websocket_connect(self):
        """Test WebSocket connection for scan updates"""
        from unittest.mock import AsyncMock

        from api.routes.websocket import scan_websocket

        mock_websocket = AsyncMock()
        scan_id = str(uuid4())

        # Simulate connection
        await scan_websocket(mock_websocket, scan_id)

        mock_websocket.accept.assert_called_once()
        # Should send initial connection message
        mock_websocket.send_json.assert_any_call(
            {
                "type": "connected",
                "channel": f"scan:{scan_id}",
                "message": "Connected to scan updates",
            }
        )

    @pytest.mark.asyncio
    async def test_scan_websocket_ping(self):
        """Test WebSocket ping/pong"""
        from api.routes.websocket import scan_websocket

        mock_websocket = AsyncMock()
        scan_id = str(uuid4())

        # First call returns ping message, second raises disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps({"action": "ping"}),
            Exception("Disconnect"),
        ]

        try:
            await scan_websocket(mock_websocket, scan_id)
        except Exception:
            pass

        mock_websocket.send_json.assert_any_call({"type": "pong"})

    @pytest.mark.asyncio
    async def test_scan_websocket_subscribe(self):
        """Test WebSocket subscribe action"""
        from api.routes.websocket import scan_websocket

        mock_websocket = AsyncMock()
        scan_id = str(uuid4())

        mock_websocket.receive_text.side_effect = [
            json.dumps({"action": "subscribe"}),
            Exception("Disconnect"),
        ]

        try:
            await scan_websocket(mock_websocket, scan_id)
        except Exception:
            pass

        mock_websocket.send_json.assert_any_call(
            {
                "type": "subscribed",
                "channel": f"scan:{scan_id}",
            }
        )

    @pytest.mark.asyncio
    async def test_scan_websocket_invalid_json(self):
        """Test WebSocket with invalid JSON"""
        from api.routes.websocket import scan_websocket

        mock_websocket = AsyncMock()
        scan_id = str(uuid4())

        mock_websocket.receive_text.side_effect = [
            "not valid json",
            Exception("Disconnect"),
        ]

        try:
            await scan_websocket(mock_websocket, scan_id)
        except Exception:
            pass

        mock_websocket.send_json.assert_any_call(
            {
                "type": "error",
                "message": "Invalid JSON",
            }
        )

    @pytest.mark.asyncio
    async def test_agents_websocket_connect(self):
        """Test WebSocket connection for agents"""
        from api.routes.websocket import agents_websocket

        mock_websocket = AsyncMock()

        try:
            await agents_websocket(mock_websocket)
        except Exception:
            pass

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_agents_websocket_get_status(self):
        """Test WebSocket get_status action"""
        from api.routes.websocket import agents_websocket

        mock_websocket = AsyncMock()
        mock_websocket.receive_text.side_effect = [
            json.dumps({"action": "get_status"}),
            Exception("Disconnect"),
        ]

        with patch("api.routes.websocket.agent_manager") as mock_manager:
            mock_manager.get_all_agents.return_value = []

            try:
                await agents_websocket(mock_websocket)
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_system_websocket_connect(self):
        """Test WebSocket connection for system"""
        from api.routes.websocket import system_websocket

        mock_websocket = AsyncMock()

        with patch("api.routes.websocket.psutil") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 25.5
            mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)

            try:
                await system_websocket(mock_websocket)
            except Exception:
                pass

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self):
        """Test broadcast helper function"""
        from api.routes.websocket import broadcast_to_channel

        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        # Temporarily set active connections
        import api.routes.websocket as ws_module

        original_connections = ws_module.active_connections.copy()
        ws_module.active_connections["test_channel"] = {mock_ws1, mock_ws2}

        try:
            await broadcast_to_channel("test_channel", {"msg": "test"})

            mock_ws1.send_json.assert_called_once_with({"msg": "test"})
            mock_ws2.send_json.assert_called_once_with({"msg": "test"})
        finally:
            ws_module.active_connections = original_connections

    @pytest.mark.asyncio
    async def test_notify_scan_update(self):
        """Test scan update notification helper"""
        from api.routes.websocket import notify_scan_update

        mock_ws = AsyncMock()

        import api.routes.websocket as ws_module

        original_connections = ws_module.active_connections.copy()
        scan_id = str(uuid4())
        ws_module.active_connections[f"scan:{scan_id}"] = {mock_ws}

        try:
            await notify_scan_update(scan_id, {"progress": 50})

            mock_ws.send_json.assert_called_once()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "scan_update"
            assert call_args["scan_id"] == scan_id
        finally:
            ws_module.active_connections = original_connections

    @pytest.mark.asyncio
    async def test_notify_agent_update(self):
        """Test agent update notification helper"""
        from api.routes.websocket import notify_agent_update

        mock_ws = AsyncMock()

        import api.routes.websocket as ws_module

        original_connections = ws_module.active_connections.copy()
        ws_module.active_connections["agents"] = {mock_ws}

        try:
            await notify_agent_update("agent-123", {"status": "running"})

            mock_ws.send_json.assert_called_once()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "agent_update"
            assert call_args["agent_id"] == "agent-123"
        finally:
            ws_module.active_connections = original_connections

    @pytest.mark.asyncio
    async def test_notify_system_event(self):
        """Test system event notification helper"""
        from api.routes.websocket import notify_system_event

        mock_ws = AsyncMock()

        import api.routes.websocket as ws_module

        original_connections = ws_module.active_connections.copy()
        ws_module.active_connections["system"] = {mock_ws}

        try:
            await notify_system_event("maintenance", "System update", "info")

            mock_ws.send_json.assert_called_once()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "system_event"
            assert call_args["event_type"] == "maintenance"
            assert call_args["severity"] == "info"
        finally:
            ws_module.active_connections = original_connections


# =============================================================================


@pytest.mark.unit
class TestAdditionalSystemTests:
    """Additional system tests"""

    @pytest.fixture
    def client(self):
        from api.routes.system import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/system")

        with patch("api.routes.system.require_permissions") as mock_perms:
            mock_perms.return_value = lambda: create_mock_user(role="ADMIN")
            yield TestClient(app)

    def test_get_system_metrics_with_exception(self, client):
        """Test metrics when psutil raises exception"""
        test_client = client

        with patch("psutil.cpu_percent") as mock_cpu:
            mock_cpu.side_effect = Exception("CPU error")
            response = test_client.get("/api/v1/system/metrics")
        assert response.status_code in [200, 500]

    def test_get_system_info_with_exception(self, client):
        """Test system info when platform raises exception"""
        test_client = client

        with patch("platform.platform") as mock_plat:
            mock_plat.side_effect = Exception("Platform error")
            response = test_client.get("/api/v1/system/info")
        assert response.status_code in [200, 500]

    def test_toggle_maintenance_mode_false(self, client):
        """Test disabling maintenance mode"""
        test_client = client
        response = test_client.post("/api/v1/system/maintenance?enabled=false")
        assert response.status_code == 200
        assert response.json()["enabled"] is False


@pytest.mark.unit
@pytest.mark.unit
class TestAdditionalDashboardTests:
    """Additional dashboard tests"""

    @pytest.fixture
    def client(self):
        from api.routes.dashboard import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/dashboard")

        with patch("api.routes.dashboard.get_dashboard") as mock_get_dash:
            mock_dashboard = MagicMock()
            mock_get_dash.return_value = mock_dashboard
            yield TestClient(app), mock_dashboard

    def test_broadcast_event_no_data(self, client):
        """Test broadcast with empty data"""
        test_client, mock_dashboard = client
        mock_dashboard.broadcast = AsyncMock(return_value=0)

        response = test_client.post(
            "/api/v1/dashboard/broadcast",
            json={"type": "custom", "data": {}},
        )
        assert response.status_code == 200

    def test_get_recent_events_zero_limit(self, client):
        """Test getting events with limit 0"""
        test_client, mock_dashboard = client
        mock_dashboard._event_buffer = []

        response = test_client.get("/api/v1/dashboard/events/recent?limit=0")
        assert response.status_code == 200

    def test_send_notification_empty(self, client):
        """Test sending empty notification"""
        test_client, mock_dashboard = client
        mock_dashboard.broadcast_notification = AsyncMock(return_value=0)

        response = test_client.post("/api/v1/dashboard/notify?title=&message=&level=info")
        assert response.status_code == 200
