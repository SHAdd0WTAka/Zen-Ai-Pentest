"""
Comprehensive tests for agents/agent_base.py module
Tests BaseAgent class initialization, state management, message handling, 
configuration management, and tool execution.

Target: 80%+ coverage of agent_base.py
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

from agents.agent_base import (
    AgentRole,
    AgentState,
    AgentMessage,
    BaseAgent,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def concrete_agent():
    """Fixture to create a concrete agent implementation for testing."""
    class ConcreteAgent(BaseAgent):
        async def execute_task(self, task: dict) -> dict:
            return {"task": task, "status": "completed", "agent": self.name}
    
    return ConcreteAgent


@pytest.fixture
def mock_orchestrator():
    """Fixture to create a mock orchestrator."""
    mock = AsyncMock()
    mock.route_message = AsyncMock()
    mock.update_shared_context = AsyncMock()
    return mock


@pytest.fixture
def sample_message():
    """Fixture to create a sample message."""
    return AgentMessage(
        id="msg123",
        sender="TestSender",
        recipient="TestRecipient",
        msg_type="chat",
        content="Test message content",
        context={"key": "value"},
        timestamp=datetime.now().isoformat(),
        priority=2,
        requires_response=False,
    )


# ============================================================================
# Test BaseAgent Class Initialization
# ============================================================================

class TestBaseAgentInitialization:
    """Test BaseAgent class initialization with various configurations."""

    def test_basic_initialization(self, concrete_agent):
        """Test basic agent initialization with minimal parameters."""
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
        """Test initialization with orchestrator."""
        agent = concrete_agent(
            "OrchestratedAgent",
            AgentRole.ANALYST,
            orchestrator=mock_orchestrator
        )
        
        assert agent.orchestrator is mock_orchestrator
        assert agent.name == "OrchestratedAgent"
        assert agent.role == AgentRole.ANALYST

    def test_initialization_all_roles(self, concrete_agent):
        """Test initialization with all available roles."""
        roles_agents = {
            AgentRole.RESEARCHER: "ResearchAgent",
            AgentRole.ANALYST: "AnalystAgent",
            AgentRole.EXPLOIT: "ExploitAgent",
            AgentRole.COORDINATOR: "CoordinatorAgent",
            AgentRole.REPORTER: "ReporterAgent",
            AgentRole.POST_EXPLOITATION: "PostExploitAgent",
        }
        
        for role, name in roles_agents.items():
            agent = concrete_agent(name, role)
            assert agent.role == role
            assert agent.name == name
            assert len(agent.id) == 8

    def test_agent_id_uniqueness(self, concrete_agent):
        """Test that each agent gets a unique ID."""
        agents = [concrete_agent(f"Agent{i}", AgentRole.RESEARCHER) for i in range(100)]
        ids = [agent.id for agent in agents]
        assert len(set(ids)) == 100  # All IDs should be unique

    def test_initialization_with_special_characters(self, concrete_agent):
        """Test initialization with special characters in name."""
        special_names = [
            "Agent-With-Dashes",
            "Agent_With_Underscores",
            "Agent.With.Dots",
            "Agent With Spaces",
            "Agent@With@Special#Chars!",
            "",
            "A" * 1000,  # Very long name
        ]
        
        for name in special_names:
            agent = concrete_agent(name, AgentRole.RESEARCHER)
            assert agent.name == name

    @patch("agents.agent_base.logger")
    def test_initialization_logs_info(self, mock_logger, concrete_agent):
        """Test that initialization logs appropriate message."""
        agent = concrete_agent("LoggedAgent", AgentRole.RESEARCHER)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "LoggedAgent" in log_message
        assert "researcher" in log_message
        assert agent.id in log_message


# ============================================================================
# Test Agent State Management
# ============================================================================

class TestAgentStateManagement:
    """Test agent state management including lifecycle states."""

    @pytest.mark.anyio
    async def test_state_idle_to_running(self, concrete_agent):
        """Test transition from idle to running state."""
        agent = concrete_agent("StateAgent", AgentRole.RESEARCHER)
        
        assert agent.running is False  # IDLE equivalent
        
        await agent.start()
        await asyncio.sleep(0.05)  # Allow task to start
        
        assert agent.running is True
        
        await agent.stop()
        assert agent.running is False

    @pytest.mark.anyio
    async def test_stop_gracefully_handles_cancelled_error(self, concrete_agent):
        """Test that stop() handles CancelledError gracefully."""
        agent = concrete_agent("StopAgent", AgentRole.RESEARCHER)
        
        await agent.start()
        await asyncio.sleep(0.05)
        
        # Stop should not raise
        await agent.stop()
        assert agent.running is False

    @pytest.mark.anyio
    async def test_stop_without_start(self, concrete_agent):
        """Test stopping an agent that was never started."""
        agent = concrete_agent("UnstartedAgent", AgentRole.RESEARCHER)
        
        assert agent.task is None
        await agent.stop()  # Should not raise
        assert agent.running is False

    @pytest.mark.anyio
    async def test_multiple_start_stop_cycles(self, concrete_agent):
        """Test multiple start/stop cycles."""
        agent = concrete_agent("CycleAgent", AgentRole.RESEARCHER)
        
        for i in range(3):
            await agent.start()
            await asyncio.sleep(0.05)
            assert agent.running is True
            
            await agent.stop()
            assert agent.running is False

    def test_get_status_reflects_state(self, concrete_agent):
        """Test that get_status reflects current agent state."""
        agent = concrete_agent("StatusAgent", AgentRole.ANALYST)
        
        status = agent.get_status()
        assert status["running"] is False
        assert status["name"] == "StatusAgent"
        assert status["role"] == "analyst"
        assert status["queue_size"] == 0
        assert status["inbox_count"] == 0
        assert status["memory_entries"] == 0

    @pytest.mark.anyio
    async def test_get_status_with_active_agent(self, concrete_agent):
        """Test status with actively running agent."""
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
        agent.update_context("nested", {"a": 1, "b": 2})
        
        status = agent.get_status()
        assert "key1" in status["context_keys"]
        assert "key2" in status["context_keys"]
        assert "nested" in status["context_keys"]


# ============================================================================
# Test Message Handling
# ============================================================================

class TestMessageHandling:
    """Test message handling including sending, receiving, and processing."""

    @pytest.mark.anyio
    async def test_send_message_via_orchestrator(self, concrete_agent, mock_orchestrator):
        """Test sending message through orchestrator."""
        agent = concrete_agent(
            "SenderAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        msg_id = await agent.send_message(
            content="Hello World",
            recipient="TargetAgent",
            msg_type="task",
            priority=3,
            requires_response=True,
            context={"task_id": "123"}
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
            orchestrator=mock_orchestrator
        )
        
        await agent.send_message("Broadcast message", recipient="all")
        
        sent_msg = mock_orchestrator.route_message.call_args[0][0]
        assert sent_msg.recipient == "all"

    @pytest.mark.anyio
    async def test_send_message_without_orchestrator(self, concrete_agent):
        """Test sending message without orchestrator (direct queue)."""
        agent = concrete_agent("DirectAgent", AgentRole.RESEARCHER)
        
        await agent.send_message("Direct message")
        
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
        assert agent.memory[0]["message"]["id"] == sample_message.id

    @pytest.mark.anyio
    async def test_receive_multiple_messages(self, concrete_agent):
        """Test receiving multiple messages."""
        agent = concrete_agent("MultiReceiver", AgentRole.RESEARCHER)
        
        messages = [
            AgentMessage(sender=f"Agent{i}", content=f"Message {i}")
            for i in range(10)
        ]
        
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
        
        agent.register_handler("custom_type", custom_handler)
        
        msg = AgentMessage(
            sender="Tester",
            content="Test content",
            msg_type="custom_type"
        )
        await agent.receive_message(msg)
        
        # Process messages briefly
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
        assert received_msg.content == "Test content"

    @pytest.mark.anyio
    async def test_message_processing_marks_memory_processed(self, concrete_agent):
        """Test that processed messages are marked in memory."""
        agent = concrete_agent("MemoryAgent", AgentRole.RESEARCHER)
        
        async def handler(msg):
            pass
        
        agent.register_handler("test", handler)
        
        msg = AgentMessage(sender="Tester", content="Test", msg_type="test")
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
        
        # Check memory was updated
        assert agent.memory[0]["processed"] is True

    @pytest.mark.anyio
    async def test_default_handle_message_chat(self, concrete_agent):
        """Test default message handler for chat messages."""
        agent = concrete_agent("Handler", AgentRole.RESEARCHER)
        agent.orchestrator = AsyncMock()
        
        msg = AgentMessage(
            sender="OtherAgent",
            content="Hello there!",
            msg_type="chat",
            requires_response=True
        )
        
        await agent.handle_message(msg)
        
        # Should send acknowledgment response
        agent.orchestrator.route_message.assert_called_once()
        response_msg = agent.orchestrator.route_message.call_args[0][0]
        assert response_msg.msg_type == "response"
        assert "Acknowledged" in response_msg.content
        assert "OtherAgent" in response_msg.recipient

    @pytest.mark.anyio
    async def test_default_handle_message_no_response(self, concrete_agent):
        """Test default handler doesn't respond when not required."""
        agent = concrete_agent("Handler", AgentRole.RESEARCHER)
        agent.orchestrator = AsyncMock()
        
        msg = AgentMessage(
            sender="OtherAgent",
            content="Hello",
            msg_type="chat",
            requires_response=False
        )
        
        await agent.handle_message(msg)
        
        agent.orchestrator.route_message.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_message_non_chat(self, concrete_agent):
        """Test default handler with non-chat message type."""
        agent = concrete_agent("Handler", AgentRole.RESEARCHER)
        
        msg = AgentMessage(
            sender="OtherAgent",
            content="Some data",
            msg_type="data"
        )
        
        # Should not raise, just log
        await agent.handle_message(msg)

    @pytest.mark.anyio
    async def test_process_messages_timeout_handling(self, concrete_agent):
        """Test that process_messages handles timeout correctly."""
        agent = concrete_agent("TimeoutAgent", AgentRole.RESEARCHER)
        
        agent.running = True
        task = asyncio.create_task(agent.process_messages())
        
        # Let it run through a few timeout cycles
        await asyncio.sleep(2.2)
        
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
        
        msg = AgentMessage(sender="Tester", content="Test", msg_type="fail")
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

    @patch("agents.agent_base.logger")
    @pytest.mark.anyio
    async def test_send_message_logs_debug(self, mock_logger, concrete_agent, mock_orchestrator):
        """Test that sending message logs debug information."""
        agent = concrete_agent("Logger", AgentRole.RESEARCHER, orchestrator=mock_orchestrator)
        
        await agent.send_message("Test", recipient="Other", msg_type="task")
        
        mock_logger.debug.assert_called_once()
        log_msg = mock_logger.debug.call_args[0][0]
        assert "task" in log_msg
        assert "Other" in log_msg


