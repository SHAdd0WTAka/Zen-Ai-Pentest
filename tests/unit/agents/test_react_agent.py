import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.agent_base import AgentMessage, AgentRole, AgentState, BaseAgent


class ConcreteAgent(BaseAgent):
    async def execute_task(self, task: dict) -> dict:
        return {"task": task, "status": "completed", "agent": self.name}


@pytest.fixture
def agent():
    return ConcreteAgent("TestAgent", AgentRole.RESEARCHER)


@pytest.fixture
def mock_orchestrator():
    m = AsyncMock()
    m.route_message = AsyncMock()
    m.update_shared_context = AsyncMock()
    return m


class TestAgentInitialization:
    def test_init_with_defaults(self):
        agent = ConcreteAgent("DefaultAgent")
        assert agent.name == "DefaultAgent"
        assert agent.role == AgentRole.RESEARCHER
        assert len(agent.id) == 8
        assert agent.orchestrator is None
        assert isinstance(agent.message_queue, asyncio.Queue)
        assert agent.state == AgentState.IDLE
        assert agent.running is False

    def test_init_with_orchestrator(self, mock_orchestrator):
        agent = ConcreteAgent("OrchAgent", AgentRole.ANALYST, orchestrator=mock_orchestrator)
        assert agent.orchestrator is mock_orchestrator

    def test_init_all_roles(self):
        for role in AgentRole:
            agent = ConcreteAgent(f"Agent_{role.value}", role)
            assert agent.role == role

    def test_unique_ids(self):
        ids = {ConcreteAgent(f"A{i}").id for i in range(50)}
        assert len(ids) == 50


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_receive_message_adds_to_inbox(self, agent):
        msg = AgentMessage(sender="other", content="hello")
        await agent.receive_message(msg)
        assert len(agent.inbox) == 1
        assert agent.inbox[0].content == "hello"

    @pytest.mark.asyncio
    async def test_receive_message_stores_in_memory(self, agent):
        msg = AgentMessage(sender="other", content="hello")
        await agent.receive_message(msg)
        assert len(agent.memory) == 1
        assert agent.memory[0]["type"] == "received"
        assert agent.memory[0]["processed"] is False

    @pytest.mark.asyncio
    async def test_handle_message_default_chat(self, agent):
        msg = AgentMessage(sender="other", content="ping", msg_type="chat")
        await agent.handle_message(msg)
        assert len(agent.memory) >= 1

    @pytest.mark.asyncio
    async def test_handle_message_chat_requires_response(self, agent):
        msg = AgentMessage(sender="other", content="ping", msg_type="chat", requires_response=True)
        with patch.object(agent, "send_message", new=AsyncMock()) as mock_send:
            await agent.handle_message(msg)
            mock_send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_messages_uses_handler(self, agent):
        handler = AsyncMock()
        agent.register_handler("custom_type", handler)
        msg = AgentMessage(sender="other", content="data", msg_type="custom_type")
        await agent.receive_message(msg)
        await agent.start()
        await asyncio.sleep(0.15)
        await agent.stop()
        handler.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_handler_error_does_not_crash(self, agent):
        async def failing_handler(msg):
            raise ValueError("oops")

        agent.register_handler("broken", failing_handler)
        msg = AgentMessage(sender="other", content="data", msg_type="broken")
        await agent.receive_message(msg)
        await agent.start()
        await asyncio.sleep(0.15)
        await agent.stop()

    @pytest.mark.asyncio
    async def test_memory_marked_processed(self, agent):
        msg = AgentMessage(sender="other", content="hello")
        await agent.receive_message(msg)
        await agent.start()
        await asyncio.sleep(0.15)
        await agent.stop()
        assert agent.memory[0]["processed"] is True


class TestToolUse:
    @pytest.mark.asyncio
    async def test_execute_task_returns_result(self, agent):
        result = await agent.execute_task({"type": "scan", "target": "10.0.0.1"})
        assert result["status"] == "completed"
        assert result["task"]["type"] == "scan"

    @pytest.mark.asyncio
    async def test_send_message_sends_via_orchestrator(self, mock_orchestrator):
        agent = ConcreteAgent("OrchAgent", orchestrator=mock_orchestrator)
        msg_id = await agent.send_message("hello", recipient="other", msg_type="task")
        mock_orchestrator.route_message.assert_awaited_once()
        assert msg_id is not None

    @pytest.mark.asyncio
    async def test_send_message_without_orchestrator(self, agent):
        msg_id = await agent.send_message("hello", recipient="other", msg_type="task")
        assert msg_id is not None

    @pytest.mark.asyncio
    async def test_send_message_sets_priority(self, agent):
        msg_id = await agent.send_message("urgent", priority=4)
        assert msg_id is not None


