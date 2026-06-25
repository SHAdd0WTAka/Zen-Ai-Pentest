"""Smoke tests for agent_comm/ package (models, email_chain)"""

from datetime import datetime, timezone

import pytest

from agent_comm.email_chain import AgentChain, AgentChainOrchestrator, AgentEmailNode, AgentHandlers
from agent_comm.email_chain import AgentMessage as EmailAgentMessage
from agent_comm.models import AgentMessage, MessageContent, MessageContext, MessageTemplates, MessageType, PriorityLevel


class TestMessageContent:
    def test_empty(self):
        mc = MessageContent()
        assert mc.reasoning is None

    def test_with_confidence(self):
        mc = MessageContent(confidence=0.85)
        assert mc.confidence == 0.85

    def test_invalid_confidence(self):
        with pytest.raises(ValueError):
            MessageContent(confidence=1.5)


class TestMessageContext:
    def test_minimal(self):
        ctx = MessageContext(target="example.com", session_id="sess_001")
        assert ctx.safety_level == "non_destructive"

    def test_with_risk(self):
        ctx = MessageContext(target="10.0.0.1", session_id="sess_002", risk_score=7.5)
        assert ctx.risk_score == 7.5


class TestAgentMessage:
    def test_minimal_message(self):
        msg = AgentMessage(
            message_id="msg_test_001",
            agent_id="bot-1",
            session_id="sess_001",
            type=MessageType.REASON,
            content=MessageContent(reasoning="analyzing"),
            targets=["orchestrator"],
            context=MessageContext(target="example.com", session_id="sess_001"),
        )
        assert msg.version == "1.1"
        assert msg.is_high_priority() is False

    def test_high_priority(self):
        msg = AgentMessage(
            message_id="msg_critical_001",
            agent_id="bot-1",
            session_id="sess_001",
            type=MessageType.ACT,
            priority=PriorityLevel.CRITICAL,
            content=MessageContent(action="nmap", parameters={"target": "10.0.0.1"}),
            targets=["scanner"],
            context=MessageContext(target="10.0.0.1", session_id="sess_001"),
        )
        assert msg.is_high_priority() is True

    def test_expired_message(self):
        old_ts = datetime(2020, 1, 1, tzinfo=timezone.utc)
        msg = AgentMessage(
            message_id="msg_old_12345678",
            agent_id="bot-1",
            session_id="sess_001",
            type=MessageType.STATUS_UPDATE,
            timestamp=old_ts,
            content=MessageContent(observation="status ok"),
            targets=["orchestrator"],
            context=MessageContext(target="example.com", session_id="sess_001"),
            ttl_seconds=1,
        )
        assert msg.is_expired() is True

    def test_validation_act_requires_action(self):
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg_bad_001",
                agent_id="bot-1",
                session_id="sess_001",
                type=MessageType.ACT,
                content=MessageContent(),
                targets=["orchestrator"],
                context=MessageContext(target="example.com", session_id="sess_001"),
            )


class TestPriorityLevel:
    def test_values(self):
        assert PriorityLevel.CRITICAL == 0
        assert PriorityLevel.BACKGROUND == 4


class TestMessageTemplates:
    def test_create_delegate_task(self):
        msg = MessageTemplates.create_delegate_task(
            agent_id="scanner-1",
            session_id="sess_001",
            task_description="Scan target",
            assignee="nmap-agent",
            target="10.0.0.1",
        )
        assert msg.type == MessageType.DELEGATE_TASK
        assert msg.content.task_description == "Scan target"

    def test_create_status_update(self):
        msg = MessageTemplates.create_status_update(
            agent_id="scanner-1",
            session_id="sess_001",
            status="50% complete",
            progress_percent=50,
            target="10.0.0.1",
        )
        assert msg.type == MessageType.STATUS_UPDATE
        assert msg.content.result == {"progress": 50}


class TestEmailAgentMessage:
    def test_create(self):
        msg = EmailAgentMessage.create(
            sender="a@test.local",
            recipient="b@test.local",
            message_type="task",
            payload={"target": "example.com"},
        )
        assert msg.sender == "a@test.local"
        assert msg.chain_position == 0

    def test_encode_decode(self):
        original = EmailAgentMessage.create(
            sender="a@test.local",
            recipient="b@test.local",
            message_type="task",
            payload={"target": "example.com"},
        )
        encoded = original.encode()
        decoded = EmailAgentMessage.decode(encoded)
        assert decoded.sender == original.sender
        assert decoded.payload == original.payload

    def test_add_history_entry(self):
        msg = EmailAgentMessage.create(
            sender="a@test.local",
            recipient="b@test.local",
            message_type="task",
            payload={},
        )
        msg.add_history_entry("agent-1", "scan_started")
        assert len(msg.history) == 1
        assert msg.history[0]["agent"] == "agent-1"


class TestAgentEmailNode:
    def test_init(self):
        node = AgentEmailNode(email="scanner@test.local", role="scanner")
        assert node.email == "scanner@test.local"
        assert node.role == "scanner"


class TestAgentChain:
    def test_min_agents(self):
        node_a = AgentEmailNode(email="a@test.local", role="a")
        node_b = AgentEmailNode(email="b@test.local", role="b")
        chain = AgentChain([node_a, node_b])
        assert chain.total_agents == 2

    def test_too_few_agents(self):
        node = AgentEmailNode(email="a@test.local", role="a")
        with pytest.raises(ValueError, match="at least 2"):
            AgentChain([node])

    def test_is_last_agent(self):
        node_a = AgentEmailNode(email="a@test.local", role="a")
        node_b = AgentEmailNode(email="b@test.local", role="b")
        chain = AgentChain([node_a, node_b])
        assert chain.is_last_agent("b@test.local") is True
        assert chain.is_last_agent("a@test.local") is False


class TestAgentHandlers:
    def test_scan_handler(self):
        msg = EmailAgentMessage.create(
            sender="orchestrator", recipient="scanner", message_type="task", payload={"target": "example.com"}
        )
        result = AgentHandlers.scan_handler(msg)
        assert "target" in result
        assert "findings" in result

    def test_report_handler(self):
        msg = EmailAgentMessage.create(
            sender="analyzer", recipient="reporter", message_type="result", payload={"findings": []}
        )
        result = AgentHandlers.report_handler(msg)
        assert result["report_generated"] is True


class TestAgentChainOrchestrator:
    def test_create_scan_chain(self):
        chain = AgentChainOrchestrator.create_scan_chain()
        assert chain.total_agents == 3
        assert chain.agents[0].role == "scanner"

    def test_create_recon_chain(self):
        chain = AgentChainOrchestrator.create_recon_chain()
        assert chain.total_agents == 3
        assert chain.agents[0].role == "subfinder"
