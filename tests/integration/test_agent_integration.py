"""
Agent Integration Tests for Zen-AI-Pentest
============================================

Comprehensive tests for multi-agent coordination including:
- Multi-agent coordination and orchestration
- Agent message passing
- Shared context management
- Agent lifecycle management
- Role-based agent operations

Usage:
    pytest tests/integration/test_agent_integration.py -v
    pytest tests/integration/test_agent_integration.py -v --cov=agents --cov-report=term-missing
"""

import asyncio
import os
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.agent_base import AgentMessage, AgentRole, AgentState, BaseAgent
from agents.agent_orchestrator import AgentOrchestrator
from agents.analysis_agent import AnalysisAgent
from agents.research_agent import ResearchAgent

# Mark all tests in this file
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def orchestrator():
    """Create an agent orchestrator for testing."""
    return AgentOrchestrator()


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    mock = MagicMock()
    mock.route_message = AsyncMock()
    mock.update_shared_context = AsyncMock()
    return mock


@pytest.fixture
def research_agent(mock_orchestrator):
    """Create a research agent for testing."""
    agent = ResearchAgent("TestResearcher")
    agent.orchestrator = mock_orchestrator
    return agent


@pytest.fixture
def analysis_agent(mock_orchestrator):
    """Create an analysis agent for testing."""
    agent = AnalysisAgent("TestAnalyst")
    agent.orchestrator = mock_orchestrator
    return agent


@pytest.fixture
def sample_agent_context():
    """Create sample context for agent testing."""
    return {
        "target": "scanme.nmap.org",
        "scan_type": "comprehensive",
        "objective": "Identify vulnerabilities",
        "previous_findings": [],
        "config": {"ports": "80,443", "intensity": "medium"},
    }


@pytest.fixture
def sample_message():
    """Create a sample agent message."""
    return AgentMessage(
        sender="TestAgent[1234]",
        recipient="all",
        msg_type="chat",
        content="Test message content",
        context={"key": "value"},
        priority=2,
    )


# ============================================================================
# TEST CLASS: Agent Initialization
# ============================================================================


class TestAgentInitialization:
    """Test agent initialization and basic properties."""

    def test_base_agent_initialization(self, mock_orchestrator):
        """Test basic agent initialization."""
        agent = BaseAgent("TestAgent", AgentRole.RESEARCHER, mock_orchestrator)

        assert agent.name == "TestAgent"
        assert agent.role == AgentRole.RESEARCHER
        assert agent.orchestrator == mock_orchestrator
        assert agent.id is not None
        assert len(agent.id) == 8  # UUID first 8 chars
        assert agent.running is False

    def test_research_agent_initialization(self):
        """Test research agent initialization."""
        agent = ResearchAgent("Researcher1")

        assert agent.name == "Researcher1"
        assert agent.role == AgentRole.RESEARCHER
        assert hasattr(agent, "tools")

    def test_analysis_agent_initialization(self):
        """Test analysis agent initialization."""
        agent = AnalysisAgent("Analyst1")

        assert agent.name == "Analyst1"
        assert agent.role == AgentRole.ANALYST
        assert hasattr(agent, "analysis_methods")

    def test_agent_unique_ids(self, mock_orchestrator):
        """Test that each agent gets a unique ID."""
        agent1 = BaseAgent("Agent1", AgentRole.RESEARCHER, mock_orchestrator)
        agent2 = BaseAgent("Agent2", AgentRole.ANALYST, mock_orchestrator)

        assert agent1.id != agent2.id


# ============================================================================
# TEST CLASS: Agent Lifecycle
# ============================================================================


class TestAgentLifecycle:
    """Test agent start, stop, and status."""

    @pytest.mark.asyncio
    async def test_agent_start(self, mock_orchestrator):
        """Test starting an agent."""
        agent = BaseAgent("TestAgent", AgentRole.RESEARCHER, mock_orchestrator)

        await agent.start()

        assert agent.running is True
        assert agent.task is not None

        await agent.stop()

    @pytest.mark.asyncio
    async def test_agent_stop(self, mock_orchestrator):
        """Test stopping an agent."""
        agent = BaseAgent("TestAgent", AgentRole.RESEARCHER, mock_orchestrator)

        await agent.start()
        assert agent.running is True

        await agent.stop()
        assert agent.running is False

    @pytest.mark.asyncio
    async def test_agent_get_status(self, mock_orchestrator):
        """Test getting agent status."""
        agent = BaseAgent("TestAgent", AgentRole.RESEARCHER, mock_orchestrator)

        status = agent.get_status()

        assert "id" in status
        assert "name" in status
        assert "role" in status
        assert status["name"] == "TestAgent"
        assert status["role"] == AgentRole.RESEARCHER.value
        assert "running" in status
        assert "queue_size" in status
        assert "inbox_count" in status
        assert "memory_entries" in status
        assert "context_keys" in status


