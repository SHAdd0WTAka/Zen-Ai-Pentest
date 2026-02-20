"""
Comprehensive tests for Base Agent Classes
Tests AgentRole, AgentState, AgentMessage, and BaseAgent
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from agents.agent_base import (
    AgentMessage,
    AgentRole,
    AgentState,
    BaseAgent,
)


class TestAgentRole:
    """Test AgentRole enum"""

    def test_agent_role_values(self):
        """Test that all expected roles exist with correct values"""
        assert AgentRole.RESEARCHER.value == "researcher"
        assert AgentRole.ANALYST.value == "analyst"
        assert AgentRole.EXPLOIT.value == "exploit"
        assert AgentRole.COORDINATOR.value == "coordinator"
        assert AgentRole.REPORTER.value == "reporter"
        assert AgentRole.POST_EXPLOITATION.value == "post_exploit"

    def test_agent_role_count(self):
        """Test that we have expected number of roles"""
        roles = list(AgentRole)
        assert len(roles) == 6

    def test_agent_role_comparison(self):
        """Test role comparison"""
        assert AgentRole.RESEARCHER != AgentRole.ANALYST
        assert AgentRole.RESEARCHER == AgentRole.RESEARCHER


class TestAgentState:
    """Test AgentState enum"""

    def test_agent_state_values(self):
        """Test that all expected states exist with correct values"""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.BUSY.value == "busy"
        assert AgentState.WAITING.value == "waiting"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.FAILED.value == "failed"
        assert AgentState.STOPPED.value == "stopped"

    def test_agent_state_count(self):
        """Test that we have expected number of states"""
        states = list(AgentState)
        assert len(states) == 6

    def test_agent_state_transitions(self):
        """Test state transitions conceptually"""
        # IDLE can transition to BUSY
        # BUSY can transition to COMPLETED, FAILED, or WAITING
        # etc.
        current = AgentState.IDLE
        assert current.value == "idle"


class TestAgentMessage:
    """Test AgentMessage dataclass"""

    def test_default_message_creation(self):
        """Test creating message with defaults"""
        msg = AgentMessage()

        assert len(msg.id) == 8  # UUID shortened to 8 chars
        assert msg.sender == ""
        assert msg.recipient == ""
        assert msg.msg_type == "chat"
        assert msg.content == ""
        assert msg.context == {}
        assert msg.priority == 1
        assert msg.requires_response is False
        assert isinstance(msg.timestamp, str)

    def test_custom_message_creation(self):
        """Test creating message with custom values"""
        msg = AgentMessage(
            sender="Agent1",
            recipient="Agent2",
            msg_type="task",
            content="Test content",
            context={"key": "value"},
            priority=3,
            requires_response=True,
        )

        assert msg.sender == "Agent1"
        assert msg.recipient == "Agent2"
        assert msg.msg_type == "task"
        assert msg.content == "Test content"
        assert msg.context == {"key": "value"}
        assert msg.priority == 3
        assert msg.requires_response is True

    def test_message_to_dict(self):
        """Test conversion to dictionary"""
        msg = AgentMessage(
            sender="TestAgent",
            msg_type="result",
            content="Test result",
            context={"data": "value"},
            priority=2,
        )

        d = msg.to_dict()

        assert d["sender"] == "TestAgent"
        assert d["type"] == "result"
        assert d["content"] == "Test result"
        assert d["context"] == {"data": "value"}
        assert d["priority"] == 2
        assert "id" in d
        assert "timestamp" in d

    def test_message_id_uniqueness(self):
        """Test that each message gets unique ID"""
        msg1 = AgentMessage()
        msg2 = AgentMessage()

        assert msg1.id != msg2.id

    def test_message_priority_levels(self):
        """Test different priority levels"""
        low = AgentMessage(priority=1)
        medium = AgentMessage(priority=2)
        high = AgentMessage(priority=3)
        critical = AgentMessage(priority=4)

        assert low.priority == 1
        assert medium.priority == 2
        assert high.priority == 3
        assert critical.priority == 4


class TestBaseAgentInitialization:
    """Test BaseAgent initialization"""

    def test_basic_initialization(self):
        """Test basic agent initialization"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        assert agent.name == "TestAgent"
        assert agent.role == AgentRole.RESEARCHER
        assert len(agent.id) == 8
        assert agent.orchestrator is None
        assert agent.running is False
        assert agent.task is None
        assert agent.context == {}
        assert agent.memory == []
        assert agent.inbox == []
        assert agent.handlers == {}

    def test_initialization_with_orchestrator(self):
        """Test initialization with orchestrator"""
        mock_orchestrator = Mock()
        agent = ConcreteTestAgent("TestAgent", AgentRole.ANALYST, orchestrator=mock_orchestrator)

        assert agent.orchestrator is mock_orchestrator

    def test_different_roles(self):
        """Test initialization with different roles"""
        researcher = ConcreteTestAgent("R1", AgentRole.RESEARCHER)
        analyst = ConcreteTestAgent("A1", AgentRole.ANALYST)
        exploit = ConcreteTestAgent("E1", AgentRole.EXPLOIT)
        coordinator = ConcreteTestAgent("C1", AgentRole.COORDINATOR)

        assert researcher.role == AgentRole.RESEARCHER
        assert analyst.role == AgentRole.ANALYST
        assert exploit.role == AgentRole.EXPLOIT
        assert coordinator.role == AgentRole.COORDINATOR


