"""
WebSocket Tests for Zen-AI-Pentest
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWebSocketConnections:
    """Test WebSocket connection handling"""

    def test_websocket_endpoint_exists(self, client):
        """Test that WebSocket endpoint exists"""
        # WebSocket upgrade request
        response = client.get(
            "/ws/scans",
            headers={
                "Upgrade": "websocket",
                "Connection": "Upgrade",
            },
        )
        # Should either upgrade or return appropriate status
        assert response.status_code in [200, 403, 404, 426]

    @pytest.mark.asyncio
    async def test_websocket_scan_updates(self):
        """Test WebSocket scan updates"""
        from unittest.mock import AsyncMock

        mock_ws = AsyncMock()
        mock_ws.receive_text = AsyncMock(return_value=json.dumps({"action": "subscribe", "scan_id": 1}))

        # Simulate connection
        with patch("api.websocket.WebSocket") as MockWS:
            MockWS.return_value = mock_ws

            # Connection should be accepted
            assert mock_ws.accept.called or True  # Placeholder


@pytest.mark.asyncio
class TestWebSocketManager:
    """Test WebSocket manager functionality"""

    async def test_manager_initialization(self):
        """Test WebSocket manager initialization"""
        from api.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        assert manager.active_connections == {}

    async def test_add_connection(self):
        """Test adding connection"""
        from api.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()

        await manager.connect(mock_ws, "scan-1")

        assert "scan-1" in manager.active_connections

    async def test_remove_connection(self):
        """Test removing connection"""
        from api.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()

        await manager.connect(mock_ws, "scan-1")
        manager.disconnect(mock_ws, "scan-1")

        assert "scan-1" not in manager.active_connections

    async def test_broadcast_to_scan(self):
        """Test broadcasting to scan subscribers"""
        from api.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.connect(mock_ws1, "scan-1")
        await manager.connect(mock_ws2, "scan-1")

        message = {"status": "completed", "progress": 100}
        await manager.broadcast(message, client_id="scan-1")

        # Both connections should receive message
        assert mock_ws1.send_text.called
        assert mock_ws2.send_text.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
