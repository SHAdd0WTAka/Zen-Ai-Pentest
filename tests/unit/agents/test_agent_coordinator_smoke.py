"""Smoke tests for agents/agent_coordinator_v3.py"""

import pytest

from agents.agent_coordinator_v3 import (
    Agent,
    AgentCapability,
    AgentCoordinator,
    AgentInfo,
    AgentMessage,
    AgentState,
    AgentType,
    MessageType,
    TaskAssignment,
    get_coordinator,
)


class TestAgentType:
    def test_values(self):
        assert AgentType.RECON.value == "reconnaissance"
        assert AgentType.COORDINATOR.value == "coordinator"
        assert AgentType.CUSTOM.value == "custom"


class TestAgentState:
    def test_values(self):
        assert AgentState.IDLE.name == "IDLE"
        assert AgentState.BUSY.name == "BUSY"
        assert AgentState.ERROR.name == "ERROR"


class TestMessageType:
    def test_values(self):
        assert MessageType.COMMAND.value == "command"
        assert MessageType.HEARTBEAT.value == "heartbeat"


class TestAgentCapability:
    def test_creation(self):
        cap = AgentCapability(name="port_scan", description="Scan open ports")
        assert cap.name == "port_scan"
        assert cap.description == "Scan open ports"
        assert cap.parameters == {}


class TestAgentInfo:
    def test_creation(self):
        info = AgentInfo(
            agent_id="agent-1",
            agent_type=AgentType.SCANNER,
            name="test-scanner",
        )
        assert info.agent_id == "agent-1"
        assert info.state == AgentState.INITIALIZING
        assert info.task_count == 0
        assert info.success_rate == 1.0


class TestAgentMessage:
    def test_creation(self):
        msg = AgentMessage(
            msg_type=MessageType.DIRECT,
            sender_id="src",
            recipient_id="dst",
            payload={"key": "value"},
        )
        assert msg.msg_type == MessageType.DIRECT
        assert msg.payload == {"key": "value"}
        assert msg.priority == 1


class TestTaskAssignment:
    def test_creation(self):
        assignment = TaskAssignment(
            task_id="t-1",
            agent_id="a-1",
            task_type="scan",
            parameters={"target": "example.com"},
        )
        assert assignment.task_id == "t-1"
        assert assignment.priority == 1
        assert assignment.parameters["target"] == "example.com"


class TestAgentCoordinator:
    def test_init(self):
        coord = AgentCoordinator(max_concurrent_tasks=50, heartbeat_timeout=30)
        assert coord.max_concurrent_tasks == 50
        assert coord.heartbeat_timeout == 30
        assert coord._agents == {}

    def test_init_defaults(self):
        coord = AgentCoordinator()
        assert coord.max_concurrent_tasks == 100
        assert coord.heartbeat_timeout == 60

    def test_get_stats_structure(self):
        import asyncio

        coord = AgentCoordinator()
        loop = asyncio.new_event_loop()
        try:
            stats = loop.run_until_complete(coord.get_stats())
            assert "agents_online" in stats
            assert "agents_idle" in stats
            assert "agents_busy" in stats
            assert "pending_tasks" in stats
            assert "messages_routed" in stats
            assert "tasks_assigned" in stats
        finally:
            loop.close()


class TestGetCoordinator:
    def test_returns_coordinator(self):
        c = get_coordinator()
        assert isinstance(c, AgentCoordinator)

    def test_singleton(self):
        c1 = get_coordinator()
        c2 = get_coordinator()
        assert c1 is c2
