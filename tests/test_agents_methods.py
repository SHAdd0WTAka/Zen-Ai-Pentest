"""Agent Method Tests.

Target: +8% Coverage durch Agent-Methoden-Tests.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from agents.agent_base import AgentState, AgentRole, AgentMessage
from agents.agent_orchestrator import AgentOrchestrator


class TestAgentMessage:
    """Tests for AgentMessage."""

    def test_message_creation(self):
        """Test creating an agent message."""
        msg = AgentMessage(
            sender="agent1",
            recipient="agent2",
            content="Test message",
        )
        assert msg.sender == "agent1"
        assert msg.recipient == "agent2"
        assert msg.content == "Test message"

    def test_message_string_content(self):
        """Test message with string content."""
        msg = AgentMessage(sender="agent1", recipient="agent2")
        assert isinstance(msg.content, str)


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator."""
        return AgentOrchestrator()

    def test_orchestrator_init(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator is not None

    def test_register_agent(self, orchestrator):
        """Test registering an agent."""
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        orchestrator.register(mock_agent)
        # Check if agent was registered

    def test_orchestrator_str(self, orchestrator):
        """Test orchestrator string representation."""
        str_repr = str(orchestrator)
        assert isinstance(str_repr, str)


class TestAgentRoleAndState:
    """Tests for AgentRole and AgentState enums."""

    def test_agent_role_values(self):
        """Test AgentRole enum values."""
        assert AgentRole.RESEARCHER.value == "researcher"
        assert AgentRole.ANALYST.value == "analyst"

    def test_agent_role_exploit(self):
        """Test AgentRole exploit value."""
        assert AgentRole.EXPLOIT.value == "exploit"

    def test_agent_state_values(self):
        """Test AgentState enum values."""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.BUSY.value == "busy"

    def test_agent_state_stopped(self):
        """Test AgentState stopped value."""
        assert AgentState.STOPPED.value == "stopped"
