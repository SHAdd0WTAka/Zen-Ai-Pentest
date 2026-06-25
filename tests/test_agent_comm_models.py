"""
Tests for agent_comm/models.py
Target: 85%+ Coverage
"""

from datetime import datetime, timedelta

import pytest


class TestMessageType:
    """Test MessageType constants"""

    def test_message_types(self):
        """Test all message type constants"""
        from agent_comm.models import MessageType

        assert MessageType.REASON == "reason"
        assert MessageType.ACT == "act"
        assert MessageType.OBSERVE == "observe"
        assert MessageType.REFLECT == "reflect"
        assert MessageType.DELEGATE == "delegate"
        assert MessageType.DELEGATE_TASK == "delegate_task"
        assert MessageType.ERROR == "error"
        assert MessageType.COMPLETE == "complete"
        assert MessageType.STATUS_UPDATE == "status_update"
        assert MessageType.CANCEL == "cancel"


class TestPriorityLevel:
    """Test PriorityLevel constants"""

    def test_priority_levels(self):
        """Test all priority level constants"""
        from agent_comm.models import PriorityLevel

        assert PriorityLevel.CRITICAL == 0
        assert PriorityLevel.HIGH == 1
        assert PriorityLevel.NORMAL == 2
        assert PriorityLevel.LOW == 3
        assert PriorityLevel.BACKGROUND == 4


class TestMessageContent:
    """Test MessageContent model"""

    def test_default_creation(self):
        """Test creating MessageContent with defaults"""
        from agent_comm.models import MessageContent

        content = MessageContent()
        assert content.reasoning is None
        assert content.action is None
        assert content.parameters is None
        assert content.confidence is None

    def test_confidence_validation(self):
        """Test confidence field validation"""
        from agent_comm.models import MessageContent

        # Valid confidence
        content = MessageContent(confidence=0.8)
        assert content.confidence == 0.8

        # Boundary values
        MessageContent(confidence=0.0)
        MessageContent(confidence=1.0)

    def test_confidence_out_of_range(self):
        """Test confidence out of range raises error"""
        from agent_comm.models import MessageContent

        with pytest.raises(ValueError):
            MessageContent(confidence=1.5)

        with pytest.raises(ValueError):
            MessageContent(confidence=-0.1)

    def test_extra_fields_allowed(self):
        """Test extra fields are allowed"""
        from agent_comm.models import MessageContent

        content = MessageContent(custom_field="custom_value")
        assert content.custom_field == "custom_value"


class TestMessageContext:
    """Test MessageContext model"""

    def test_valid_context(self):
        """Test creating valid MessageContext"""
        from agent_comm.models import MessageContext

        context = MessageContext(
            target="api.target.com", session_id="scan_123", risk_score=5.5
        )

        assert context.target == "api.target.com"
        assert context.session_id == "scan_123"
        assert context.risk_score == 5.5
        assert context.safety_level == "non_destructive"

    def test_risk_score_validation(self):
        """Test risk score validation"""
        from agent_comm.models import MessageContext

        # Valid scores
        MessageContext(target="t", session_id="s", risk_score=0.0)
        MessageContext(target="t", session_id="s", risk_score=10.0)

        # Invalid scores
        with pytest.raises(ValueError):
            MessageContext(target="t", session_id="s", risk_score=11.0)

        with pytest.raises(ValueError):
            MessageContext(target="t", session_id="s", risk_score=-1.0)