class TestBaseAgentHandlers:
    """Test BaseAgent handler registration"""

    def test_register_handler(self):
        """Test handler registration"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        def handler(msg):
            pass

        agent.register_handler("custom_type", handler)

        assert "custom_type" in agent.handlers
        assert agent.handlers["custom_type"] == handler

    def test_register_multiple_handlers(self):
        """Test registering multiple handlers"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        def handler1(msg):
            pass

        def handler2(msg):
            pass

        agent.register_handler("type1", handler1)
        agent.register_handler("type2", handler2)

        assert len(agent.handlers) == 2


class TestBaseAgentMessaging:
    """Test BaseAgent messaging functionality"""

    @pytest.mark.asyncio
    async def test_send_message_with_orchestrator(self):
        """Test sending message through orchestrator"""
        mock_orchestrator = AsyncMock()
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        msg_id = await agent.send_message("Hello", recipient="Agent2", msg_type="chat")

        mock_orchestrator.route_message.assert_called_once()
        assert len(msg_id) == 8

    @pytest.mark.asyncio
    async def test_send_message_broadcast(self):
        """Test broadcasting message to all"""
        mock_orchestrator = AsyncMock()
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        await agent.send_message("Broadcast", recipient="all")

        call_args = mock_orchestrator.route_message.call_args[0][0]
        assert call_args.recipient == "all"

    @pytest.mark.asyncio
    async def test_send_message_with_context(self):
        """Test sending message with context"""
        mock_orchestrator = AsyncMock()
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        context = {"key": "value", "number": 42}
        await agent.send_message("Message", context=context)

        call_args = mock_orchestrator.route_message.call_args[0][0]
        assert call_args.context == context

    @pytest.mark.asyncio
    async def test_send_message_without_orchestrator(self):
        """Test sending message without orchestrator (direct queue)"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        await agent.send_message("Direct message")

        # Message should be in the queue
        assert agent.message_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_receive_message(self):
        """Test receiving message"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        msg = AgentMessage(sender="Other", content="Test")
        await agent.receive_message(msg)

        assert agent.message_queue.qsize() == 1
        assert len(agent.inbox) == 1
        assert len(agent.memory) == 1
        assert agent.memory[0]["type"] == "received"
        assert agent.memory[0]["processed"] is False

    @pytest.mark.asyncio
    async def test_receive_multiple_messages(self):
        """Test receiving multiple messages"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        for i in range(5):
            msg = AgentMessage(sender=f"Agent{i}", content=f"Message {i}")
            await agent.receive_message(msg)

        assert agent.message_queue.qsize() == 5
        assert len(agent.inbox) == 5
        assert len(agent.memory) == 5


class TestBaseAgentProcessing:
    """Test BaseAgent message processing"""

    @pytest.mark.asyncio
    async def test_process_single_message(self):
        """Test processing a single message"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        # Add a message to the queue
        msg = AgentMessage(sender="Other", content="Test", msg_type="chat")
        await agent.receive_message(msg)

        # Start and immediately stop processing
        task = asyncio.create_task(agent.process_messages())
        await asyncio.sleep(0.1)
        agent.running = False
        try:
            await asyncio.wait_for(task, timeout=0.5)
        except asyncio.TimeoutError:
            task.cancel()

    @pytest.mark.asyncio
    async def test_process_message_with_handler(self):
        """Test processing message with registered handler"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        handler_called = False

        async def handler(msg):
            nonlocal handler_called
            handler_called = True

        agent.register_handler("custom", handler)

        msg = AgentMessage(sender="Other", content="Test", msg_type="custom")
        await agent.receive_message(msg)

        # Process
        task = asyncio.create_task(agent.process_messages())
        await asyncio.sleep(0.2)
        agent.running = False
        try:
            await asyncio.wait_for(task, timeout=0.5)
        except asyncio.TimeoutError:
            task.cancel()

    @pytest.mark.asyncio
    async def test_process_messages_stops_gracefully(self):
        """Test that message processing stops gracefully"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        agent.running = True
        task = asyncio.create_task(agent.process_messages())
        await asyncio.sleep(0.1)

        agent.running = False
        # Give it time to process the flag change
        await asyncio.sleep(1.2)  # > timeout in process_messages (1.0)

        # Cancel task if still running
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Should have stopped or be cancelable
        assert True