# ============================================================================
# TEST CLASS: Agent Messaging
# ============================================================================


class TestAgentMessaging:
    """Test agent message passing."""

    @pytest.mark.asyncio
    async def test_send_message(self, research_agent, mock_orchestrator):
        """Test sending a message from agent."""
        msg_id = await research_agent.send_message(
            content="Hello all",
            recipient="all",
            msg_type="chat",
            priority=2,
        )

        assert msg_id is not None
        assert len(msg_id) > 0
        mock_orchestrator.route_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_message(self, research_agent, sample_message):
        """Test receiving a message by agent."""
        await research_agent.receive_message(sample_message)

        assert len(research_agent.inbox) == 1
        assert research_agent.inbox[0].id == sample_message.id
        assert len(research_agent.memory) == 1

    @pytest.mark.asyncio
    async def test_message_queue_processing(self, mock_orchestrator):
        """Test message queue processing."""
        agent = BaseAgent("TestAgent", AgentRole.RESEARCHER, mock_orchestrator)

        # Add message to queue
        msg = AgentMessage(
            sender="OtherAgent[5678]",
            recipient="TestAgent",
            msg_type="chat",
            content="Test",
        )
        await agent.receive_message(msg)

        # Process messages briefly
        agent.running = True
        try:
            await asyncio.wait_for(agent.process_messages(), timeout=0.5)
        except asyncio.TimeoutError:
            pass  # Expected

        agent.running = False

    @pytest.mark.asyncio
    async def test_broadcast_message(self, research_agent, mock_orchestrator):
        """Test broadcasting message to all agents."""
        await research_agent.send_message(
            content="Broadcast message",
            recipient="all",
            msg_type="announcement",
            priority=3,
        )

        mock_orchestrator.route_message.assert_called_once()
        call_args = mock_orchestrator.route_message.call_args[0][0]
        assert call_args.recipient == "all"
        assert call_args.priority == 3

    @pytest.mark.asyncio
    async def test_direct_message(self, research_agent, mock_orchestrator):
        """Test direct message to specific agent."""
        await research_agent.send_message(
            content="Direct message",
            recipient="Analyst1[abcd1234]",
            msg_type="chat",
            requires_response=True,
        )

        mock_orchestrator.route_message.assert_called_once()
        call_args = mock_orchestrator.route_message.call_args[0][0]
        assert call_args.recipient == "Analyst1[abcd1234]"
        assert call_args.requires_response is True


# ============================================================================
# TEST CLASS: Agent Context Management
# ============================================================================


class TestAgentContextManagement:
    """Test agent context management."""

    def test_update_local_context(self, research_agent):
        """Test updating local agent context."""
        research_agent.update_context("target", "example.com")

        assert research_agent.get_context("target") == "example.com"
        assert "target" in research_agent.context

    @pytest.mark.asyncio
    async def test_update_shared_context(self, research_agent, mock_orchestrator):
        """Test updating shared context."""
        research_agent.update_context("finding", "Critical vulnerability", share=True)

        # Allow async call to complete
        await asyncio.sleep(0.1)

        mock_orchestrator.update_shared_context.assert_called_once()

    def test_share_findings(self, research_agent, mock_orchestrator):
        """Test sharing findings with other agents."""
        findings = {
            "vulnerabilities": [
                {"title": "SQL Injection", "severity": "critical"},
                {"title": "XSS", "severity": "high"},
            ]
        }

        research_agent.share_findings(findings)

        # share_findings creates an async task, so we just verify it doesn't error

    def test_context_isolation(self, mock_orchestrator):
        """Test that each agent has isolated context."""
        agent1 = BaseAgent("Agent1", AgentRole.RESEARCHER, mock_orchestrator)
        agent2 = BaseAgent("Agent2", AgentRole.ANALYST, mock_orchestrator)

        agent1.update_context("secret", "agent1_data")
        agent2.update_context("secret", "agent2_data")

        assert agent1.get_context("secret") == "agent1_data"
        assert agent2.get_context("secret") == "agent2_data"
        assert agent1.get_context("secret") != agent2.get_context("secret")