class TestAgentMessage:
    """Test AgentMessage model"""

    def test_valid_message(self):
        """Test creating valid AgentMessage"""
        from agent_comm.models import (
            AgentMessage,
            MessageContent,
            MessageContext,
            MessageType,
        )

        message = AgentMessage(
            message_id="msg_test12345678",
            agent_id="test-agent",
            session_id="session_123",
            type=MessageType.REASON,
            content=MessageContent(reasoning="Test reasoning"),
            targets=["orchestrator"],
            context=MessageContext(
                target="target.com", session_id="session_123"
            ),
        )

        assert message.message_id == "msg_test12345678"
        assert message.version == "1.1"
        assert message.type == "reason"

    def test_message_id_pattern(self):
        """Test message_id pattern validation"""
        from agent_comm.models import (
            AgentMessage,
            MessageContent,
            MessageContext,
        )

        # Valid IDs
        AgentMessage(
            message_id="msg_abc123456789",
            agent_id="agent",
            session_id="session",
            type="reason",
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="t", session_id="s"),
        )

        # Invalid ID (wrong prefix)
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="invalid_id",
                agent_id="agent",
                session_id="session",
                type="reason",
                content=MessageContent(),
                targets=["target"],
                context=MessageContext(target="t", session_id="s"),
            )

    def test_priority_validation(self):
        """Test priority validation"""
        from agent_comm.models import (
            AgentMessage,
            MessageContent,
            MessageContext,
            PriorityLevel,
        )

        # Valid priorities
        AgentMessage(
            message_id="msg_test12345678",
            agent_id="agent",
            session_id="session",
            type="reason",
            priority=PriorityLevel.CRITICAL,
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="t", session_id="s"),
        )

        # Invalid priority
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg_test12345678",
                agent_id="agent",
                session_id="session",
                type="reason",
                priority=5,
                content=MessageContent(),
                targets=["target"],
                context=MessageContext(target="t", session_id="s"),
            )

    def test_targets_validation(self):
        """Test targets validation"""
        from agent_comm.models import (
            AgentMessage,
            MessageContent,
            MessageContext,
        )

        # Empty targets should fail
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg_test12345678",
                agent_id="agent",
                session_id="session",
                type="reason",
                content=MessageContent(),
                targets=[],
                context=MessageContext(target="t", session_id="s"),
            )

    def test_content_validation_act(self):
        """Test content validation for ACT messages"""
        from agent_comm.models import (
            AgentMessage,
            MessageContent,
            MessageContext,
            MessageType,
        )

        # ACT without action should fail
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg_test12345678",
                agent_id="agent",
                session_id="session",
                type=MessageType.ACT,
                content=MessageContent(),  # No action
                targets=["target"],
                context=MessageContext(target="t", session_id="s"),
            )

        # ACT with action should succeed
        AgentMessage(
            message_id="msg_test12345679",
            agent_id="agent",
            session_id="session",
            type=MessageType.ACT,
            content=MessageContent(action="scan"),
            targets=["target"],
            context=MessageContext(target="t", session_id="s"),
        )

    def test_is_high_priority(self):
        """Test is_high_priority method"""
        from agent_comm.models import (
            AgentMessage,
            MessageContent,
            MessageContext,
            PriorityLevel,
        )

        critical = AgentMessage(
            message_id="msg_test12345678",
            agent_id="agent",
            session_id="session",
            type="reason",
            priority=PriorityLevel.CRITICAL,
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="t", session_id="s"),
        )
        assert critical.is_high_priority() is True

        normal = AgentMessage(
            message_id="msg_test12345679",
            agent_id="agent",
            session_id="session",
            type="reason",
            priority=PriorityLevel.NORMAL,
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="t", session_id="s"),
        )
        assert normal.is_high_priority() is False

    def test_is_expired(self):
        """Test is_expired method"""
        from agent_comm.models import (
            AgentMessage,
            MessageContent,
            MessageContext,
        )

        # Message with short TTL
        message = AgentMessage(
            message_id="msg_test12345678",
            agent_id="agent",
            session_id="session",
            type="reason",
            ttl_seconds=1,
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="t", session_id="s"),
        )

        # Not expired yet
        assert message.is_expired() is False


class TestMessageResponse:
    """Test MessageResponse model"""

    def test_success_response(self):
        """Test successful response"""
        from agent_comm.models import MessageResponse

        response = MessageResponse(success=True, message_id="msg_123")
        assert response.success is True
        assert response.message_id == "msg_123"
        assert response.error is None

    def test_error_response(self):
        """Test error response"""
        from agent_comm.models import MessageResponse

        response = MessageResponse(success=False, error="Something went wrong")
        assert response.success is False
        assert response.error == "Something went wrong"


class TestMessageTemplates:
    """Test MessageTemplates class"""

    def test_create_delegate_task(self):
        """Test create_delegate_task template"""
        from agent_comm.models import (
            MessageTemplates,
            MessageType,
            PriorityLevel,
        )

        message = MessageTemplates.create_delegate_task(
            agent_id="agent-1",
            session_id="session-123",
            task_description="Perform scan",
            assignee="recon-bot",
            target="target.com",
        )

        assert message.type == MessageType.DELEGATE_TASK
        assert message.agent_id == "agent-1"
        assert message.content.task_description == "Perform scan"
        assert message.content.assignee == "recon-bot"
        assert message.priority == PriorityLevel.NORMAL

    def test_create_delegate_task_with_list_assignees(self):
        """Test create_delegate_task with multiple assignees"""
        from agent_comm.models import MessageTemplates

        message = MessageTemplates.create_delegate_task(
            agent_id="agent-1",
            session_id="session-123",
            task_description="Perform scan",
            assignee=["bot-1", "bot-2"],
            target="target.com",
        )

        assert message.targets == ["bot-1", "bot-2"]

    def test_create_status_update(self):
        """Test create_status_update template"""
        from agent_comm.models import MessageTemplates, MessageType

        message = MessageTemplates.create_status_update(
            agent_id="agent-1",
            session_id="session-123",
            status="Scanning ports",
            progress_percent=50,
            target="target.com",
        )

        assert message.type == MessageType.STATUS_UPDATE
        assert message.content.observation == "Scanning ports"
        assert message.content.result["progress"] == 50
        assert "orchestrator" in message.targets
