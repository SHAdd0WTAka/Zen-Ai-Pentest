"""
Comprehensive tests for api/main.py - FastAPI app initialization and core functionality
"""

import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock modules before importing main - must mock all dependencies
sys.modules["redis"] = MagicMock()
sys.modules["auth"] = MagicMock()
sys.modules["auth.jwt_handler"] = MagicMock()
sys.modules["database"] = MagicMock()
sys.modules["database.auth_models"] = MagicMock()
sys.modules["database.crud"] = MagicMock()
sys.modules["database.models"] = MagicMock()
sys.modules["agents"] = MagicMock()
sys.modules["agents.react_agent"] = MagicMock()
sys.modules["agents.workflows.orchestrator"] = MagicMock()
sys.modules["tools"] = MagicMock()
sys.modules["tools.nmap_integration"] = MagicMock()
sys.modules["reports"] = MagicMock()
sys.modules["reports.generator"] = MagicMock()
sys.modules["notifications"] = MagicMock()
sys.modules["notifications.slack"] = MagicMock()
sys.modules["integrations"] = MagicMock()
sys.modules["integrations.jira_client"] = MagicMock()

# Set environment variables before import
os.environ["ADMIN_PASSWORD"] = "test123"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["CORS_ORIGINS"] = (
    '["http://localhost:3000", "http://localhost:8000"]'  # JSON format
)

# Now import the app
from api.main import (
    ALLOWED_ORIGINS,
    SimpleAgentConnection,
    agent_connection_manager,
    calculate_next_run,
    get_tool_category,
    lifespan,
    verify_admin_credentials,
    ws_manager,
)


class TestAppInitialization:
    """Test FastAPI app initialization"""

    def test_cors_origins_loaded(self):
        """Test CORS origins are loaded from environment"""
        assert isinstance(ALLOWED_ORIGINS, list)
        assert len(ALLOWED_ORIGINS) > 0
        # The origins might be parsed as JSON or comma-separated depending on env
        origins_str = str(ALLOWED_ORIGINS)
        assert "localhost" in origins_str


class TestLifespan:
    """Test startup/shutdown events"""

    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """Test lifespan startup initializes database"""
        from fastapi import FastAPI

        test_app = FastAPI()

        with patch("api.main.init_db") as mock_init_db:
            async with lifespan(test_app):
                pass
            mock_init_db.assert_called_once()


class TestWebSocket:
    """Test WebSocket functionality"""

    def test_websocket_manager_initialization(self):
        """Test WebSocket manager is initialized"""
        assert ws_manager is not None
        assert hasattr(ws_manager, "scan_connections")
        assert hasattr(ws_manager, "global_connections")

    def test_agent_connection_manager(self):
        """Test agent connection manager"""
        assert agent_connection_manager is not None
        assert isinstance(agent_connection_manager, SimpleAgentConnection)

    def test_simple_agent_connection_connect(self):
        """Test SimpleAgentConnection connect method"""
        import asyncio

        async def test_connect():
            manager = SimpleAgentConnection()
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()

            await manager.connect(mock_ws, "agent_1", "zen_test_key")
            assert "agent_1" in manager.active_connections
            assert manager.agent_info["agent_1"]["api_key"] == "zen_test_key"

        asyncio.run(test_connect())

    def test_simple_agent_connection_disconnect(self):
        """Test SimpleAgentConnection disconnect method"""
        import asyncio

        async def test_disconnect():
            manager = SimpleAgentConnection()
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()

            await manager.connect(mock_ws, "agent_1", "zen_key")
            manager.disconnect("agent_1")
            assert "agent_1" not in manager.active_connections

        asyncio.run(test_disconnect())

    def test_simple_agent_connection_send_to_agent(self):
        """Test SimpleAgentConnection send_to_agent method"""
        import asyncio

        async def test_send():
            manager = SimpleAgentConnection()
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_json = AsyncMock()

            await manager.connect(mock_ws, "agent_1", "zen_key")
            result = await manager.send_to_agent("agent_1", {"type": "test"})
            assert result is True
            mock_ws.send_json.assert_called_once()

        asyncio.run(test_send())

    def test_simple_agent_connection_broadcast(self):
        """Test SimpleAgentConnection broadcast method"""
        import asyncio

        async def test_broadcast():
            manager = SimpleAgentConnection()
            mock_ws1 = MagicMock()
            mock_ws1.accept = AsyncMock()
            mock_ws1.send_json = AsyncMock()
            mock_ws2 = MagicMock()
            mock_ws2.accept = AsyncMock()
            mock_ws2.send_json = AsyncMock()

            await manager.connect(mock_ws1, "agent_1", "zen_key1")
            await manager.connect(mock_ws2, "agent_2", "zen_key2")

            await manager.broadcast({"type": "announcement"})
            mock_ws1.send_json.assert_called_once()
            mock_ws2.send_json.assert_called_once()

        asyncio.run(test_broadcast())

    def test_simple_agent_connection_get_connected_agents(self):
        """Test SimpleAgentConnection get_connected_agents method"""
        import asyncio

        async def test_get_agents():
            manager = SimpleAgentConnection()
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()

            await manager.connect(mock_ws, "agent_1", "zen_key")
            agents = manager.get_connected_agents()
            assert "agent_1" in agents

        asyncio.run(test_get_agents())

    def test_simple_agent_connection_is_agent_connected(self):
        """Test SimpleAgentConnection is_agent_connected method"""
        import asyncio

        async def test_is_connected():
            manager = SimpleAgentConnection()
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()

            await manager.connect(mock_ws, "agent_1", "zen_key")
            assert manager.is_agent_connected("agent_1") is True
            assert manager.is_agent_connected("agent_2") is False

        asyncio.run(test_is_connected())


