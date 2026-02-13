"""
Tests for Agent Communication Protocol (ACP) Models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_comm.models import (
    AgentMessage,
    MessageContent,
    MessageContext,
    MessageType,
    PriorityLevel,
    MessageTemplates,
    MessageResponse
)


class TestMessageContent:
    """Test MessageContent model"""
    
    def test_valid_content(self):
        """Test creating valid MessageContent"""
        content = MessageContent(
            reasoning="Test reasoning",
            action="nmap_scan",
            confidence=0.85
        )
        assert content.reasoning == "Test reasoning"
        assert content.action == "nmap_scan"
        assert content.confidence == 0.85
    
    def test_confidence_validation(self):
        """Test confidence must be between 0 and 1"""
        # Valid values
        MessageContent(confidence=0.0)
        MessageContent(confidence=1.0)
        MessageContent(confidence=0.5)
        
        # Invalid values
        with pytest.raises(ValidationError):
            MessageContent(confidence=1.5)
        
        with pytest.raises(ValidationError):
            MessageContent(confidence=-0.1)
    
    def test_delegate_task_content(self):
        """Test content for delegate_task type"""
        content = MessageContent(
            task_description="Enumerate subdomains",
            assignee="recon-bot-1",
            due_in_seconds=1800,
            parameters={"target": "example.com"}
        )
        assert content.task_description == "Enumerate subdomains"
        assert content.assignee == "recon-bot-1"
        assert content.due_in_seconds == 1800


class TestMessageContext:
    """Test MessageContext model"""
    
    def test_valid_context(self):
        """Test creating valid MessageContext"""
        context = MessageContext(
            target="192.168.1.1",
            session_id="scan_123",
            risk_score=7.5,
            safety_level="medium_risk"
        )
        assert context.target == "192.168.1.1"
        assert context.session_id == "scan_123"
        assert context.risk_score == 7.5
        assert context.safety_level == "medium_risk"
    
    def test_risk_score_validation(self):
        """Test risk_score must be between 0 and 10"""
        # Valid
        MessageContext(target="test", session_id="123", risk_score=0)
        MessageContext(target="test", session_id="123", risk_score=10)
        
        # Invalid
        with pytest.raises(ValidationError):
            MessageContext(target="test", session_id="123", risk_score=11)
        
        with pytest.raises(ValidationError):
            MessageContext(target="test", session_id="123", risk_score=-1)
    
    def test_safety_level_validation(self):
        """Test safety_level must be valid enum"""
        # Valid
        MessageContext(target="test", session_id="123", safety_level="non_destructive")
        MessageContext(target="test", session_id="123", safety_level="high_risk")
        
        # Invalid
        with pytest.raises(ValidationError):
            MessageContext(target="test", session_id="123", safety_level="invalid_level")


class TestAgentMessage:
    """Test AgentMessage model"""
    
    def test_valid_message(self):
        """Test creating valid AgentMessage"""
        msg = AgentMessage(
            message_id="msg_abc12345",
            agent_id="test-agent-1",
            session_id="scan_123",
            type=MessageType.OBSERVE,
            content=MessageContent(observation="Port 80 open"),
            targets=["orchestrator"],
            context=MessageContext(target="192.168.1.1", session_id="scan_123")
        )
        assert msg.message_id == "msg_abc12345"
        assert msg.version == "1.1"
        assert msg.agent_id == "test-agent-1"
        assert msg.type == "observe"
    
    def test_message_id_validation(self):
        """Test message_id must match pattern"""
        # Valid
        AgentMessage(
            message_id="msg_abc12345",
            agent_id="test",
            session_id="123",
            type="observe",
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="test", session_id="123")
        )
        
        # Invalid - wrong prefix
        with pytest.raises(ValidationError):
            AgentMessage(
                message_id="invalid_abc123",
                agent_id="test",
                session_id="123",
                type="observe",
                content=MessageContent(),
                targets=["target"],
                context=MessageContext(target="test", session_id="123")
            )
    
    def test_targets_validation(self):
        """Test targets must not be empty"""
        with pytest.raises(ValidationError):
            AgentMessage(
                message_id="msg_abc12345",
                agent_id="test",
                session_id="123",
                type="observe",
                content=MessageContent(),
                targets=[],  # Empty - should fail
                context=MessageContext(target="test", session_id="123")
            )
    
    def test_act_message_requires_action(self):
        """Test that 'act' messages require action field"""
        # Missing action - should fail
        with pytest.raises(ValidationError):
            AgentMessage(
                message_id="msg_abc12345",
                agent_id="test",
                session_id="123",
                type=MessageType.ACT,
                content=MessageContent(),  # No action
                targets=["target"],
                context=MessageContext(target="test", session_id="123")
            )
        
        # With action - should pass
        AgentMessage(
            message_id="msg_abc12345",
            agent_id="test",
            session_id="123",
            type=MessageType.ACT,
            content=MessageContent(action="nmap_scan"),
            targets=["target"],
            context=MessageContext(target="test", session_id="123")
        )
    
    def test_delegate_task_requires_description(self):
        """Test that 'delegate_task' messages require task_description"""
        with pytest.raises(ValidationError):
            AgentMessage(
                message_id="msg_abc12345",
                agent_id="test",
                session_id="123",
                type=MessageType.DELEGATE_TASK,
                content=MessageContent(),  # No task_description
                targets=["target"],
                context=MessageContext(target="test", session_id="123")
            )
    
    def test_is_high_priority(self):
        """Test is_high_priority method"""
        # Critical priority (0)
        msg_critical = AgentMessage(
            message_id="msg_abc12345",
            agent_id="test",
            session_id="123",
            type="observe",
            priority=PriorityLevel.CRITICAL,
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="test", session_id="123")
        )
        assert msg_critical.is_high_priority() is True
        
        # Normal priority (2)
        msg_normal = AgentMessage(
            message_id="msg_abc12346",
            agent_id="test",
            session_id="123",
            type="observe",
            priority=PriorityLevel.NORMAL,
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="test", session_id="123")
        )
        assert msg_normal.is_high_priority() is False
    
    def test_is_expired(self):
        """Test is_expired method"""
        # Message with very short TTL
        msg = AgentMessage(
            message_id="msg_abc12345",
            agent_id="test",
            session_id="123",
            type="observe",
            ttl_seconds=1,
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="test", session_id="123")
        )
        
        # Should not be expired immediately
        assert msg.is_expired() is False
        
        # Message without TTL should not expire
        msg_no_ttl = AgentMessage(
            message_id="msg_abc12346",
            agent_id="test",
            session_id="123",
            type="observe",
            ttl_seconds=None,
            content=MessageContent(),
            targets=["target"],
            context=MessageContext(target="test", session_id="123")
        )
        assert msg_no_ttl.is_expired() is False


class TestMessageTemplates:
    """Test MessageTemplates helper class"""
    
    def test_create_delegate_task(self):
        """Test create_delegate_task template"""
        msg = MessageTemplates.create_delegate_task(
            agent_id="analysis-bot-1",
            session_id="scan_123",
            task_description="Enumerate subdomains",
            assignee="recon-bot-2",
            target="example.com",
            priority=PriorityLevel.HIGH,
            due_in_seconds=1800
        )
        
        assert msg.agent_id == "analysis-bot-1"
        assert msg.session_id == "scan_123"
        assert msg.type == MessageType.DELEGATE_TASK
        assert msg.content.task_description == "Enumerate subdomains"
        assert msg.content.assignee == "recon-bot-2"
        assert msg.content.due_in_seconds == 1800
        assert msg.priority == PriorityLevel.HIGH
    
    def test_create_status_update(self):
        """Test create_status_update template"""
        msg = MessageTemplates.create_status_update(
            agent_id="recon-bot-1",
            session_id="scan_123",
            status="Scanning ports 80-443",
            progress_percent=50,
            target="example.com"
        )
        
        assert msg.agent_id == "recon-bot-1"
        assert msg.type == MessageType.STATUS_UPDATE
        assert msg.content.observation == "Scanning ports 80-443"
        assert msg.content.result == {"progress": 50}
        assert msg.targets == ["orchestrator"]


class TestMessageResponse:
    """Test MessageResponse model"""
    
    def test_success_response(self):
        """Test successful response"""
        response = MessageResponse(
            success=True,
            message_id="msg_abc12345"
        )
        assert response.success is True
        assert response.message_id == "msg_abc12345"
        assert response.error is None
    
    def test_error_response(self):
        """Test error response"""
        response = MessageResponse(
            success=False,
            error="Validation failed"
        )
        assert response.success is False
        assert response.error == "Validation failed"
        assert response.message_id is None


class TestSerialization:
    """Test serialization/deserialization"""
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        msg = AgentMessage(
            message_id="msg_abc12345",
            agent_id="test-agent",
            session_id="scan_123",
            type="observe",
            content=MessageContent(observation="Test"),
            targets=["orchestrator"],
            context=MessageContext(target="test", session_id="scan_123")
        )
        
        data = msg.model_dump()
        assert data["message_id"] == "msg_abc12345"
        assert data["agent_id"] == "test-agent"
        assert data["type"] == "observe"
        assert data["content"]["observation"] == "Test"
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "message_id": "msg_abc12345",
            "agent_id": "test-agent",
            "session_id": "scan_123",
            "type": "observe",
            "content": {"observation": "Port 80 open"},
            "targets": ["orchestrator"],
            "context": {"target": "192.168.1.1", "session_id": "scan_123", "safety_level": "non_destructive"}
        }
        
        msg = AgentMessage.model_validate(data)
        assert msg.message_id == "msg_abc12345"
        assert msg.content.observation == "Port 80 open"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
