"""Real AgentLifecycle tests with verification - not just execution."""

# flake8: noqa: D403

from __future__ import annotations

import asyncio
from typing import Dict

import pytest

from agents.agent_base import AgentMessage, AgentRole, AgentState, BaseAgent


class MockOrchestrator:
    """Minimal mock only for message routing - not the agent logic."""

    def __init__(self):
        """Initialize mock orchestrator with empty message list."""
        self.messages: list[AgentMessage] = []
        self.shared_context: Dict = {}

    async def route_message(self, msg: AgentMessage):
        """Route message by appending to internal list."""
        self.messages.append(msg)

    async def update_shared_context(self, key: str, value, agent_id: str):
        """Update shared context with key-value pair."""
        self.shared_context[key] = {"value": value, "agent_id": agent_id}


class MockAgent(BaseAgent):
    """Concrete test agent that implements execute_task."""

    async def execute_task(self, task: Dict) -> Dict:
        """Execute task and return completion status."""
        return {"status": "completed", "task": task}


@pytest.fixture
def orchestrator():
    """Provide mock orchestrator for testing."""
    return MockOrchestrator()


@pytest.fixture
def agent(orchestrator):
    """Provide test agent instance with mock orchestrator."""
    return MockAgent(name="test_agent", role=AgentRole.RESEARCHER, orchestrator=orchestrator)


class TestAgentLifecycleStates:
    """Test state transitions with real assertions."""

    @pytest.mark.asyncio
    async def test_agent_initial_state(self, agent):
        """Verify fresh agent is in correct initial state."""
        status = agent.get_status()

        assert status["name"] == "test_agent"
        assert status["role"] == "researcher"
        assert status["running"] is False
        assert status["queue_size"] == 0
        assert status["inbox_count"] == 0
        assert agent.id is not None
        assert len(agent.id) == 8  # UUID short format

    @pytest.mark.asyncio
    async def test_start_transitions_to_running(self, agent):
        """start() must set running=True and create task."""
        assert agent.running is False
        assert agent.task is None

        await agent.start()
        await asyncio.sleep(0.1)  # Let task start

        assert agent.running is True
        assert agent.task is not None
        assert not agent.task.done()

        # Cleanup
        await agent.stop()

    @pytest.mark.asyncio
    async def test_stop_transitions_to_stopped(self, agent):
        """stop() must set running=False and cancel task."""
        await agent.start()
        await asyncio.sleep(0.1)  # Let task start
        assert agent.running is True

        await agent.stop()

        assert agent.running is False
        assert agent.task.cancelled() or agent.task.done()

    @pytest.mark.asyncio
    async def test_multiple_start_stop_cycles(self, agent):
        """Agent must handle multiple start/stop cycles correctly."""
        for i in range(3):
            await agent.start()
            await asyncio.sleep(0.1)  # Let task start
            assert agent.running is True, f"Cycle {i}: Agent not running after start"

            await agent.stop()
            assert agent.running is False, f"Cycle {i}: Agent still running after stop"

    @pytest.mark.asyncio
    async def test_get_status_reflects_state_changes(self, agent):
        """get_status() must reflect actual internal state."""
        # Initial state
        status = agent.get_status()
        assert status["running"] is False
        assert status["memory_entries"] == 0

        # After start
        await agent.start()
        await asyncio.sleep(0.1)  # Let task start
        status = agent.get_status()
        assert status["running"] is True

        # After message received
        msg = AgentMessage(sender="test", content="hello")
        await agent.receive_message(msg)
        status = agent.get_status()
        assert status["inbox_count"] == 1
        assert status["memory_entries"] == 1

        await agent.stop()


class TestAgentMessaging:
    """Test message passing with real queue operations."""

    @pytest.mark.asyncio
    async def test_receive_message_adds_to_inbox(self, agent):
        """receive_message() must add to inbox and memory."""
        msg = AgentMessage(sender="sender_001", content="test content", msg_type="chat")

        await agent.receive_message(msg)

        assert len(agent.inbox) == 1
        assert agent.inbox[0].content == "test content"
        assert len(agent.memory) == 1
        assert agent.memory[0]["type"] == "received"
        assert agent.memory[0]["processed"] is False

    @pytest.mark.asyncio
    async def test_send_message_with_orchestrator(self, agent, orchestrator):
        """send_message() must route through orchestrator."""
        await agent.send_message(
            content="test message",
            recipient="recipient_001",
            msg_type="task",
            priority=3,
        )

        assert len(orchestrator.messages) == 1
        sent_msg = orchestrator.messages[0]
        assert sent_msg.content == "test message"
        assert sent_msg.recipient == "recipient_001"
        assert sent_msg.msg_type == "task"
        assert sent_msg.priority == 3
        assert sent_msg.sender.startswith("test_agent[")

    @pytest.mark.asyncio
    async def test_send_message_without_orchestrator(self):
        """send_message() must use internal queue when no orchestrator."""
        standalone_agent = MockAgent(name="standalone", role=AgentRole.ANALYST)

        msg_id = await standalone_agent.send_message(content="direct message", recipient="all")

        # Message should be in internal queue
        assert standalone_agent.message_queue.qsize() == 1
        assert msg_id is not None
        assert len(msg_id) == 8  # UUID format

    @pytest.mark.asyncio
    async def test_message_processing_loop(self, agent):
        """process_messages() must actually process queued messages."""
        # Setup handler to track processed messages
        processed_messages: list[str] = []

        async def track_handler(msg: AgentMessage):
            processed_messages.append(msg.content)

        agent.register_handler("chat", track_handler)

        # Send messages
        await agent.receive_message(AgentMessage(sender="a", content="msg1", msg_type="chat"))
        await agent.receive_message(AgentMessage(sender="b", content="msg2", msg_type="chat"))

        # Start processing
        await agent.start()

        # Wait for processing
        await asyncio.sleep(0.2)

        await agent.stop()

        # Verify messages were processed
        assert len(processed_messages) == 2
        assert "msg1" in processed_messages
        assert "msg2" in processed_messages

        # Verify memory marked as processed
        processed_count = sum(1 for m in agent.memory if m["processed"])
        assert processed_count == 2


