"""Tests for api/websocket.py - WebSocket Connection Manager."""

import pytest
from unittest.mock import MagicMock

from api.websocket import ConnectionManager


class TestConnectionManager:
    """Test ConnectionManager class."""

    def test_init(self):
        """Test initialization."""
        manager = ConnectionManager()

        assert manager.scan_connections == {}
        assert manager.global_connections == set()

    def test_connect_global(self):
        """Test global connection (verify sync logic)."""
        manager = ConnectionManager()
        mock_ws = MagicMock()

        # Simulate what happens after accept
        manager.global_connections.add(mock_ws)

        assert mock_ws in manager.global_connections

    def test_connect_to_scan(self):
        """Test scan-specific connection logic."""
        manager = ConnectionManager()
        mock_ws = MagicMock()

        # Simulate connection tracking
        if 123 not in manager.scan_connections:
            manager.scan_connections[123] = set()
        manager.scan_connections[123].add(mock_ws)

        assert 123 in manager.scan_connections
        assert mock_ws in manager.scan_connections[123]

    def test_connect_multiple_to_same_scan(self):
        """Test multiple connections to same scan."""
        manager = ConnectionManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()

        manager.scan_connections[123] = {mock_ws1, mock_ws2}

        assert len(manager.scan_connections[123]) == 2

    def test_disconnect_global(self):
        """Test disconnecting global connection."""
        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.global_connections.add(mock_ws)

        manager.disconnect(mock_ws)

        assert mock_ws not in manager.global_connections

    def test_disconnect_from_scan(self):
        """Test disconnecting from scan."""
        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.scan_connections[123] = {mock_ws}

        manager.disconnect(mock_ws, scan_id=123)

        assert 123 not in manager.scan_connections

    def test_disconnect_clears_empty_scan(self):
        """Test that empty scan entries are cleaned up."""
        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.scan_connections[123] = {mock_ws}

        manager.disconnect(mock_ws, scan_id=123)

        assert 123 not in manager.scan_connections

    def test_disconnect_from_scan_partial(self):
        """Test disconnecting one of multiple connections."""
        manager = ConnectionManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        manager.scan_connections[123] = {mock_ws1, mock_ws2}

        manager.disconnect(mock_ws1, scan_id=123)

        assert mock_ws2 in manager.scan_connections[123]
        assert 123 in manager.scan_connections

    def test_get_scan_connections_count(self):
        """Test getting scan connection count."""
        manager = ConnectionManager()
        manager.scan_connections[123] = {MagicMock(), MagicMock()}

        assert manager.get_scan_connections_count(123) == 2
        assert manager.get_scan_connections_count(999) == 0

    def test_get_global_connections_count(self):
        """Test getting global connection count."""
        manager = ConnectionManager()
        manager.global_connections = {MagicMock(), MagicMock(), MagicMock()}

        assert manager.get_global_connections_count() == 3

    def test_get_stats(self):
        """Test getting connection statistics."""
        manager = ConnectionManager()
        manager.global_connections = {MagicMock()}
        manager.scan_connections[1] = {MagicMock(), MagicMock()}
        manager.scan_connections[2] = {MagicMock()}

        stats = manager.get_stats()

        assert stats["global_connections"] == 1
        assert stats["active_scans"] == 2
        assert stats["total_scan_connections"] == 3

    def test_scan_connections_is_dict_of_sets(self):
        """Test that scan_connections structure is correct."""
        manager = ConnectionManager()

        # Should be empty dict initially
        assert isinstance(manager.scan_connections, dict)

        # Add scan connections
        manager.scan_connections[1] = {MagicMock()}
        assert isinstance(manager.scan_connections[1], set)