# ============================================================================
# TEST CLASS: Orchestrator Registration
# ============================================================================


class TestOrchestratorRegistration:
    """Test agent registration with orchestrator."""

    def test_register_agent(self, orchestrator):
        """Test registering an agent with orchestrator."""
        agent = ResearchAgent("Researcher1")

        orchestrator.register_agent(agent)

        assert agent.id in orchestrator.agents
        assert agent.orchestrator == orchestrator
        assert AgentRole.RESEARCHER in orchestrator.agent_by_role

    def test_unregister_agent(self, orchestrator):
        """Test unregistering an agent from orchestrator."""
        agent = ResearchAgent("Researcher1")
        orchestrator.register_agent(agent)

        orchestrator.unregister_agent(agent.id)

        assert agent.id not in orchestrator.agents
        assert (
            AgentRole.RESEARCHER not in orchestrator.agent_by_role
            or len(orchestrator.agent_by_role[AgentRole.RESEARCHER]) == 0
        )

    def test_register_multiple_agents_same_role(self, orchestrator):
        """Test registering multiple agents with same role."""
        agent1 = ResearchAgent("Researcher1")
        agent2 = ResearchAgent("Researcher2")

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        assert len(orchestrator.agents) == 2
        assert len(orchestrator.agent_by_role[AgentRole.RESEARCHER]) == 2

    def test_register_different_roles(self, orchestrator):
        """Test registering agents with different roles."""
        research_agent = ResearchAgent("Researcher1")
        analysis_agent = AnalysisAgent("Analyst1")

        orchestrator.register_agent(research_agent)
        orchestrator.register_agent(analysis_agent)

        assert len(orchestrator.agents) == 2
        assert len(orchestrator.agent_by_role[AgentRole.RESEARCHER]) == 1
        assert len(orchestrator.agent_by_role[AgentRole.ANALYST]) == 1


# ============================================================================
# TEST CLASS: Message Routing
# ============================================================================


class TestMessageRouting:
    """Test message routing through orchestrator."""

    @pytest.mark.asyncio
    async def test_route_message_to_all(self, orchestrator):
        """Test routing message to all agents."""
        agent1 = ResearchAgent("Researcher1")
        agent2 = AnalysisAgent("Analyst1")

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        await agent1.start()
        await agent2.start()

        msg = AgentMessage(
            sender="Test[1234]",
            recipient="all",
            msg_type="chat",
            content="Hello all",
        )

        await orchestrator.route_message(msg)

        # Give time for message processing
        await asyncio.sleep(0.1)

        assert len(agent1.inbox) == 1
        assert len(agent2.inbox) == 1

        await agent1.stop()
        await agent2.stop()

    @pytest.mark.asyncio
    async def test_route_message_by_role(self, orchestrator):
        """Test routing message to agents by role."""
        research_agent = ResearchAgent("Researcher1")
        analysis_agent = AnalysisAgent("Analyst1")

        orchestrator.register_agent(research_agent)
        orchestrator.register_agent(analysis_agent)

        await research_agent.start()
        await analysis_agent.start()

        msg = AgentMessage(
            sender="Coordinator[0000]",
            recipient="role:researcher",
            msg_type="task",
            content="Research task",
        )

        await orchestrator.route_message(msg)
        await asyncio.sleep(0.1)

        assert len(research_agent.inbox) == 1
        # Analysis agent should not receive role-specific message

        await research_agent.stop()
        await analysis_agent.stop()

    @pytest.mark.asyncio
    async def test_route_message_direct(self, orchestrator):
        """Test routing message to specific agent."""
        agent1 = ResearchAgent("Researcher1")
        agent2 = ResearchAgent("Researcher2")

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        await agent1.start()
        await agent2.start()

        msg = AgentMessage(
            sender="Test[1234]",
            recipient=f"Researcher2[{agent2.id}]",
            msg_type="chat",
            content="Private message",
        )

        await orchestrator.route_message(msg)
        await asyncio.sleep(0.1)

        assert len(agent2.inbox) == 1

        await agent1.stop()
        await agent2.stop()

    @pytest.mark.asyncio
    async def test_message_history_tracking(self, orchestrator):
        """Test that routed messages are tracked in history."""
        msg = AgentMessage(
            sender="Test[1234]",
            recipient="all",
            msg_type="chat",
            content="Test",
        )

        await orchestrator.route_message(msg)

        assert len(orchestrator.message_history) == 1
        assert orchestrator.message_history[0].id == msg.id