class TestAgentContext:
    """Test context management with real data."""

    def test_update_context_locally(self, agent):
        """update_context() must store values locally."""
        agent.update_context("scan_target", "example.com")
        agent.update_context("port_range", "80-443")

        assert agent.get_context("scan_target") == "example.com"
        assert agent.get_context("port_range") == "80-443"
        assert agent.get_context("nonexistent") is None

    @pytest.mark.asyncio
    async def test_update_context_with_share(self, agent, orchestrator):
        """update_context(share=True) must broadcast to orchestrator."""
        agent.update_context("shared_key", "shared_value", share=True)

        # Give async task time to execute
        await asyncio.sleep(0.1)

        assert "shared_key" in orchestrator.shared_context
        assert orchestrator.shared_context["shared_key"]["value"] == "shared_value"
        assert orchestrator.shared_context["shared_key"]["agent_id"] == agent.id

    def test_context_isolation_between_agents(self):
        """Each agent must have isolated context."""
        agent1 = MockAgent(name="agent1", role=AgentRole.RESEARCHER)
        agent2 = MockAgent(name="agent2", role=AgentRole.ANALYST)

        agent1.update_context("key", "value1")
        agent2.update_context("key", "value2")

        assert agent1.get_context("key") == "value1"
        assert agent2.get_context("key") == "value2"


class TestAgentMessageData:
    """Test AgentMessage dataclass behavior."""

    def test_message_to_dict_conversion(self):
        """to_dict() must serialize all fields correctly."""
        msg = AgentMessage(
            sender="test_sender",
            recipient="test_recipient",
            msg_type="task",
            content="test content",
            context={"key": "value"},
            priority=3,
            requires_response=True,
        )

        data = msg.to_dict()

        assert data["sender"] == "test_sender"
        assert data["recipient"] == "test_recipient"
        assert data["type"] == "task"
        assert data["content"] == "test content"
        assert data["context"] == {"key": "value"}
        assert data["priority"] == 3
        assert data["requires_response"] is True
        assert "id" in data
        assert "timestamp" in data

    def test_message_default_values(self):
        """AgentMessage must have sensible defaults."""
        msg = AgentMessage()

        assert msg.sender == ""
        assert msg.recipient == ""
        assert msg.msg_type == "chat"
        assert msg.content == ""
        assert msg.context == {}
        assert msg.priority == 1
        assert msg.requires_response is False
        assert len(msg.id) == 8


class TestAgentRoleAndStateEnums:
    """Test enum definitions."""

    def test_agent_role_values(self):
        """Test that AgentRole has all expected values."""
        roles = {r.value for r in AgentRole}
        expected = {
            "researcher",
            "analyst",
            "exploit",
            "coordinator",
            "reporter",
            "post_exploit",
        }
        assert roles == expected

    def test_agent_state_values(self):
        """Test that AgentState has all expected values."""
        states = {s.value for s in AgentState}
        expected = {
            "idle",
            "busy",
            "waiting",
            "completed",
            "failed",
            "stopped",
        }
        assert states == expected


class TestAgentErrorHandling:
    """Test error conditions and edge cases."""

    @pytest.mark.asyncio
    async def test_stop_without_start(self, agent):
        """Test that stop() does not fail if start() was never called."""
        assert agent.task is None

        await agent.stop()  # Should not raise

        assert agent.running is False

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_crash_agent(self, agent):
        """Exception in handler must not crash processing loop."""

        async def failing_handler(msg: AgentMessage):
            raise ValueError("Handler error")

        agent.register_handler("chat", failing_handler)

        # Send message that triggers failing handler
        await agent.receive_message(AgentMessage(sender="a", content="test", msg_type="chat"))

        # Start processing
        await agent.start()
        await asyncio.sleep(0.2)

        # Agent should still be running despite handler error
        assert agent.running is True

        await agent.stop()

    @pytest.mark.asyncio
    async def test_empty_message_queue_timeout(self, agent):
        """Empty queue must not block forever - timeout must work."""
        await agent.start()

        # Let it run with empty queue for a bit
        await asyncio.sleep(0.5)

        # Should still be running (not crashed)
        assert agent.running is True

        await agent.stop()