class TestErrorRecovery:
    @pytest.mark.asyncio
    async def test_execute_task_not_implemented_raises(self):
        class MissingImpl(BaseAgent):
            pass

        agent = MissingImpl("BadAgent")
        with pytest.raises(NotImplementedError):
            await agent.execute_task({"task": "test"})

    @pytest.mark.asyncio
    async def test_process_messages_error_logged(self, agent):
        async def failing_handler(msg):
            raise RuntimeError("handler failure")

        agent.register_handler("fail", failing_handler)
        msg = AgentMessage(sender="other", content="x", msg_type="fail")
        await agent.receive_message(msg)
        await agent.start()
        await asyncio.sleep(0.15)
        await agent.stop()

    @pytest.mark.asyncio
    async def test_stop_without_start(self, agent):
        await agent.stop()
        assert agent.running is False

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, agent):
        await agent.start()
        await asyncio.sleep(0.05)
        assert agent.running is True
        await agent.stop()
        assert agent.running is False

    @pytest.mark.asyncio
    async def test_stop_cancelled_error_handled(self, agent):
        await agent.start()
        await asyncio.sleep(0.05)
        await agent.stop()


class TestConversationHistory:
    def test_memory_stores_interactions(self, agent):
        agent.memory.append({"type": "received", "message": {"id": "1"}, "processed": False})
        agent.memory.append({"type": "shared", "findings": {"port": 80}})
        assert len(agent.memory) == 2

    @pytest.mark.asyncio
    async def test_share_findings_adds_to_memory(self, agent):
        agent.share_findings({"port": 80, "service": "http"})
        assert len(agent.memory) == 1
        assert agent.memory[0]["type"] == "shared"

    def test_get_status_includes_memory_count(self, agent):
        agent.memory.append({"type": "received", "message": {"id": "1"}, "processed": False})
        status = agent.get_status()
        assert status["memory_entries"] == 1

    def test_get_status_includes_queue_size(self, agent):
        status = agent.get_status()
        assert "queue_size" in status
        assert status["queue_size"] == 0

    def test_get_status_context_keys(self, agent):
        agent.update_context("host", "10.0.0.1")
        agent.update_context("port", 443)
        status = agent.get_status()
        assert "host" in status["context_keys"]
        assert "port" in status["context_keys"]

    @pytest.mark.asyncio
    async def test_send_message_returns_id(self, agent):
        msg_id = await agent.send_message("test")
        assert msg_id is not None
        assert isinstance(msg_id, str)


class TestContextManagement:
    def test_update_context(self, agent):
        agent.update_context("target", "10.0.0.1")
        assert agent.get_context("target") == "10.0.0.1"

    def test_update_context_missing_key(self, agent):
        assert agent.get_context("nonexistent") is None

    def test_update_context_overwrite(self, agent):
        agent.update_context("key", "old")
        agent.update_context("key", "new")
        assert agent.get_context("key") == "new"

    @pytest.mark.asyncio
    async def test_update_context_shared_calls_orchestrator(self, mock_orchestrator):
        agent = ConcreteAgent("Shared", orchestrator=mock_orchestrator)
        agent.update_context("key", "value", share=True)
        await asyncio.sleep(0.1)
        mock_orchestrator.update_shared_context.assert_called_once()

    def test_share_findings(self, agent):
        agent.share_findings({"vuln": "CVE-2024-0001"})
        assert len(agent.memory) == 1


class TestAgentLifecycle:
    @pytest.mark.asyncio
    async def test_start_sets_running(self, agent):
        await agent.start()
        await asyncio.sleep(0.05)
        assert agent.running is True
        assert agent.task is not None
        await agent.stop()

    @pytest.mark.asyncio
    async def test_start_twice(self, agent):
        await agent.start()
        await asyncio.sleep(0.05)
        await agent.start()
        await asyncio.sleep(0.05)
        await agent.stop()

    def test_agent_role_enum_values(self):
        assert AgentRole.RESEARCHER.value == "researcher"
        assert AgentRole.ANALYST.value == "analyst"
        assert AgentRole.COORDINATOR.value == "coordinator"

    def test_agent_state_enum_values(self):
        assert AgentState.IDLE.value == "idle"
        assert AgentState.BUSY.value == "busy"
        assert AgentState.FAILED.value == "failed"


class TestMessageSerialization:
    def test_agent_message_to_dict(self):
        msg = AgentMessage(
            sender="alice",
            recipient="bob",
            msg_type="task",
            content="scan target",
            priority=3,
            requires_response=True,
        )
        d = msg.to_dict()
        assert d["sender"] == "alice"
        assert d["recipient"] == "bob"
        assert d["type"] == "task"
        assert d["content"] == "scan target"
        assert d["priority"] == 3
        assert d["requires_response"] is True

    def test_agent_message_defaults(self):
        msg = AgentMessage()
        assert msg.msg_type == "chat"
        assert msg.priority == 1
        assert msg.requires_response is False
        assert len(msg.id) == 8

    def test_agent_message_timestamp(self):
        msg = AgentMessage()
        assert msg.timestamp is not None