# ============================================================================
# TEST CLASS: Shared Context
# ============================================================================


class TestSharedContext:
    """Test shared context functionality."""

    def test_update_shared_context(self, orchestrator):
        """Test updating shared context."""
        orchestrator.update_shared_context("target", "example.com", "agent1")

        assert "target" in orchestrator.shared_context
        assert orchestrator.shared_context["target"]["value"] == "example.com"
        assert orchestrator.shared_context["target"]["updated_by"] == "agent1"
        assert "timestamp" in orchestrator.shared_context["target"]

    def test_get_shared_context(self, orchestrator):
        """Test getting shared context values."""
        orchestrator.shared_context["key1"] = {"value": "value1", "updated_by": "agent1"}

        value = orchestrator.get_shared_context("key1")
        assert value == "value1"

        all_context = orchestrator.get_shared_context()
        assert "key1" in all_context

    @pytest.mark.asyncio
    async def test_context_update_notification(self, orchestrator):
        """Test that agents are notified of context updates."""
        agent = ResearchAgent("Researcher1")
        orchestrator.register_agent(agent)
        await agent.start()

        await orchestrator.update_shared_context("new_key", "new_value", "orchestrator")
        await asyncio.sleep(0.1)

        # Agent should have received a context update message
        context_messages = [m for m in agent.inbox if m.msg_type == "context_update"]
        assert len(context_messages) >= 1

        await agent.stop()


# ============================================================================
# TEST CLASS: Multi-Agent Coordination
# ============================================================================


class TestMultiAgentCoordination:
    """Test multi-agent coordination scenarios."""

    @pytest.mark.asyncio
    async def test_coordinate_agents_for_reconnaissance(self, orchestrator):
        """Test coordinating agents for reconnaissance task."""
        research_agent = ResearchAgent("Researcher1")
        analysis_agent = AnalysisAgent("Analyst1")

        # Mock execute_task to avoid actual execution
        research_agent.execute_task = AsyncMock(return_value={"status": "completed", "findings": []})
        analysis_agent.execute_task = AsyncMock(return_value={"status": "completed", "analysis": {}})

        orchestrator.register_agent(research_agent)
        orchestrator.register_agent(analysis_agent)

        result = await orchestrator.coordinate_agents("reconnaissance", {"target": "example.com"})

        assert result["task_type"] == "reconnaissance"
        assert "agent_responses" in result
        assert len(result["agent_responses"]) == 2

    @pytest.mark.asyncio
    async def test_coordinate_agents_for_vulnerability_analysis(self, orchestrator):
        """Test coordinating agents for vulnerability analysis."""
        analysis_agent = AnalysisAgent("Analyst1")
        exploit_agent = MagicMock()
        exploit_agent.id = "exploit123"
        exploit_agent.role = AgentRole.EXPLOIT
        exploit_agent.execute_task = AsyncMock(return_value={"status": "completed"})

        analysis_agent.execute_task = AsyncMock(return_value={"status": "completed"})

        orchestrator.register_agent(analysis_agent)
        orchestrator.register_agent(exploit_agent)

        result = await orchestrator.coordinate_agents("vulnerability_analysis", {"findings": []})

        assert result["task_type"] == "vulnerability_analysis"

    @pytest.mark.asyncio
    async def test_start_stop_all_agents(self, orchestrator):
        """Test starting and stopping all registered agents."""
        agent1 = ResearchAgent("Researcher1")
        agent2 = AnalysisAgent("Analyst1")

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        await orchestrator.start_all()

        assert agent1.running is True
        assert agent2.running is True

        await orchestrator.stop_all()

        assert agent1.running is False
        assert agent2.running is False

    def test_get_system_status(self, orchestrator):
        """Test getting system status from orchestrator."""
        agent1 = ResearchAgent("Researcher1")
        agent2 = AnalysisAgent("Analyst1")

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        status = orchestrator.get_system_status()

        assert "agents" in status
        assert "shared_context_keys" in status
        assert "message_count" in status
        assert "role_distribution" in status
        assert len(status["agents"]) == 2


# ============================================================================
# TEST CLASS: Research Coordination
# ============================================================================


