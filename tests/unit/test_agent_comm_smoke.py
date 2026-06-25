"""Smoke tests for api/websockets/agent_comm.py"""

import pytest

from api.websockets.agent_comm import ConnectionManager, manager, router


class TestConnectionManager:
    def test_init(self):
        cm = ConnectionManager()
        assert cm.active_connections == {}
        assert cm.agent_sessions == {}

    def test_get_session_agents_empty(self):
        cm = ConnectionManager()
        agents = cm.get_session_agents("session-1")
        assert agents == []

    def test_session_agents_after_connect_disconnect(self):
        cm = ConnectionManager()
        assert cm.get_session_agents("s1") == []


class TestGlobalManager:
    def test_manager_instance(self):
        assert isinstance(manager, ConnectionManager)
        assert manager.active_connections == {}


class TestRouter:
    def test_prefix(self):
        assert router.prefix == "/ws/agent-comm"

    def test_routes_exist(self):
        routes = [r.path for r in router.routes]
        assert "/ws/agent-comm/{session_id}" in routes
        assert "/ws/agent-comm/sessions/{session_id}/agents" in routes
