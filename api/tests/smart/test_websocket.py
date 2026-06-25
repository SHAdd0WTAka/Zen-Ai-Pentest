"""
Smart tests for api/websocket.py module.

Tests cover:
1. Module importability
2. ConnectionManager initialization
3. Connection handling
4. Broadcasting messages
5. Statistics
6. Error handling
"""

from unittest.mock import AsyncMock

import pytest


class TestWebsocketImportable:
    """Test that websocket module can be imported."""

    def test_module_importable(self):
        """Test that websocket module can be imported."""
        import api.websocket as websocket

        assert websocket is not None

    def test_connection_manager_available(self):
        """Test that ConnectionManager is available."""
        from api.websocket import ConnectionManager

        assert ConnectionManager is not None


class TestConnectionManagerInit:
    """Test ConnectionManager initialization."""

    def test_connection_manager_init(self):
        """Test ConnectionManager initialization."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        assert manager is not None
        assert manager.scan_connections == {}
        assert manager.global_connections == set()

    def test_connection_manager_empty_stats(self):
        """Test ConnectionManager empty stats."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        stats = manager.get_stats()
        assert stats["global_connections"] == 0
        assert stats["active_scans"] == 0
        assert stats["total_scan_connections"] == 0


class TestConnectionHandling:
    """Test connection handling."""

    @pytest.mark.asyncio
    async def test_connect_scan(self):
        """Test connecting to a scan."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        await manager.connect(websocket, scan_id=1)
        assert 1 in manager.scan_connections
        assert websocket in manager.scan_connections[1]

    @pytest.mark.asyncio
    async def test_connect_global(self):
        """Test connecting globally."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        await manager.connect(websocket, scan_id=None)
        assert websocket in manager.global_connections

    @pytest.mark.asyncio
    async def test_disconnect_scan(self):
        """Test disconnecting from a scan."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        await manager.connect(websocket, scan_id=1)
        manager.disconnect(websocket, scan_id=1)
        assert websocket not in manager.scan_connections.get(1, set())

    @pytest.mark.asyncio
    async def test_disconnect_global(self):
        """Test disconnecting globally."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        await manager.connect(websocket, scan_id=None)
        manager.disconnect(websocket, scan_id=None)
        assert websocket not in manager.global_connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_scan(self):
        """Test disconnecting from non-existent scan."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        # Should not raise error
        manager.disconnect(websocket, scan_id=999)

    @pytest.mark.asyncio
    async def test_multiple_connections_same_scan(self):
        """Test multiple connections to same scan."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, scan_id=1)
        await manager.connect(ws2, scan_id=1)
        assert len(manager.scan_connections[1]) == 2

    @pytest.mark.asyncio
    async def test_multiple_scans(self):
        """Test connections to multiple scans."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, scan_id=1)
        await manager.connect(ws2, scan_id=2)
        assert len(manager.scan_connections) == 2


class TestBroadcasting:
    """Test message broadcasting."""

    @pytest.mark.asyncio
    async def test_broadcast_to_scan(self):
        """Test broadcasting to scan connections."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        await manager.connect(websocket, scan_id=1)
        message = {"type": "update", "data": "test"}
        await manager.broadcast_to_scan(1, message)
        websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_scan_no_connections(self):
        """Test broadcasting to scan with no connections."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        message = {"type": "update", "data": "test"}
        # Should not raise error
        await manager.broadcast_to_scan(999, message)

    @pytest.mark.asyncio
    async def test_broadcast_global(self):
        """Test broadcasting globally."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        await manager.connect(websocket, scan_id=None)
        message = {"type": "notification", "data": "test"}
        await manager.broadcast_global(message)
        websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending personal message."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        message = {"type": "personal", "data": "test"}
        await manager.send_personal_message(websocket, message)
        websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_connections(self):
        """Test broadcasting to multiple connections."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, scan_id=1)
        await manager.connect(ws2, scan_id=1)
        message = {"type": "update", "data": "test"}
        await manager.broadcast_to_scan(1, message)
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_broadcast_to_disconnected_client(self):
        """Test broadcasting to disconnected client."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        websocket.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        await manager.connect(websocket, scan_id=1)
        message = {"type": "update", "data": "test"}
        # Should handle error and remove disconnected client
        await manager.broadcast_to_scan(1, message)
        # Client should be removed after error
        assert websocket not in manager.scan_connections.get(1, set())

    @pytest.mark.asyncio
    async def test_send_personal_message_error(self):
        """Test sending personal message with error."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        websocket.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        message = {"type": "update", "data": "test"}
        # Should not raise error
        await manager.send_personal_message(websocket, message)

    @pytest.mark.asyncio
    async def test_broadcast_global_with_error(self):
        """Test global broadcast with one failing connection."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        await manager.connect(ws1, scan_id=None)
        await manager.connect(ws2, scan_id=None)
        message = {"type": "update", "data": "test"}
        await manager.broadcast_global(message)
        ws1.send_json.assert_called_once_with(message)


class TestStatistics:
    """Test statistics functions."""

    @pytest.mark.asyncio
    async def test_get_scan_connections_count(self):
        """Test getting scan connections count."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, scan_id=1)
        await manager.connect(ws2, scan_id=1)
        assert manager.get_scan_connections_count(1) == 2

    def test_get_scan_connections_count_nonexistent(self):
        """Test getting count for non-existent scan."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        assert manager.get_scan_connections_count(999) == 0

    @pytest.mark.asyncio
    async def test_get_global_connections_count(self):
        """Test getting global connections count."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, scan_id=None)
        await manager.connect(ws2, scan_id=None)
        assert manager.get_global_connections_count() == 2

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting connection statistics."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()
        await manager.connect(ws1, scan_id=1)
        await manager.connect(ws2, scan_id=1)
        await manager.connect(ws3, scan_id=2)
        stats = manager.get_stats()
        assert stats["global_connections"] == 0
        assert stats["active_scans"] == 2
        assert stats["total_scan_connections"] == 3


class TestEmptyInput:
    """Test handling of empty input."""

    @pytest.mark.asyncio
    async def test_connect_with_none_websocket(self):
        """Test connecting with None websocket."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        # Should raise AttributeError when trying to call accept()
        with pytest.raises(AttributeError):
            await manager.connect(None, scan_id=1)

    def test_disconnect_with_none_websocket(self):
        """Test disconnecting with None websocket."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        # Should not raise error
        manager.disconnect(None, scan_id=1)


class TestInvalidOutput:
    """Test handling of invalid output."""

    @pytest.mark.asyncio
    async def test_broadcast_non_json_message(self):
        """Test broadcasting non-JSON message."""
        from api.websocket import ConnectionManager

        manager = ConnectionManager()
        websocket = AsyncMock()
        websocket.send_json = AsyncMock(side_effect=TypeError("Invalid JSON"))
        await manager.connect(websocket, scan_id=1)
        # Should handle error
        await manager.broadcast_to_scan(1, {"invalid": object()})