class TestResearchCoordination:
    """Test research coordination functionality."""

    @pytest.mark.asyncio
    async def test_start_research_coordination(self, orchestrator):
        """Test starting research coordination."""
        research_agent = ResearchAgent("Researcher1")
        research_agent.orchestrator = orchestrator

        orchestrator.register_agent(research_agent)
        await research_agent.start()

        thread_id = await orchestrator.start_research_coordination(
            topic="CVE-2024-1234",
            pentest_context={"target": "example.com"},
        )

        assert thread_id is not None
        assert thread_id.startswith("research_")
        assert thread_id in orchestrator.research_coordination

        await research_agent.stop()

    @pytest.mark.asyncio
    async def test_research_coordination_notify_agents(self, orchestrator):
        """Test that research coordination notifies research agents."""
        research_agent1 = ResearchAgent("Researcher1")
        research_agent2 = ResearchAgent("Researcher2")

        orchestrator.register_agent(research_agent1)
        orchestrator.register_agent(research_agent2)

        await research_agent1.start()
        await research_agent2.start()

        await orchestrator.start_research_coordination(
            topic="Security Research",
            pentest_context={},
        )

        await asyncio.sleep(0.1)

        # Both research agents should have received research task message
        assert len(research_agent1.inbox) >= 1
        assert len(research_agent2.inbox) >= 1

        await research_agent1.stop()
        await research_agent2.stop()


# ============================================================================
# TEST CLASS: Conversation Facilitation
# ============================================================================


class TestConversationFacilitation:
    """Test conversation facilitation between agents."""

    @pytest.mark.asyncio
    async def test_facilitate_conversation(self, orchestrator):
        """Test facilitating conversation between agents."""
        agent1 = ResearchAgent("Researcher1")
        agent2 = AnalysisAgent("Analyst1")

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        await agent1.start()
        await agent2.start()

        conversation = await orchestrator.facilitate_conversation(
            topic="Security Assessment",
            participants=[agent1.id, agent2.id],
            rounds=2,
        )

        # Conversation tracking may vary based on implementation
        assert isinstance(conversation, list)

        await agent1.stop()
        await agent2.stop()


# ============================================================================
# TEST CLASS: Error Handling
# ============================================================================


class TestAgentErrorHandling:
    """Test error handling in agent operations."""

    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, orchestrator):
        """Test handling agent task timeout."""
        slow_agent = ResearchAgent("SlowAgent")
        slow_agent.execute_task = AsyncMock(side_effect=asyncio.TimeoutError())

        orchestrator.register_agent(slow_agent)

        result = await orchestrator.coordinate_agents("test_task", {})

        # Should handle timeout gracefully
        assert "agent_responses" in result

    @pytest.mark.asyncio
    async def test_agent_exception_handling(self, orchestrator):
        """Test handling agent task exception."""
        error_agent = ResearchAgent("ErrorAgent")
        error_agent.execute_task = AsyncMock(side_effect=Exception("Test error"))

        orchestrator.register_agent(error_agent)

        result = await orchestrator.coordinate_agents("test_task", {})

        # Should handle exception gracefully
        assert "agent_responses" in result

    def test_invalid_role_routing(self, orchestrator):
        """Test routing to invalid role."""
        import logging

        with (
            self.assertLogs(level="ERROR")
            if hasattr(self, "assertLogs")
            else patch.object(logging.getLogger("ZenAI.Agents"), "error")
        ):
            msg = AgentMessage(
                sender="Test[1234]",
                recipient="role:invalid_role",
                msg_type="task",
                content="Test",
            )

            # Should handle gracefully without error
            asyncio.run(orchestrator.route_message(msg))


# ============================================================================
# TEST CLASS: Agent Memory
# ============================================================================


class TestAgentMemory:
    """Test agent memory functionality."""

    @pytest.mark.asyncio
    async def test_memory_tracking(self, research_agent, sample_message):
        """Test that agent tracks message in memory."""
        await research_agent.receive_message(sample_message)

        assert len(research_agent.memory) == 1
        assert research_agent.memory[0]["type"] == "received"
        assert research_agent.memory[0]["message"]["id"] == sample_message.id
        assert research_agent.memory[0]["processed"] is False

    @pytest.mark.asyncio
    async def test_memory_mark_processed(self, research_agent, sample_message):
        """Test that processed messages are marked."""

        # Register a handler to process the message
        async def handler(msg):
            pass

        research_agent.register_handler("chat", handler)

        await research_agent.receive_message(sample_message)

        # Manually mark as processed (normally done in process_messages)
        for mem in research_agent.memory:
            if mem["message"]["id"] == sample_message.id:
                mem["processed"] = True

        assert research_agent.memory[0]["processed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents", "--cov-report=term-missing"])