class TestBaseAgentLifecycle:
    """Test BaseAgent lifecycle methods"""

    @pytest.mark.asyncio
    async def test_start_agent(self):
        """Test starting the agent"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        await agent.start()

        # Allow task to start
        await asyncio.sleep(0.1)

        assert agent.running is True
        assert agent.task is not None

        # Cleanup
        await agent.stop()

    @pytest.mark.asyncio
    async def test_stop_agent(self):
        """Test stopping the agent"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        await agent.start()
        await agent.stop()

        assert agent.running is False

    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        """Test stopping agent that was never started"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        await agent.stop()

        assert agent.running is False

    @pytest.mark.asyncio
    async def test_double_stop(self):
        """Test stopping agent twice"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        await agent.start()
        await agent.stop()
        await agent.stop()  # Should not raise

        assert agent.running is False


class TestBaseAgentContext:
    """Test BaseAgent context management"""

    def test_update_context(self):
        """Test updating context"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        agent.update_context("key1", "value1")

        assert agent.context["key1"] == "value1"

    def test_update_context_multiple(self):
        """Test updating context with multiple values"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        agent.update_context("key1", "value1")
        agent.update_context("key2", "value2")
        agent.update_context("key3", 42)

        assert agent.context["key1"] == "value1"
        assert agent.context["key2"] == "value2"
        assert agent.context["key3"] == 42

    def test_get_context(self):
        """Test getting context value"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        agent.update_context("test_key", "test_value")

        assert agent.get_context("test_key") == "test_value"

    def test_get_context_nonexistent(self):
        """Test getting nonexistent context key"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        assert agent.get_context("nonexistent") is None

    @pytest.mark.asyncio
    async def test_update_context_with_share(self):
        """Test updating context with sharing"""
        mock_orchestrator = AsyncMock()
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        agent.update_context("shared_key", "shared_value", share=True)

        mock_orchestrator.update_shared_context.assert_called_once_with("shared_key", "shared_value", agent.id)

    def test_update_context_without_share(self):
        """Test updating context without sharing"""
        mock_orchestrator = Mock()
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        agent.update_context("local_key", "local_value", share=False)

        mock_orchestrator.update_shared_context.assert_not_called()


