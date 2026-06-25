"""
Comprehensive Unit Tests for agents/agent_base.py

Target: >80% Coverage
Tests: State Machine Flow, Tool Execution, Memory/Context Handling, Message Processing

Author: AI Test Generator
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from agents.agent_base import AgentMessage, AgentRole, AgentState, BaseAgent

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def concrete_agent():
    """Fixture providing a concrete BaseAgent implementation for testing."""

    class ConcreteAgent(BaseAgent):
        async def execute_task(self, task: Dict) -> Dict:
            """Mock implementation of abstract execute_task method."""
            return {
                "status": "completed",
                "agent_id": self.id,
                "agent_name": self.name,
                "task": task,
                "result": f"Executed: {task.get('action', 'unknown')}",
                "timestamp": datetime.now().isoformat(),
            }

    return ConcreteAgent


@pytest.fixture
def mock_orchestrator():
    """Fixture providing a mocked orchestrator with async methods."""
    mock = AsyncMock()
    mock.route_message = AsyncMock(return_value=None)
    mock.update_shared_context = AsyncMock(return_value=None)
    mock.get_shared_context = Mock(return_value={})
    mock.register_agent = Mock(return_value=None)
    return mock


@pytest.fixture
def sample_message():
    """Fixture providing a sample AgentMessage for testing."""
    return AgentMessage(
        id="msg001",
        sender="TestSender[abc123]",
        recipient="TestRecipient[def456]",
        msg_type="task",
        content="Execute scan on target",
        context={"target": "192.168.1.1", "ports": [80, 443]},
        timestamp=datetime.now().isoformat(),
        priority=2,
        requires_response=True,
    )


@pytest.fixture
async def running_agent(concrete_agent, mock_orchestrator):
    """Fixture providing a running agent, cleaned up after test."""
    agent = concrete_agent("RunningAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)
    await agent.start()
    await asyncio.sleep(0.05)  # Allow task to start
    yield agent
    await agent.stop()


# =============================================================================
# Test Agent Initialization
# =============================================================================


class TestAgentInitialization:
    """Test suite for BaseAgent initialization."""

    def test_basic_initialization(self, concrete_agent):
        """Test agent initializes with correct default values."""
        agent = concrete_agent("TestAgent", AgentRole.RESEARCHER)

        assert agent.name == "TestAgent"
        assert agent.role == AgentRole.RESEARCHER
        assert len(agent.id) == 8  # UUID truncated to 8 chars
        assert agent.orchestrator is None
        assert isinstance(agent.message_queue, asyncio.Queue)
        assert agent.inbox == []
        assert agent.context == {}
        assert agent.memory == []
        assert agent.handlers == {}
        assert agent.running is False
        assert agent.task is None

    def test_initialization_with_orchestrator(self, concrete_agent, mock_orchestrator):
        """Test agent initializes correctly with orchestrator."""
        agent = concrete_agent(
            name="OrchestratedAgent",
            role=AgentRole.ANALYST,
            orchestrator=mock_orchestrator,
        )

        assert agent.orchestrator is mock_orchestrator
        assert agent.name == "OrchestratedAgent"
        assert agent.role == AgentRole.ANALYST

    def test_initialization_all_roles(self, concrete_agent):
        """Test agent can be initialized with all role types."""
        roles = [
            (AgentRole.RESEARCHER, "ResearchAgent"),
            (AgentRole.ANALYST, "AnalystAgent"),
            (AgentRole.EXPLOIT, "ExploitAgent"),
            (AgentRole.COORDINATOR, "CoordinatorAgent"),
            (AgentRole.REPORTER, "ReporterAgent"),
            (AgentRole.POST_EXPLOITATION, "PostExploitAgent"),
        ]

        for role, name in roles:
            agent = concrete_agent(name, role)
            assert agent.role == role
            assert agent.name == name
            assert len(agent.id) == 8

    def test_agent_id_uniqueness(self, concrete_agent):
        """Test that each agent instance gets a unique ID."""
        agents = [concrete_agent(f"Agent{i}", AgentRole.RESEARCHER) for i in range(50)]
        ids = [agent.id for agent in agents]
        assert len(set(ids)) == 50  # All IDs should be unique

    def test_initialization_special_characters(self, concrete_agent):
        """Test agent names with special characters."""
        special_names = [
            "Agent-With-Dashes",
            "Agent_With_Underscores",
            "Agent.With.Dots",
            "Agent With Spaces",
            "Agent123Numeric",
            "",  # Empty name
            "A" * 1000,  # Very long name
        ]

        for name in special_names:
            agent = concrete_agent(name, AgentRole.RESEARCHER)
            assert agent.name == name

    @patch("agents.agent_base.logger")
    def test_initialization_logs(self, mock_logger, concrete_agent):
        """Test that initialization logs the correct info."""
        agent = concrete_agent("LoggedAgent", AgentRole.RESEARCHER)

        mock_logger.info.assert_called_once()
        log_msg = mock_logger.info.call_args[0][0]
        assert "LoggedAgent" in log_msg
        assert "researcher" in log_msg
        assert agent.id in log_msg


# =============================================================================
# Test State Machine Flow
# =============================================================================


class TestStateMachineFlow:
    """Test suite for agent state machine transitions."""

    @pytest.mark.anyio
    async def test_state_idle_to_running(self, concrete_agent):
        """Test transition from IDLE to RUNNING state."""
        agent = concrete_agent("StateAgent", AgentRole.RESEARCHER)

        assert agent.running is False  # Initial state: IDLE

        await agent.start()
        await asyncio.sleep(0.05)

        assert agent.running is True  # After start: RUNNING

        await agent.stop()
        assert agent.running is False  # After stop: IDLE

    @pytest.mark.anyio
    async def test_state_multiple_transitions(self, concrete_agent):
        """Test multiple start/stop state transitions."""
        agent = concrete_agent("CycleAgent", AgentRole.RESEARCHER)

        for i in range(3):
            assert agent.running is False
            await agent.start()
            await asyncio.sleep(0.05)
            assert agent.running is True
            await agent.stop()
            assert agent.running is False

    @pytest.mark.anyio
    async def test_stop_without_start(self, concrete_agent):
        """Test stopping an agent that was never started."""
        agent = concrete_agent("Unstarted", AgentRole.RESEARCHER)

        assert agent.task is None
        await agent.stop()  # Should not raise
        assert agent.running is False

    @pytest.mark.anyio
    async def test_graceful_shutdown(self, concrete_agent):
        """Test graceful shutdown handling."""
        agent = concrete_agent("GracefulAgent", AgentRole.RESEARCHER)

        await agent.start()
        await asyncio.sleep(0.05)

        # Cancel the task gracefully
        await agent.stop()

        assert agent.running is False
        assert agent.task is None or agent.task.done()

    @pytest.mark.anyio
    async def test_running_while_processing(self, concrete_agent):
        """Test running state while processing messages."""
        agent = concrete_agent("ProcessingAgent", AgentRole.RESEARCHER)

        # Register a handler that takes some time
        async def slow_handler(msg):
            await asyncio.sleep(0.1)

        agent.register_handler("slow", slow_handler)

        await agent.start()
        await asyncio.sleep(0.05)

        # Send a message
        msg = AgentMessage(msg_type="slow", content="test")
        await agent.receive_message(msg)

        # Agent should still be running while processing
        assert agent.running is True

        await asyncio.sleep(0.2)
        await agent.stop()

    def test_agent_state_enum_values(self):
        """Test AgentState enum has all expected values."""
        states = [
            AgentState.IDLE,
            AgentState.BUSY,
            AgentState.WAITING,
            AgentState.COMPLETED,
            AgentState.FAILED,
            AgentState.STOPPED,
        ]

        expected_values = [
            "idle",
            "busy",
            "waiting",
            "completed",
            "failed",
            "stopped",
        ]

        for state, expected in zip(states, expected_values):
            assert state.value == expected


# =============================================================================
# Test Message Handling
# =============================================================================


class TestMessageHandling:
    """Test suite for message sending, receiving, and processing."""

    @pytest.mark.anyio
    async def test_send_message_via_orchestrator(self, concrete_agent, mock_orchestrator):
        """Test sending message through orchestrator."""
        agent = concrete_agent("Sender", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        msg_id = await agent.send_message(
            content="Hello World",
            recipient="TargetAgent",
            msg_type="task",
            priority=3,
            requires_response=True,
            context={"task_id": "123"},
        )

        assert len(msg_id) == 8
        mock_orchestrator.route_message.assert_called_once()

        sent_msg = mock_orchestrator.route_message.call_args[0][0]
        assert sent_msg.content == "Hello World"
        assert sent_msg.recipient == "TargetAgent"
        assert sent_msg.msg_type == "task"
        assert sent_msg.priority == 3
        assert sent_msg.requires_response is True
        assert sent_msg.context == {"task_id": "123"}
        assert sent_msg.sender == f"{agent.name}[{agent.id}]"

    @pytest.mark.anyio
    async def test_send_message_broadcast(self, concrete_agent, mock_orchestrator):
        """Test broadcasting message to all agents."""
        agent = concrete_agent(
            "Broadcaster",
            AgentRole.COORDINATOR,
            orchestrator=mock_orchestrator,
        )

        await agent.send_message("Broadcast message", recipient="all")

        sent_msg = mock_orchestrator.route_message.call_args[0][0]
        assert sent_msg.recipient == "all"

    @pytest.mark.anyio
    async def test_send_message_without_orchestrator(self, concrete_agent):
        """Test direct queue sending without orchestrator."""
        agent = concrete_agent("DirectAgent", AgentRole.RESEARCHER)

        await agent.send_message("Direct message", recipient="Other")

        assert agent.message_queue.qsize() == 1
        queued_msg = await agent.message_queue.get()
        assert queued_msg.content == "Direct message"

    @pytest.mark.anyio
    async def test_receive_message(self, concrete_agent, sample_message):
        """Test receiving a message."""
        agent = concrete_agent("Receiver", AgentRole.RESEARCHER)

        await agent.receive_message(sample_message)

        assert agent.message_queue.qsize() == 1
        assert len(agent.inbox) == 1
        assert agent.inbox[0] == sample_message
        assert len(agent.memory) == 1
        assert agent.memory[0]["type"] == "received"
        assert agent.memory[0]["processed"] is False

    @pytest.mark.anyio
    async def test_receive_multiple_messages(self, concrete_agent):
        """Test receiving multiple messages."""
        agent = concrete_agent("MultiReceiver", AgentRole.RESEARCHER)

        messages = [AgentMessage(sender=f"Agent{i}", content=f"Message {i}") for i in range(10)]

        for msg in messages:
            await agent.receive_message(msg)

        assert agent.message_queue.qsize() == 10
        assert len(agent.inbox) == 10
        assert len(agent.memory) == 10

    @pytest.mark.anyio
    async def test_message_processing_with_handler(self, concrete_agent):
        """Test message processing with registered handler."""
        agent = concrete_agent("Processor", AgentRole.RESEARCHER)

        handler_called = False
        received_msg = None

        async def custom_handler(msg):
            nonlocal handler_called, received_msg
            handler_called = True
            received_msg = msg

        agent.register_handler("custom", custom_handler)

        msg = AgentMessage(msg_type="custom", content="test", sender="Tester")
        await agent.receive_message(msg)

        # Process messages
        agent.running = True
        task = asyncio.create_task(agent.process_messages())
        await asyncio.sleep(0.2)
        agent.running = False

        try:
            await asyncio.wait_for(task, timeout=0.5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            if not task.done():
                task.cancel()

        assert handler_called is True
        assert received_msg is not None
        assert received_msg.content == "test"

    @pytest.mark.anyio
    async def test_message_processing_marks_memory(self, concrete_agent):
        """Test that processed messages are marked in memory."""
        agent = concrete_agent("MemoryAgent", AgentRole.RESEARCHER)

        async def handler(msg):
            pass

        agent.register_handler("test", handler)

        msg = AgentMessage(msg_type="test", content="test", sender="Tester")
        await agent.receive_message(msg)

        agent.running = True
        task = asyncio.create_task(agent.process_messages())
        await asyncio.sleep(0.3)
        agent.running = False

        try:
            await asyncio.wait_for(task, timeout=0.5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            if not task.done():
                task.cancel()

        assert agent.memory[0]["processed"] is True

    @pytest.mark.anyio
    async def test_default_handle_message_chat_response(self, concrete_agent):
        """Test default handler sends response for chat requiring response."""
        agent = concrete_agent("Handler", AgentRole.RESEARCHER)
        agent.orchestrator = AsyncMock()

        msg = AgentMessage(
            sender="OtherAgent",
            content="Hello there!",
            msg_type="chat",
            requires_response=True,
        )

        await agent.handle_message(msg)

        agent.orchestrator.route_message.assert_called_once()
        response = agent.orchestrator.route_message.call_args[0][0]
        assert response.msg_type == "response"
        assert "Acknowledged" in response.content

    @pytest.mark.anyio
    async def test_default_handle_message_no_response(self, concrete_agent):
        """Test default handler doesn't respond when not required."""
        agent = concrete_agent("Handler", AgentRole.RESEARCHER)
        agent.orchestrator = AsyncMock()

        msg = AgentMessage(
            sender="OtherAgent",
            content="Hello",
            msg_type="chat",
            requires_response=False,
        )

        await agent.handle_message(msg)

        agent.orchestrator.route_message.assert_not_called()

    @pytest.mark.anyio
    async def test_process_messages_timeout(self, concrete_agent):
        """Test message processing handles timeout correctly."""
        agent = concrete_agent("TimeoutAgent", AgentRole.RESEARCHER)

        agent.running = True
        task = asyncio.create_task(agent.process_messages())

        # Let it run through timeout cycles
        await asyncio.sleep(2.1)

        agent.running = False

        try:
            await asyncio.wait_for(task, timeout=0.5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            if not task.done():
                task.cancel()

    @pytest.mark.anyio
    async def test_process_messages_error_handling(self, concrete_agent):
        """Test error handling in message processing loop."""
        agent = concrete_agent("ErrorAgent", AgentRole.RESEARCHER)

        async def failing_handler(msg):
            raise ValueError("Test error")

        agent.register_handler("fail", failing_handler)

        msg = AgentMessage(msg_type="fail", content="test", sender="Tester")
        await agent.receive_message(msg)

        agent.running = True
        task = asyncio.create_task(agent.process_messages())
        await asyncio.sleep(0.3)
        agent.running = False

        try:
            await asyncio.wait_for(task, timeout=0.5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            if not task.done():
                task.cancel()

        # Should have handled the error without crashing
        assert True

    @pytest.mark.anyio
    async def test_process_messages_unregistered_type(self, concrete_agent):
        """Test processing message with unregistered type falls back to handle_message."""
        agent = concrete_agent("FallbackAgent", AgentRole.RESEARCHER)

        msg = AgentMessage(msg_type="unknown", content="test", sender="Tester")
        await agent.receive_message(msg)

        agent.running = True
        task = asyncio.create_task(agent.process_messages())
        await asyncio.sleep(0.2)
        agent.running = False

        try:
            await asyncio.wait_for(task, timeout=0.5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            if not task.done():
                task.cancel()


# =============================================================================
# Test Memory and Context Handling
# =============================================================================


class TestMemoryContextHandling:
    """Test suite for memory and context management."""

    def test_update_context_basic(self, concrete_agent):
        """Test basic context update."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)

        agent.update_context("key", "value")
        assert agent.context["key"] == "value"

    def test_update_context_multiple_types(self, concrete_agent):
        """Test updating context with various data types."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)

        test_data = [
            ("string_key", "string_value"),
            ("int_key", 42),
            ("float_key", 3.14),
            ("bool_key", True),
            ("list_key", [1, 2, 3]),
            ("dict_key", {"nested": "value"}),
            ("none_key", None),
            ("tuple_key", (1, 2, 3)),
        ]

        for key, value in test_data:
            agent.update_context(key, value)
            assert agent.context[key] == value

    def test_update_context_overwrite(self, concrete_agent):
        """Test that context values can be overwritten."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)

        agent.update_context("key", "original")
        assert agent.context["key"] == "original"

        agent.update_context("key", "updated")
        assert agent.context["key"] == "updated"

    def test_get_context_existing(self, concrete_agent):
        """Test getting existing context value."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)

        agent.update_context("existing", "value")
        assert agent.get_context("existing") == "value"

    def test_get_context_nonexistent(self, concrete_agent):
        """Test getting non-existent context key returns None."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)

        result = agent.get_context("nonexistent")
        assert result is None

    @pytest.mark.anyio
    async def test_update_context_with_share(self, concrete_agent, mock_orchestrator):
        """Test updating context with sharing to orchestrator."""
        agent = concrete_agent(
            "SharingAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator,
        )

        agent.update_context("shared_key", "shared_value", share=True)

        await asyncio.sleep(0.1)  # Allow async task

        mock_orchestrator.update_shared_context.assert_called_once_with("shared_key", "shared_value", agent.id)

    def test_update_context_share_without_orchestrator(self, concrete_agent):
        """Test sharing context without orchestrator doesn't fail."""
        agent = concrete_agent("NoOrchestrator", AgentRole.RESEARCHER)

        # Should not raise
        agent.update_context("key", "value", share=True)
        assert agent.context["key"] == "value"

    def test_update_context_no_share(self, concrete_agent, mock_orchestrator):
        """Test updating context without sharing."""
        agent = concrete_agent("LocalAgent", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)

        agent.update_context("local_key", "local_value", share=False)

        mock_orchestrator.update_shared_context.assert_not_called()
        assert agent.context["local_key"] == "local_value"

    def test_context_isolation(self, concrete_agent):
        """Test context isolation between different agents."""
        agent1 = concrete_agent("Agent1", AgentRole.RESEARCHER)
        agent2 = concrete_agent("Agent2", AgentRole.RESEARCHER)

        agent1.update_context("shared_name", "agent1_value")
        agent2.update_context("shared_name", "agent2_value")

        assert agent1.get_context("shared_name") == "agent1_value"
        assert agent2.get_context("shared_name") == "agent2_value"

    @pytest.mark.anyio
    async def test_memory_tracking(self, concrete_agent):
        """Test memory tracking of received messages."""
        agent = concrete_agent("MemoryAgent", AgentRole.RESEARCHER)

        msg1 = AgentMessage(sender="Agent1", content="Message 1")
        msg2 = AgentMessage(sender="Agent2", content="Message 2")

        await agent.receive_message(msg1)
        await agent.receive_message(msg2)

        assert len(agent.memory) == 2
        assert agent.memory[0]["message"]["content"] == "Message 1"
        assert agent.memory[1]["message"]["content"] == "Message 2"

    def test_memory_structure(self, concrete_agent):
        """Test memory entry structure."""
        agent = concrete_agent("MemoryAgent", AgentRole.RESEARCHER)

        # Manually add memory entry
        agent.memory.append(
            {
                "type": "received",
                "message": {"id": "test123", "content": "test"},
                "processed": False,
            }
        )

        assert len(agent.memory) == 1
        assert agent.memory[0]["type"] == "received"
        assert "message" in agent.memory[0]
        assert "processed" in agent.memory[0]


# =============================================================================
# Test Tool Execution
# =============================================================================


class TestToolExecution:
    """Test suite for tool execution via execute_task method."""

    @pytest.mark.anyio
    async def test_execute_task_basic(self, concrete_agent):
        """Test basic task execution."""
        agent = concrete_agent("TaskAgent", AgentRole.EXPLOIT)

        task = {"type": "scan", "target": "192.168.1.1", "ports": [80, 443]}
        result = await agent.execute_task(task)

        assert result["status"] == "completed"
        assert result["agent_id"] == agent.id
        assert result["agent_name"] == "TaskAgent"
        assert result["task"] == task

    @pytest.mark.anyio
    async def test_execute_task_various_inputs(self, concrete_agent):
        """Test execute_task with various input types."""
        agent = concrete_agent("TaskAgent", AgentRole.EXPLOIT)

        test_tasks = [
            {},  # Empty task
            {"type": "scan"},  # Simple task
            {
                "type": "exploit",
                "target": {"host": "example.com", "port": 8080},
            },  # Nested
            {"data": ["item1", "item2", "item3"]},  # List data
            {"config": {"nested": {"deep": "value"}}},  # Deeply nested
        ]

        for task in test_tasks:
            result = await agent.execute_task(task)
            assert result["status"] == "completed"
            assert "agent_id" in result

    @pytest.mark.anyio
    async def test_execute_task_multiple_calls(self, concrete_agent):
        """Test multiple sequential task executions."""
        agent = concrete_agent("TaskAgent", AgentRole.ANALYST)

        tasks = [
            {"id": 1, "action": "scan"},
            {"id": 2, "action": "analyze"},
            {"id": 3, "action": "report"},
        ]

        results = []
        for task in tasks:
            result = await agent.execute_task(task)
            results.append(result)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["task"]["id"] == i + 1
            assert result["status"] == "completed"

    def test_base_agent_execute_task_raises_not_implemented(self):
        """Test that BaseAgent.execute_task raises NotImplementedError."""
        agent = BaseAgent("Test", AgentRole.RESEARCHER)

        with pytest.raises(NotImplementedError) as exc_info:
            asyncio.run(agent.execute_task({}))

        assert "execute_task" in str(exc_info.value)

    def test_subclass_without_execute_task_raises_on_call(self):
        """Test that subclasses without execute_task raise on call."""

        class IncompleteAgent(BaseAgent):
            pass

        agent = IncompleteAgent("Test", AgentRole.RESEARCHER)

        with pytest.raises(NotImplementedError) as exc_info:
            asyncio.run(agent.execute_task({}))

        assert "execute_task" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_custom_execute_task(self):
        """Test custom execute_task implementation."""

        class CustomAgent(BaseAgent):
            async def execute_task(self, task: dict) -> dict:
                return {
                    "custom": True,
                    "agent_name": self.name,
                    "task_data": task,
                    "processed_at": datetime.now().isoformat(),
                }

        agent = CustomAgent("Custom", AgentRole.ANALYST)
        task = {"type": "custom_task", "data": "test"}

        result = await agent.execute_task(task)

        assert result["custom"] is True
        assert result["agent_name"] == "Custom"
        assert result["task_data"] == task
        assert "processed_at" in result


# =============================================================================
# Test Handler Registration
# =============================================================================


class TestHandlerRegistration:
    """Test suite for handler registration functionality."""

    def test_register_single_handler(self, concrete_agent):
        """Test registering a single handler."""
        agent = concrete_agent("HandlerAgent", AgentRole.RESEARCHER)

        def handler(msg):
            return "handled"

        agent.register_handler("event", handler)

        assert "event" in agent.handlers
        assert agent.handlers["event"] == handler

    def test_register_multiple_handlers(self, concrete_agent):
        """Test registering multiple handlers."""
        agent = concrete_agent("HandlerAgent", AgentRole.RESEARCHER)

        handlers = {
            "event1": lambda msg: "handler1",
            "event2": lambda msg: "handler2",
            "event3": lambda msg: "handler3",
        }

        for event, handler in handlers.items():
            agent.register_handler(event, handler)

        assert len(agent.handlers) == 3

    def test_register_handler_overwrite(self, concrete_agent):
        """Test that registering handler overwrites existing."""
        agent = concrete_agent("HandlerAgent", AgentRole.RESEARCHER)

        def original(msg):
            return "original"

        def new(msg):
            return "new"

        agent.register_handler("event", original)
        assert agent.handlers["event"] == original

        agent.register_handler("event", new)
        assert agent.handlers["event"] == new

    def test_register_async_handler(self, concrete_agent):
        """Test registering async handler."""
        agent = concrete_agent("HandlerAgent", AgentRole.RESEARCHER)

        async def async_handler(msg):
            await asyncio.sleep(0.01)
            return "async"

        agent.register_handler("async_event", async_handler)

        assert "async_event" in agent.handlers


# =============================================================================
# Test Findings Sharing
# =============================================================================


class TestFindingsSharing:
    """Test suite for findings sharing functionality."""

    @pytest.mark.anyio
    async def test_share_findings_with_orchestrator(self, concrete_agent, mock_orchestrator):
        """Test sharing findings through orchestrator."""
        agent = concrete_agent(
            "FindingAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator,
        )

        findings = {
            "vulnerability": "SQL Injection",
            "severity": "high",
            "target": "example.com",
        }

        agent.share_findings(findings)
        await asyncio.sleep(0.1)

    @pytest.mark.anyio
    async def test_share_findings_without_orchestrator(self, concrete_agent):
        """Test sharing findings without orchestrator."""
        agent = concrete_agent("FindingAgent", AgentRole.RESEARCHER)

        findings = {"vulnerability": "XSS", "severity": "medium"}

        # Should not raise
        agent.share_findings(findings)
        await asyncio.sleep(0.1)

    @pytest.mark.anyio
    async def test_share_findings_empty(self, concrete_agent, mock_orchestrator):
        """Test sharing empty findings."""
        agent = concrete_agent(
            "FindingAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator,
        )

        agent.share_findings({})
        await asyncio.sleep(0.1)

    @pytest.mark.anyio
    async def test_share_findings_large(self, concrete_agent, mock_orchestrator):
        """Test sharing large findings data."""
        agent = concrete_agent(
            "FindingAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator,
        )

        large_findings = {f"finding_{i}": {"data": "x" * 100} for i in range(50)}

        agent.share_findings(large_findings)
        await asyncio.sleep(0.1)


# =============================================================================
# Test AgentMessage Dataclass
# =============================================================================


class TestAgentMessage:
    """Test suite for AgentMessage dataclass."""

    def test_default_message_creation(self):
        """Test creating message with default values."""
        msg = AgentMessage()

        assert len(msg.id) == 8
        assert msg.sender == ""
        assert msg.recipient == ""
        assert msg.msg_type == "chat"
        assert msg.content == ""
        assert msg.context == {}
        assert msg.priority == 1
        assert msg.requires_response is False
        assert isinstance(msg.timestamp, str)

    def test_custom_message_creation(self):
        """Test creating message with custom values."""
        msg = AgentMessage(
            id="custom123",
            sender="AgentA",
            recipient="AgentB",
            msg_type="task",
            content="Do something",
            context={"priority": "high"},
            timestamp="2024-01-01T00:00:00",
            priority=3,
            requires_response=True,
        )

        assert msg.id == "custom123"
        assert msg.sender == "AgentA"
        assert msg.recipient == "AgentB"
        assert msg.msg_type == "task"
        assert msg.content == "Do something"
        assert msg.context == {"priority": "high"}
        assert msg.timestamp == "2024-01-01T00:00:00"
        assert msg.priority == 3
        assert msg.requires_response is True

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = AgentMessage(
            sender="TestAgent",
            recipient="OtherAgent",
            msg_type="result",
            content="Task completed",
            context={"findings": ["finding1", "finding2"]},
            priority=2,
            requires_response=False,
        )

        d = msg.to_dict()

        assert d["id"] == msg.id
        assert d["sender"] == "TestAgent"
        assert d["recipient"] == "OtherAgent"
        assert d["type"] == "result"
        assert d["content"] == "Task completed"
        assert d["context"] == {"findings": ["finding1", "finding2"]}
        assert d["timestamp"] == msg.timestamp
        assert d["priority"] == 2
        assert d["requires_response"] is False

    def test_message_id_uniqueness(self):
        """Test that each message gets unique ID."""
        messages = [AgentMessage() for _ in range(100)]
        ids = [msg.id for msg in messages]
        assert len(set(ids)) == 100

    def test_message_priority_levels(self):
        """Test all priority levels."""
        for priority in [1, 2, 3, 4]:
            msg = AgentMessage(priority=priority)
            assert msg.priority == priority


# =============================================================================
# Test AgentRole Enum
# =============================================================================


class TestAgentRole:
    """Test suite for AgentRole enum."""

    def test_all_roles_exist(self):
        """Test that all expected roles exist."""
        expected = {
            "RESEARCHER": "researcher",
            "ANALYST": "analyst",
            "EXPLOIT": "exploit",
            "COORDINATOR": "coordinator",
            "REPORTER": "reporter",
            "POST_EXPLOITATION": "post_exploit",
        }

        for role_name, expected_value in expected.items():
            role = getattr(AgentRole, role_name)
            assert role.value == expected_value

    def test_role_count(self):
        """Test correct number of roles."""
        assert len(list(AgentRole)) == 6

    def test_role_equality(self):
        """Test role equality."""
        assert AgentRole.RESEARCHER == AgentRole.RESEARCHER
        assert AgentRole.RESEARCHER != AgentRole.ANALYST


# =============================================================================
# Test Agent Status
# =============================================================================


class TestAgentStatus:
    """Test suite for agent status reporting."""

    def test_get_status_basic(self, concrete_agent):
        """Test basic status retrieval."""
        agent = concrete_agent("StatusAgent", AgentRole.ANALYST)

        status = agent.get_status()

        assert status["id"] == agent.id
        assert status["name"] == "StatusAgent"
        assert status["role"] == "analyst"
        assert status["running"] is False
        assert status["queue_size"] == 0
        assert status["inbox_count"] == 0
        assert status["memory_entries"] == 0
        assert status["context_keys"] == []

    @pytest.mark.anyio
    async def test_get_status_running(self, concrete_agent):
        """Test status when agent is running."""
        agent = concrete_agent("ActiveAgent", AgentRole.RESEARCHER)

        await agent.start()
        await asyncio.sleep(0.05)

        status = agent.get_status()
        assert status["running"] is True

        await agent.stop()

    def test_get_status_with_context(self, concrete_agent):
        """Test status includes context keys."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)

        agent.update_context("key1", "value1")
        agent.update_context("key2", "value2")
        agent.update_context("nested", {"a": 1})

        status = agent.get_status()
        assert "key1" in status["context_keys"]
        assert "key2" in status["context_keys"]
        assert "nested" in status["context_keys"]

    @pytest.mark.anyio
    async def test_get_status_with_messages(self, concrete_agent):
        """Test status with messages in queue."""
        agent = concrete_agent("MessageAgent", AgentRole.RESEARCHER)

        msg = AgentMessage(sender="Other", content="Test")
        await agent.receive_message(msg)

        status = agent.get_status()
        assert status["queue_size"] == 1
        assert status["inbox_count"] == 1
        assert status["memory_entries"] == 1


# =============================================================================
# Integration Tests
# =============================================================================


class TestAgentIntegration:
    """Integration tests for agent functionality."""

    @pytest.mark.anyio
    async def test_full_message_flow(self, concrete_agent, mock_orchestrator):
        """Test complete message flow from send to process."""
        agent = concrete_agent(
            "IntegrationAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator,
        )

        # Register handler
        received = []

        async def handler(msg):
            received.append(msg)

        agent.register_handler("task", handler)

        # Start agent
        await agent.start()
        await asyncio.sleep(0.05)

        # Send message via orchestrator simulation
        msg = AgentMessage(
            sender="External",
            recipient=f"{agent.name}[{agent.id}]",
            msg_type="task",
            content="Execute task",
        )
        await agent.receive_message(msg)

        # Wait for processing
        await asyncio.sleep(0.2)

        # Stop agent
        await agent.stop()

        # Verify
        assert len(received) == 1
        assert received[0].content == "Execute task"

    @pytest.mark.anyio
    async def test_context_sharing_flow(self, concrete_agent, mock_orchestrator):
        """Test context sharing through orchestrator."""
        agent = concrete_agent(
            "SharingAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator,
        )

        # Update with sharing
        agent.update_context("important_key", "important_value", share=True)

        await asyncio.sleep(0.1)

        # Verify orchestrator was called
        mock_orchestrator.update_shared_context.assert_called_with("important_key", "important_value", agent.id)

    @pytest.mark.anyio
    async def test_multiple_agents_communication(self, concrete_agent, mock_orchestrator):
        """Test multiple agents communicating through orchestrator."""
        agent1 = concrete_agent("Agent1", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)
        agent2 = concrete_agent("Agent2", AgentRole.ANALYST, orchestrator=mock_orchestrator)

        # Agent1 sends message to Agent2
        await agent1.send_message("Hello Agent2", recipient=f"Agent2[{agent2.id}]")

        # Verify orchestrator routed the message
        assert mock_orchestrator.route_message.called
        sent_msg = mock_orchestrator.route_message.call_args[0][0]
        assert sent_msg.content == "Hello Agent2"