class TestHelperFunctions:
    """Test helper functions"""

    def test_get_tool_category(self):
        """Test tool category classification"""
        assert get_tool_category("nmap_scan") == "network"
        assert get_tool_category("masscan_ports") == "network"
        assert get_tool_category("scapy_packet") == "network"
        assert get_tool_category("tshark_capture") == "network"
        assert get_tool_category("sqlmap_test") == "web"
        assert get_tool_category("burp_scan") == "web"
        assert get_tool_category("gobuster_dir") == "web"
        assert get_tool_category("metasploit_exploit") == "exploitation"
        assert get_tool_category("hydra_brute") == "brute_force"
        assert get_tool_category("amass_enum") == "recon"
        assert get_tool_category("bloodhound_data") == "ad"
        assert get_tool_category("cme_scan") == "ad"
        assert get_tool_category("responder_poison") == "ad"
        assert get_tool_category("aircrack_ng") == "wireless"
        assert get_tool_category("unknown_tool") == "other"

    def test_verify_admin_credentials(self):
        """Test admin credential verification"""
        # Note: ADMIN_USERNAME and ADMIN_PASSWORD are set at module import time
        # so we can only test with the values that were set at import
        admin_pass = os.environ.get("ADMIN_PASSWORD", "test123")
        admin_user = os.environ.get("ADMIN_USERNAME", "admin")

        assert verify_admin_credentials(admin_user, admin_pass) is True
        assert verify_admin_credentials(admin_user, "wrong") is False
        assert verify_admin_credentials("wrong", admin_pass) is False


class TestCalculateNextRun:
    """Test schedule calculation"""

    def test_calculate_next_run_daily(self):
        """Test daily schedule calculation"""
        now = datetime.utcnow()
        result = calculate_next_run(
            "daily", f"{now.hour:02d}:{now.minute:02d}"
        )
        assert isinstance(result, datetime)
        assert result > now or result.day != now.day

    def test_calculate_next_run_weekly(self):
        """Test weekly schedule calculation"""
        now = datetime.utcnow()
        result = calculate_next_run(
            "weekly", f"{now.hour:02d}:{now.minute:02d}", day=0
        )
        assert isinstance(result, datetime)

    def test_calculate_next_run_weekly_same_day(self):
        """Test weekly schedule calculation for same day"""
        now = datetime.utcnow()
        result = calculate_next_run(
            "weekly", f"{now.hour:02d}:{now.minute:02d}", day=now.weekday()
        )
        assert isinstance(result, datetime)

    def test_calculate_next_run_once(self):
        """Test one-time schedule calculation"""
        now = datetime.utcnow()
        # Set time in the past
        past_hour = (now.hour - 1) % 24
        result = calculate_next_run("once", f"{past_hour:02d}:00")
        assert isinstance(result, datetime)
        # Should be tomorrow
        assert result.day != now.day or result.month != now.month

    def test_calculate_next_run_once_future(self):
        """Test one-time schedule calculation for future time"""
        now = datetime.utcnow()
        future_hour = (now.hour + 1) % 24
        result = calculate_next_run("once", f"{future_hour:02d}:00")
        assert isinstance(result, datetime)

    def test_calculate_next_run_monthly(self):
        """Test monthly schedule calculation"""
        now = datetime.utcnow()
        result = calculate_next_run(
            "monthly", f"{now.hour:02d}:{now.minute:02d}"
        )
        assert isinstance(result, datetime)

    def test_calculate_next_run_invalid_frequency(self):
        """Test schedule calculation with invalid frequency"""
        now = datetime.utcnow()
        result = calculate_next_run(
            "invalid", f"{now.hour:02d}:{now.minute:02d}"
        )
        assert isinstance(result, datetime)


class TestEnumImports:
    """Test that all required enums are available"""

    def test_imports_from_main(self):
        """Test main module imports work"""
        # These should be available from the module
        assert ALLOWED_ORIGINS is not None
        assert SimpleAgentConnection is not None
        assert agent_connection_manager is not None
        assert ws_manager is not None