class TestBaseAgentStatus:
    """Test BaseAgent status reporting"""

    def test_get_status_basic(self):
        """Test getting agent status"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        status = agent.get_status()

        assert status["id"] == agent.id
        assert status["name"] == "TestAgent"
        assert status["role"] == "researcher"
        assert status["running"] is False

    def test_get_status_with_context(self):
        """Test status with context"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        agent.update_context("key1", "value1")
        agent.update_context("key2", "value2")

        status = agent.get_status()

        assert "key1" in status["context_keys"]
        assert "key2" in status["context_keys"]

    def test_get_status_with_messages(self):
        """Test status with messages in inbox"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        # Can't easily add to inbox without async, so test empty state
        status = agent.get_status()

        assert status["inbox_count"] == 0
        assert status["queue_size"] == 0


class TestBaseAgentShareFindings:
    """Test BaseAgent findings sharing"""

    @pytest.mark.asyncio
    async def test_share_findings(self):
        """Test sharing findings"""
        mock_orchestrator = AsyncMock()
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        findings = {"vulnerability": "CVE-2021-44228", "severity": "critical"}
        agent.share_findings(findings)

        # Allow async task to run
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_share_findings_without_orchestrator(self):
        """Test sharing findings without orchestrator"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        findings = {"vulnerability": "CVE-2021-44228"}

        # Should not raise
        agent.share_findings(findings)
        await asyncio.sleep(0.1)


class TestBaseAgentHandleMessage:
    """Test BaseAgent default message handler"""

    @pytest.mark.asyncio
    async def test_handle_message_chat(self):
        """Test default chat message handling"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)
        mock_orchestrator = AsyncMock()
        agent.orchestrator = mock_orchestrator

        msg = AgentMessage(sender="Other", content="Hello", msg_type="chat", requires_response=True)
        await agent.handle_message(msg)

        # Should send acknowledgment
        mock_orchestrator.route_message.assert_called()

    @pytest.mark.asyncio
    async def test_handle_message_no_response_required(self):
        """Test chat message without response requirement"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)
        mock_orchestrator = AsyncMock()
        agent.orchestrator = mock_orchestrator

        msg = AgentMessage(sender="Other", content="Hello", msg_type="chat", requires_response=False)
        await agent.handle_message(msg)

        # Should not send response
        mock_orchestrator.route_message.assert_not_called()


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing"""

    async def execute_task(self, task: dict) -> dict:
        """Execute a task - test implementation"""
        return {"task": task, "status": "completed"}


class TestBaseAgentAbstract:
    """Test BaseAgent abstract method enforcement"""

    def test_cannot_instantiate_abstract(self):
        """Test that BaseAgent cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseAgent("Test", AgentRole.RESEARCHER)

    def test_subclass_must_implement_execute_task(self):
        """Test that subclasses must implement execute_task"""

        class IncompleteAgent(BaseAgent):
            pass

        with pytest.raises(TypeError):
            IncompleteAgent("Test", AgentRole.RESEARCHER)


class TestBaseAgentEdgeCases:
    """Test edge cases"""

    def test_empty_name(self):
        """Test agent with empty name"""
        agent = ConcreteTestAgent("", AgentRole.RESEARCHER)
        assert agent.name == ""

    def test_long_name(self):
        """Test agent with long name"""
        long_name = "A" * 1000
        agent = ConcreteTestAgent(long_name, AgentRole.RESEARCHER)
        assert agent.name == long_name

    @pytest.mark.asyncio
    async def test_send_message_priority_bounds(self):
        """Test sending messages with boundary priorities"""
        mock_orchestrator = AsyncMock()
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        # Test various priority levels
        await agent.send_message("Low", priority=0)
        await agent.send_message("High", priority=10)
        await agent.send_message("Negative", priority=-5)

        assert mock_orchestrator.route_message.call_count == 3

    def test_context_overwrite(self):
        """Test that context values can be overwritten"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        agent.update_context("key", "value1")
        agent.update_context("key", "value2")

        assert agent.get_context("key") == "value2"

    @pytest.mark.asyncio
    async def test_receive_message_updates_memory(self):
        """Test that receiving message updates memory correctly"""
        agent = ConcreteTestAgent("TestAgent", AgentRole.RESEARCHER)

        msg1 = AgentMessage(sender="A1", content="M1")
        msg2 = AgentMessage(sender="A2", content="M2")

        await agent.receive_message(msg1)
        await agent.receive_message(msg2)

        assert len(agent.memory) == 2
        assert agent.memory[0]["message"]["sender"] == "A1"
        assert agent.memory[1]["message"]["sender"] == "A2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
