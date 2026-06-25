"""Tests for WebSocket"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.websocket import broadcast_event, manager

client = TestClient(app)


def test_websocket_connection():
    """Test basic WebSocket connection"""
    with client.websocket_connect("/api/v1/ws/") as websocket:
        websocket.send_json({"action": "subscribe", "channel": "all"})
        data = websocket.receive_json()
        assert data["type"] == "subscribed"
        assert data["channel"] == "all"


def test_websocket_echo():
    """Test WebSocket echo for unknown actions"""
    with client.websocket_connect("/api/v1/ws/") as websocket:
        websocket.send_json({"action": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "ack"
        assert data["received"]["action"] == "ping"


@pytest.mark.asyncio
async def test_broadcast_event():
    """Test broadcast sends to all connections"""
    mock_ws = AsyncMock()
    manager.active_connections = {mock_ws}
    await broadcast_event("test_event", {"foo": "bar"})
    mock_ws.send_json.assert_awaited_once_with({"type": "test_event", "payload": {"foo": "bar"}})


@pytest.mark.asyncio
async def test_broadcast_event_removes_dead():
    """Test broadcast removes dead connections"""
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock(side_effect=Exception("Connection closed"))
    manager.active_connections = {mock_ws}
    await broadcast_event("test_event", {"foo": "bar"})
    assert mock_ws not in manager.active_connections