# ============================================================================
# Test Configuration Management
# ============================================================================

class TestConfigurationManagement:
    """Test configuration management including context operations."""

    def test_update_context_basic(self, concrete_agent):
        """Test basic context update."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)
        
        agent.update_context("key", "value")
        assert agent.context["key"] == "value"

    def test_update_context_multiple(self, concrete_agent):
        """Test updating multiple context values."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)
        
        agent.update_context("string_key", "string_value")
        agent.update_context("int_key", 42)
        agent.update_context("float_key", 3.14)
        agent.update_context("bool_key", True)
        agent.update_context("list_key", [1, 2, 3])
        agent.update_context("dict_key", {"nested": "value"})
        agent.update_context("none_key", None)
        
        assert agent.context["string_key"] == "string_value"
        assert agent.context["int_key"] == 42
        assert agent.context["float_key"] == 3.14
        assert agent.context["bool_key"] is True
        assert agent.context["list_key"] == [1, 2, 3]
        assert agent.context["dict_key"] == {"nested": "value"}
        assert agent.context["none_key"] is None

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
        
        agent.update_context("existing_key", "existing_value")
        assert agent.get_context("existing_key") == "existing_value"

    def test_get_context_nonexistent(self, concrete_agent):
        """Test getting non-existent context key returns None."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)
        
        result = agent.get_context("nonexistent_key")
        assert result is None

    def test_get_context_after_overwrite(self, concrete_agent):
        """Test getting context after value overwrite."""
        agent = concrete_agent("ContextAgent", AgentRole.RESEARCHER)
        
        agent.update_context("key", "first")
        assert agent.get_context("key") == "first"
        
        agent.update_context("key", "second")
        assert agent.get_context("key") == "second"

    @pytest.mark.anyio
    async def test_update_context_with_share(self, concrete_agent, mock_orchestrator):
        """Test updating context with sharing to orchestrator."""
        agent = concrete_agent(
            "SharingAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        agent.update_context("shared_key", "shared_value", share=True)
        
        # Allow async task to complete
        await asyncio.sleep(0.1)
        
        mock_orchestrator.update_shared_context.assert_called_once_with(
            "shared_key", "shared_value", agent.id
        )
        assert agent.context["shared_key"] == "shared_value"

    def test_update_context_share_without_orchestrator(self, concrete_agent):
        """Test sharing context without orchestrator doesn't fail."""
        agent = concrete_agent("NoOrchestrator", AgentRole.RESEARCHER)
        
        # Should not raise
        agent.update_context("key", "value", share=True)
        assert agent.context["key"] == "value"

    def test_update_context_no_share(self, concrete_agent, mock_orchestrator):
        """Test updating context without sharing doesn't call orchestrator."""
        agent = concrete_agent(
            "LocalAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        agent.update_context("local_key", "local_value", share=False)
        
        mock_orchestrator.update_shared_context.assert_not_called()
        assert agent.context["local_key"] == "local_value"

    def test_context_isolation_between_agents(self, concrete_agent):
        """Test that context is isolated between different agents."""
        agent1 = concrete_agent("Agent1", AgentRole.RESEARCHER)
        agent2 = concrete_agent("Agent2", AgentRole.RESEARCHER)
        
        agent1.update_context("shared_name", "agent1_value")
        agent2.update_context("shared_name", "agent2_value")
        
        assert agent1.get_context("shared_name") == "agent1_value"
        assert agent2.get_context("shared_name") == "agent2_value"


# ============================================================================
# Test Tool Execution
# ============================================================================

class TestToolExecution:
    """Test tool execution capabilities via execute_task method."""

    @pytest.mark.anyio
    async def test_execute_task_implementation(self, concrete_agent):
        """Test that execute_task is properly implemented."""
        agent = concrete_agent("TaskAgent", AgentRole.EXPLOIT)
        
        task = {"type": "scan", "target": "192.168.1.1", "ports": [80, 443]}
        result = await agent.execute_task(task)
        
        assert result["task"] == task
        assert result["status"] == "completed"
        assert result["agent"] == "TaskAgent"

    @pytest.mark.anyio
    async def test_execute_task_with_different_inputs(self, concrete_agent):
        """Test execute_task with various input types."""
        agent = concrete_agent("TaskAgent", AgentRole.EXPLOIT)
        
        # Empty task
        result = await agent.execute_task({})
        assert result["status"] == "completed"
        
        # Complex nested task
        complex_task = {
            "type": "exploit",
            "target": {"host": "example.com", "port": 8080},
            "payload": {"data": "test", "encoding": "base64"},
            "options": {"verbose": True, "timeout": 30}
        }
        result = await agent.execute_task(complex_task)
        assert result["status"] == "completed"
        assert result["task"] == complex_task

    @pytest.mark.anyio
    async def test_execute_task_multiple_calls(self, concrete_agent):
        """Test multiple execute_task calls."""
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

    def test_abstract_baseagent_cannot_instantiate(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseAgent("Test", AgentRole.RESEARCHER)
        
        assert "abstract" in str(exc_info.value).lower() or "execute_task" in str(exc_info.value)

    def test_subclass_must_implement_execute_task(self):
        """Test that subclasses must implement execute_task."""
        class IncompleteAgent(BaseAgent):
            pass
        
        with pytest.raises(TypeError) as exc_info:
            IncompleteAgent("Test", AgentRole.RESEARCHER)
        
        assert "abstract" in str(exc_info.value).lower() or "execute_task" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_custom_execute_task_implementation(self):
        """Test custom execute_task implementation."""
        class CustomAgent(BaseAgent):
            async def execute_task(self, task: dict) -> dict:
                return {
                    "agent_id": self.id,
                    "agent_name": self.name,
                    "task_type": task.get("type"),
                    "result": "custom_result",
                    "timestamp": datetime.now().isoformat()
                }
        
        agent = CustomAgent("Custom", AgentRole.ANALYST)
        task = {"type": "custom_task", "data": "test"}
        
        result = await agent.execute_task(task)
        
        assert result["agent_id"] == agent.id
        assert result["agent_name"] == "Custom"
        assert result["task_type"] == "custom_task"
        assert result["result"] == "custom_result"
        assert "timestamp" in result


# ============================================================================
# Test Handler Registration
# ============================================================================

class TestHandlerRegistration:
    """Test handler registration functionality."""

    def test_register_single_handler(self, concrete_agent):
        """Test registering a single handler."""
        agent = concrete_agent("HandlerAgent", AgentRole.RESEARCHER)
        
        def handler(msg):
            pass
        
        agent.register_handler("custom_event", handler)
        
        assert "custom_event" in agent.handlers
        assert agent.handlers["custom_event"] == handler

    def test_register_multiple_handlers(self, concrete_agent):
        """Test registering multiple handlers."""
        agent = concrete_agent("HandlerAgent", AgentRole.RESEARCHER)
        
        def handler1(msg):
            pass
        
        def handler2(msg):
            pass
        
        def handler3(msg):
            pass
        
        agent.register_handler("event1", handler1)
        agent.register_handler("event2", handler2)
        agent.register_handler("event3", handler3)
        
        assert len(agent.handlers) == 3
        assert agent.handlers["event1"] == handler1
        assert agent.handlers["event2"] == handler2
        assert agent.handlers["event3"] == handler3

    def test_register_handler_overwrite(self, concrete_agent):
        """Test that registering handler overwrites existing."""
        agent = concrete_agent("HandlerAgent", AgentRole.RESEARCHER)
        
        def original_handler(msg):
            return "original"
        
        def new_handler(msg):
            return "new"
        
        agent.register_handler("event", original_handler)
        assert agent.handlers["event"] == original_handler
        
        agent.register_handler("event", new_handler)
        assert agent.handlers["event"] == new_handler

    def test_register_async_handler(self, concrete_agent):
        """Test registering async handler."""
        agent = concrete_agent("HandlerAgent", AgentRole.RESEARCHER)
        
        async def async_handler(msg):
            await asyncio.sleep(0.01)
            return "async_result"
        
        agent.register_handler("async_event", async_handler)
        
        assert "async_event" in agent.handlers
        assert agent.handlers["async_event"] == async_handler


# ============================================================================
# Test Findings Sharing
# ============================================================================

class TestFindingsSharing:
    """Test findings sharing functionality."""

    @pytest.mark.anyio
    async def test_share_findings_with_orchestrator(self, concrete_agent, mock_orchestrator):
        """Test sharing findings through orchestrator."""
        agent = concrete_agent(
            "FindingAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        findings = {
            "vulnerability": "SQL Injection",
            "severity": "high",
            "target": "example.com",
            "evidence": "error message revealed database structure"
        }
        
        agent.share_findings(findings)
        await asyncio.sleep(0.1)  # Allow async task

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
            orchestrator=mock_orchestrator
        )
        
        agent.share_findings({})
        await asyncio.sleep(0.1)

    @pytest.mark.anyio
    async def test_share_findings_large(self, concrete_agent, mock_orchestrator):
        """Test sharing large findings data."""
        agent = concrete_agent(
            "FindingAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        large_findings = {f"finding_{i}": {"data": "x" * 100} for i in range(100)}
        
        agent.share_findings(large_findings)
        await asyncio.sleep(0.1)


# ============================================================================
# Test AgentMessage Dataclass
# ============================================================================

class TestAgentMessage:
    """Test AgentMessage dataclass functionality."""

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
            requires_response=True
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
            requires_response=False
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
        priorities = [
            (1, "low"),
            (2, "medium"),
            (3, "high"),
            (4, "critical"),
        ]
        
        for priority, _ in priorities:
            msg = AgentMessage(priority=priority)
            assert msg.priority == priority


# ============================================================================
# Test AgentRole Enum
# ============================================================================

class TestAgentRole:
    """Test AgentRole enum functionality."""

    def test_all_roles_exist(self):
        """Test that all expected roles exist."""
        expected_roles = {
            "RESEARCHER": "researcher",
            "ANALYST": "analyst",
            "EXPLOIT": "exploit",
            "COORDINATOR": "coordinator",
            "REPORTER": "reporter",
            "POST_EXPLOITATION": "post_exploit",
        }
        
        for role_name, expected_value in expected_roles.items():
            role = getattr(AgentRole, role_name)
            assert role.value == expected_value

    def test_role_count(self):
        """Test correct number of roles."""
        assert len(list(AgentRole)) == 6

    def test_role_comparison(self):
        """Test role equality and inequality."""
        assert AgentRole.RESEARCHER == AgentRole.RESEARCHER
        assert AgentRole.RESEARCHER != AgentRole.ANALYST
        assert AgentRole.COORDINATOR != AgentRole.EXPLOIT

    def test_role_value_access(self):
        """Test accessing role values."""
        assert AgentRole.RESEARCHER.value == "researcher"
        assert AgentRole.POST_EXPLOITATION.value == "post_exploit"


# ============================================================================
# Test AgentState Enum
# ============================================================================

class TestAgentState:
    """Test AgentState enum functionality."""

    def test_all_states_exist(self):
        """Test that all expected states exist."""
        expected_states = {
            "IDLE": "idle",
            "BUSY": "busy",
            "WAITING": "waiting",
            "COMPLETED": "completed",
            "FAILED": "failed",
            "STOPPED": "stopped",
        }
        
        for state_name, expected_value in expected_states.items():
            state = getattr(AgentState, state_name)
            assert state.value == expected_value

    def test_state_count(self):
        """Test correct number of states."""
        assert len(list(AgentState)) == 6

    def test_state_values(self):
        """Test state value strings."""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.BUSY.value == "busy"
        assert AgentState.WAITING.value == "waiting"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.FAILED.value == "failed"
        assert AgentState.STOPPED.value == "stopped"


# ============================================================================
# Integration Tests
# ============================================================================

class TestAgentIntegration:
    """Integration tests for agent functionality."""

    @pytest.mark.anyio
    async def test_full_message_flow(self, concrete_agent):
        """Test complete message flow from send to process."""
        agent = concrete_agent("IntegrationAgent", AgentRole.COORDINATOR)
        
        messages_received = []
        
        async def message_handler(msg):
            messages_received.append(msg)
        
        agent.register_handler("test", message_handler)
        
        # Start agent
        await agent.start()
        
        # Send messages to self
        for i in range(5):
            msg = AgentMessage(
                sender=f"IntegrationAgent[{agent.id}]",
                content=f"Message {i}",
                msg_type="test"
            )
            await agent.receive_message(msg)
        
        # Allow processing
        await asyncio.sleep(0.5)
        
        # Stop agent
        await agent.stop()
        
        # Verify messages were processed
        assert len(messages_received) == 5

    @pytest.mark.anyio
    async def test_context_with_orchestrator_share(self, concrete_agent, mock_orchestrator):
        """Test context updates with orchestrator sharing in flow."""
        agent = concrete_agent(
            "ContextFlowAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        # Add local context
        agent.update_context("local_key", "local_value")
        
        # Add shared context
        agent.update_context("shared_key", "shared_value", share=True)
        await asyncio.sleep(0.1)
        
        # Verify local context
        assert agent.get_context("local_key") == "local_value"
        assert agent.get_context("shared_key") == "shared_value"
        
        # Verify orchestrator was called
        mock_orchestrator.update_shared_context.assert_called_once_with(
            "shared_key", "shared_value", agent.id
        )

    @pytest.mark.anyio
    async def test_memory_accumulation(self, concrete_agent):
        """Test memory accumulation over multiple operations."""
        agent = concrete_agent("MemoryAgent", AgentRole.RESEARCHER)
        
        # Receive multiple messages
        for i in range(10):
            msg = AgentMessage(sender=f"Sender{i}", content=f"Content {i}")
            await agent.receive_message(msg)
        
        assert len(agent.memory) == 10
        assert len(agent.inbox) == 10
        
        # Check memory entries
        for i, mem in enumerate(agent.memory):
            assert mem["type"] == "received"
            assert mem["processed"] is False
            assert mem["message"]["sender"] == f"Sender{i}"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_agent_name(self, concrete_agent):
        """Test agent with empty name."""
        agent = concrete_agent("", AgentRole.RESEARCHER)
        assert agent.name == ""

    def test_very_long_agent_name(self, concrete_agent):
        """Test agent with very long name."""
        long_name = "A" * 10000
        agent = concrete_agent(long_name, AgentRole.RESEARCHER)
        assert agent.name == long_name

    @pytest.mark.anyio
    async def test_send_message_with_empty_content(self, concrete_agent, mock_orchestrator):
        """Test sending message with empty content."""
        agent = concrete_agent(
            "EmptyContent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        await agent.send_message("")
        
        sent_msg = mock_orchestrator.route_message.call_args[0][0]
        assert sent_msg.content == ""

    @pytest.mark.anyio
    async def test_send_message_with_none_context(self, concrete_agent, mock_orchestrator):
        """Test sending message with None context (should default to empty dict)."""
        agent = concrete_agent(
            "NoneContext",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        await agent.send_message("Test", context=None)
        
        sent_msg = mock_orchestrator.route_message.call_args[0][0]
        assert sent_msg.context == {}

    def test_context_with_special_characters(self, concrete_agent):
        """Test context with special characters in keys and values."""
        agent = concrete_agent("SpecialAgent", AgentRole.RESEARCHER)
        
        special_data = {
            "key-with-dashes": "value",
            "key_with_underscores": "value",
            "key.with.dots": "value",
            "key with spaces": "value",
            "unicode_key_日本語": "unicode_value_日本語",
            "emoji_key_🚀": "emoji_value_🎉",
        }
        
        for key, value in special_data.items():
            agent.update_context(key, value)
            assert agent.get_context(key) == value

    @pytest.mark.anyio
    async def test_priority_boundaries(self, concrete_agent, mock_orchestrator):
        """Test message priority boundaries."""
        agent = concrete_agent(
            "PriorityAgent",
            AgentRole.RESEARCHER,
            orchestrator=mock_orchestrator
        )
        
        # Test various priority values
        priorities = [-100, -1, 0, 1, 5, 10, 100, 1000]
        
        for priority in priorities:
            await agent.send_message("Test", priority=priority)
        
        assert mock_orchestrator.route_message.call_count == len(priorities)

    @pytest.mark.anyio
    async def test_rapid_start_stop(self, concrete_agent):
        """Test rapid start/stop cycles."""
        agent = concrete_agent("RapidAgent", AgentRole.RESEARCHER)
        
        for _ in range(10):
            await agent.start()
            await asyncio.sleep(0.01)
            await agent.stop()
            await asyncio.sleep(0.01)
        
        assert agent.running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.agent_base", "--cov-report=term-missing"])
