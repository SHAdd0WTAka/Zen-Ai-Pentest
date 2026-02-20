"""
Comprehensive tests for Agent Orchestrator
Tests AgentOrchestrator class with mocked dependencies
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from agents.agent_base import AgentMessage, AgentRole, BaseAgent
from agents.agent_orchestrator import AgentOrchestrator


# Concrete implementation for testing
class MockAgent(BaseAgent):
    """Mock agent for testing"""

    def __init__(self, name, role, orchestrator=None):
        super().__init__(name, role, orchestrator)
        self.execute_task_called = False
        self.last_task = None

    async def execute_task(self, task: dict) -> dict:
        """Mock task execution"""
        self.execute_task_called = True
        self.last_task = task
        return {"status": "success", "agent": self.name, "task_type": task.get("type")}


class TestAgentOrchestratorInitialization:
    """Test AgentOrchestrator initialization"""

    def test_default_initialization(self):
        """Test default initialization"""
        orchestrator = AgentOrchestrator()

        assert orchestrator.agents == {}
        assert orchestrator.agent_by_role == {}
        assert orchestrator.shared_context == {}
        assert orchestrator.message_history == []
        assert orchestrator.conversation_threads == {}
        assert orchestrator.zen_orchestrator is None
        assert orchestrator.running is False
        assert orchestrator.research_coordination == {}

    def test_initialization_with_zen_orchestrator(self):
        """Test initialization with Zen orchestrator"""
        mock_zen = Mock()
        orchestrator = AgentOrchestrator(zen_orchestrator=mock_zen)

        assert orchestrator.zen_orchestrator is mock_zen


class TestAgentOrchestratorRegistration:
    """Test agent registration and unregistration"""

    def test_register_single_agent(self):
        """Test registering a single agent"""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("TestAgent", AgentRole.RESEARCHER)

        orchestrator.register_agent(agent)

        assert agent.id in orchestrator.agents
        assert orchestrator.agents[agent.id] is agent
        assert agent.orchestrator is orchestrator

    def test_register_multiple_agents(self):
        """Test registering multiple agents"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1", AgentRole.RESEARCHER)
        agent2 = MockAgent("Agent2", AgentRole.ANALYST)
        agent3 = MockAgent("Agent3", AgentRole.RESEARCHER)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)

        assert len(orchestrator.agents) == 3
        assert len(orchestrator.agent_by_role[AgentRole.RESEARCHER]) == 2
        assert len(orchestrator.agent_by_role[AgentRole.ANALYST]) == 1

    def test_register_updates_agent_orchestrator(self):
        """Test that registration updates agent's orchestrator reference"""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("TestAgent", AgentRole.RESEARCHER)
        assert agent.orchestrator is None

        orchestrator.register_agent(agent)

        assert agent.orchestrator is orchestrator

    def test_unregister_agent(self):
        """Test unregistering an agent"""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("TestAgent", AgentRole.RESEARCHER)

        orchestrator.register_agent(agent)
        orchestrator.unregister_agent(agent.id)

        assert agent.id not in orchestrator.agents
        assert agent not in orchestrator.agent_by_role[AgentRole.RESEARCHER]

    def test_unregister_nonexistent_agent(self):
        """Test unregistering agent that doesn't exist"""
        orchestrator = AgentOrchestrator()

        # Should not raise
        orchestrator.unregister_agent("nonexistent-id")

    def test_register_same_role_multiple_agents(self):
        """Test registering multiple agents with same role"""
        orchestrator = AgentOrchestrator()

        for i in range(5):
            agent = MockAgent(f"Agent{i}", AgentRole.RESEARCHER)
            orchestrator.register_agent(agent)

        assert len(orchestrator.agent_by_role[AgentRole.RESEARCHER]) == 5


class TestAgentOrchestratorMessageRouting:
    """Test message routing functionality"""

    @pytest.mark.asyncio
    async def test_route_message_broadcast(self):
        """Test broadcasting message to all agents"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1", AgentRole.RESEARCHER)
        agent2 = MockAgent("Agent2", AgentRole.ANALYST)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        msg = AgentMessage(sender="Test[testid]", recipient="all", content="Hello all")
        await orchestrator.route_message(msg)

        assert len(orchestrator.message_history) == 1
        # Both agents should receive the message
        assert agent1.message_queue.qsize() == 1
        assert agent2.message_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_route_message_broadcast_excludes_sender(self):
        """Test broadcast excludes sender"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1", AgentRole.RESEARCHER)

        orchestrator.register_agent(agent1)

        # Message from agent1 to all
        msg = AgentMessage(sender=f"Agent1[{agent1.id}]", recipient="all", content="Hello")
        await orchestrator.route_message(msg)

        # Sender should not receive their own message
        assert agent1.message_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_route_message_by_role(self):
        """Test routing message to specific role"""
        orchestrator = AgentOrchestrator()
        researcher = MockAgent("Researcher", AgentRole.RESEARCHER)
        analyst = MockAgent("Analyst", AgentRole.ANALYST)

        orchestrator.register_agent(researcher)
        orchestrator.register_agent(analyst)

        msg = AgentMessage(sender="Test", recipient="role:researcher", content="For researchers")
        await orchestrator.route_message(msg)

        assert researcher.message_queue.qsize() == 1
        assert analyst.message_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_route_message_direct(self):
        """Test direct message to specific agent"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1", AgentRole.RESEARCHER)
        agent2 = MockAgent("Agent2", AgentRole.RESEARCHER)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        msg = AgentMessage(sender="Test", recipient=f"Agent1[{agent1.id}]", content="Private")
        await orchestrator.route_message(msg)

        assert agent1.message_queue.qsize() == 1
        assert agent2.message_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_route_message_invalid_role(self):
        """Test routing to invalid role"""
        orchestrator = AgentOrchestrator()

        msg = AgentMessage(sender="Test", recipient="role:invalid_role", content="Test")

        # Should not raise
        await orchestrator.route_message(msg)

    @pytest.mark.asyncio
    async def test_route_message_tracks_history(self):
        """Test that routed messages are tracked in history"""
        orchestrator = AgentOrchestrator()

        msg1 = AgentMessage(sender="A", recipient="all", content="M1")
        msg2 = AgentMessage(sender="B", recipient="all", content="M2")

        await orchestrator.route_message(msg1)
        await orchestrator.route_message(msg2)

        assert len(orchestrator.message_history) == 2
        assert orchestrator.message_history[0].content == "M1"
        assert orchestrator.message_history[1].content == "M2"


class TestAgentOrchestratorSharedContext:
    """Test shared context management"""

    @pytest.mark.asyncio
    async def test_update_shared_context(self):
        """Test updating shared context"""
        orchestrator = AgentOrchestrator()

        await orchestrator.update_shared_context("key", "value", "agent1")

        assert "key" in orchestrator.shared_context
        assert orchestrator.shared_context["key"]["value"] == "value"
        assert orchestrator.shared_context["key"]["updated_by"] == "agent1"
        assert "timestamp" in orchestrator.shared_context["key"]

    @pytest.mark.asyncio
    async def test_update_shared_context_notifies_agents(self):
        """Test that context update notifies other agents"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1", AgentRole.RESEARCHER)
        agent2 = MockAgent("Agent2", AgentRole.ANALYST)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        await orchestrator.update_shared_context("key", "value", agent1.id)

        # Agent2 should receive notification
        assert agent2.message_queue.qsize() == 1
        # Agent1 (updater) should not receive notification
        assert agent1.message_queue.qsize() == 0

    def test_get_shared_context_single_key(self):
        """Test getting single context value"""
        orchestrator = AgentOrchestrator()

        # Set context directly
        orchestrator.shared_context["key1"] = {"value": "value1"}

        assert orchestrator.get_shared_context("key1") == "value1"

    def test_get_shared_context_all(self):
        """Test getting all context"""
        orchestrator = AgentOrchestrator()

        orchestrator.shared_context["key1"] = {"value": "value1"}
        orchestrator.shared_context["key2"] = {"value": "value2"}

        all_context = orchestrator.get_shared_context()

        assert "key1" in all_context
        assert "key2" in all_context

    def test_get_shared_context_nonexistent(self):
        """Test getting nonexistent context key"""
        orchestrator = AgentOrchestrator()

        assert orchestrator.get_shared_context("nonexistent") is None


class TestAgentOrchestratorResearchCoordination:
    """Test research coordination functionality"""

    @pytest.mark.asyncio
    async def test_start_research_coordination(self):
        """Test starting research coordination"""
        orchestrator = AgentOrchestrator()
        researcher = MockAgent("Researcher", AgentRole.RESEARCHER)
        orchestrator.register_agent(researcher)

        thread_id = await orchestrator.start_research_coordination("Test Topic", {"target": "example.com"})

        assert thread_id.startswith("research_")
        assert thread_id in orchestrator.research_coordination

        coord = orchestrator.research_coordination[thread_id]
        assert coord["topic"] == "Test Topic"
        assert coord["context"]["target"] == "example.com"
        assert coord["status"] == "active"

    @pytest.mark.asyncio
    async def test_research_coordination_notifies_researchers(self):
        """Test that research coordination notifies researchers"""
        orchestrator = AgentOrchestrator()
        researcher1 = MockAgent("R1", AgentRole.RESEARCHER)
        researcher2 = MockAgent("R2", AgentRole.RESEARCHER)
        analyst = MockAgent("A1", AgentRole.ANALYST)

        orchestrator.register_agent(researcher1)
        orchestrator.register_agent(researcher2)
        orchestrator.register_agent(analyst)

        await orchestrator.start_research_coordination("Topic", {})

        # Only researchers should be notified
        assert researcher1.message_queue.qsize() == 1
        assert researcher2.message_queue.qsize() == 1
        assert analyst.message_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_research_coordination_tracks_agents(self):
        """Test that research coordination tracks involved agents"""
        orchestrator = AgentOrchestrator()
        researcher = MockAgent("R1", AgentRole.RESEARCHER)
        orchestrator.register_agent(researcher)

        thread_id = await orchestrator.start_research_coordination("Topic", {})

        coord = orchestrator.research_coordination[thread_id]
        assert researcher.id in coord["agents_involved"]


class TestAgentOrchestratorCoordination:
    """Test agent coordination for complex tasks"""

    @pytest.mark.asyncio
    async def test_coordinate_agents_reconnaissance(self):
        """Test coordinating reconnaissance task"""
        orchestrator = AgentOrchestrator()
        researcher = MockAgent("R1", AgentRole.RESEARCHER)
        analyst = MockAgent("A1", AgentRole.ANALYST)

        orchestrator.register_agent(researcher)
        orchestrator.register_agent(analyst)

        results = await orchestrator.coordinate_agents("reconnaissance", {"target": "example.com"})

        assert results["task_type"] == "reconnaissance"
        assert "started" in results
        assert "completed" in results
        assert len(results["agent_responses"]) == 2
        assert researcher.execute_task_called is True
        assert analyst.execute_task_called is True

    @pytest.mark.asyncio
    async def test_coordinate_agents_vulnerability_analysis(self):
        """Test coordinating vulnerability analysis task"""
        orchestrator = AgentOrchestrator()
        analyst = MockAgent("A1", AgentRole.ANALYST)
        exploit = MockAgent("E1", AgentRole.EXPLOIT)

        orchestrator.register_agent(analyst)
        orchestrator.register_agent(exploit)

        results = await orchestrator.coordinate_agents("vulnerability_analysis", {"findings": ["CVE-2021-44228"]})

        assert results["task_type"] == "vulnerability_analysis"
        assert analyst.execute_task_called is True
        assert exploit.execute_task_called is True

    @pytest.mark.asyncio
    async def test_coordinate_agents_exploit_development(self):
        """Test coordinating exploit development task"""
        orchestrator = AgentOrchestrator()
        exploit = MockAgent("E1", AgentRole.EXPLOIT)
        analyst = MockAgent("A1", AgentRole.ANALYST)

        orchestrator.register_agent(exploit)
        orchestrator.register_agent(analyst)

        results = await orchestrator.coordinate_agents("exploit_development", {"vulnerability": "CVE-2021-44228"})

        assert results["task_type"] == "exploit_development"
        assert exploit.execute_task_called is True

    @pytest.mark.asyncio
    async def test_coordinate_agents_full_assessment(self):
        """Test coordinating full assessment task"""
        orchestrator = AgentOrchestrator()
        researcher = MockAgent("R1", AgentRole.RESEARCHER)
        analyst = MockAgent("A1", AgentRole.ANALYST)
        exploit = MockAgent("E1", AgentRole.EXPLOIT)

        orchestrator.register_agent(researcher)
        orchestrator.register_agent(analyst)
        orchestrator.register_agent(exploit)

        results = await orchestrator.coordinate_agents("full_assessment", {"target": "example.com"})

        assert results["task_type"] == "full_assessment"
        assert len(results["agent_responses"]) == 3
        assert "shared_findings" in results

    @pytest.mark.asyncio
    async def test_coordinate_agents_unknown_task(self):
        """Test coordinating unknown task type"""
        orchestrator = AgentOrchestrator()

        results = await orchestrator.coordinate_agents("unknown_task", {})

        assert results["task_type"] == "unknown_task"
        assert results["agent_responses"] == {}

    @pytest.mark.asyncio
    async def test_coordinate_agents_timeout(self):
        """Test timeout handling in coordination"""
        orchestrator = AgentOrchestrator()

        # Create agent with slow execution
        class SlowAgent(BaseAgent):
            async def execute_task(self, task):
                await asyncio.sleep(10)  # Will timeout
                return {"status": "done"}

        slow_agent = SlowAgent("Slow", AgentRole.RESEARCHER)
        orchestrator.register_agent(slow_agent)

        # Patch the timeout to be shorter for testing
        with patch.object(asyncio, "wait_for", side_effect=asyncio.TimeoutError):
            await orchestrator.coordinate_agents("reconnaissance", {})

        # Note: This test demonstrates timeout handling pattern


class TestAgentOrchestratorConversation:
    """Test conversation facilitation"""

    @pytest.mark.asyncio
    async def test_facilitate_conversation(self):
        """Test facilitating multi-round conversation"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("A1", AgentRole.RESEARCHER)
        agent2 = MockAgent("A2", AgentRole.ANALYST)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        conversation = await orchestrator.facilitate_conversation("Security Topic", [agent1.id, agent2.id], rounds=2)

        assert isinstance(conversation, list)
        # Each agent should receive 2 messages (2 rounds)
        assert agent1.message_queue.qsize() == 2
        assert agent2.message_queue.qsize() == 2

    @pytest.mark.asyncio
    async def test_facilitate_conversation_default_rounds(self):
        """Test conversation with default rounds"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("A1", AgentRole.RESEARCHER)
        orchestrator.register_agent(agent1)

        await orchestrator.facilitate_conversation("Topic", [agent1.id])

        # Default is 3 rounds
        assert agent1.message_queue.qsize() == 3

    @pytest.mark.asyncio
    async def test_facilitate_conversation_nonexistent_agent(self):
        """Test conversation with nonexistent agent"""
        orchestrator = AgentOrchestrator()

        # Should not raise
        conversation = await orchestrator.facilitate_conversation("Topic", ["nonexistent-id"], rounds=1)

        assert isinstance(conversation, list)


class TestAgentOrchestratorLifecycle:
    """Test orchestrator lifecycle methods"""

    @pytest.mark.asyncio
    async def test_start_all(self):
        """Test starting all agents"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("A1", AgentRole.RESEARCHER)
        agent2 = MockAgent("A2", AgentRole.ANALYST)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        await orchestrator.start_all()

        # Allow tasks to start
        await asyncio.sleep(0.1)

        assert orchestrator.running is True
        assert agent1.running is True
        assert agent2.running is True

        # Cleanup
        await orchestrator.stop_all()

    @pytest.mark.asyncio
    async def test_stop_all(self):
        """Test stopping all agents"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("A1", AgentRole.RESEARCHER)
        agent2 = MockAgent("A2", AgentRole.ANALYST)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        await orchestrator.start_all()
        await orchestrator.stop_all()

        assert orchestrator.running is False
        assert agent1.running is False
        assert agent2.running is False

    @pytest.mark.asyncio
    async def test_start_all_empty(self):
        """Test starting with no agents"""
        orchestrator = AgentOrchestrator()

        await orchestrator.start_all()

        assert orchestrator.running is True


class TestAgentOrchestratorStatus:
    """Test system status reporting"""

    def test_get_system_status_empty(self):
        """Test status with no agents"""
        orchestrator = AgentOrchestrator()

        status = orchestrator.get_system_status()

        assert status["agents"] == {}
        assert status["shared_context_keys"] == []
        assert status["message_count"] == 0
        assert status["active_research"] == []
        assert status["role_distribution"] == {}

    def test_get_system_status_with_agents(self):
        """Test status with registered agents"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("A1", AgentRole.RESEARCHER)
        agent2 = MockAgent("A2", AgentRole.ANALYST)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        status = orchestrator.get_system_status()

        assert len(status["agents"]) == 2
        assert status["role_distribution"]["researcher"] == 1
        assert status["role_distribution"]["analyst"] == 1

    def test_get_system_status_with_context(self):
        """Test status with shared context"""
        orchestrator = AgentOrchestrator()

        orchestrator.shared_context["key1"] = {"value": "v1"}
        orchestrator.shared_context["key2"] = {"value": "v2"}

        status = orchestrator.get_system_status()

        assert "key1" in status["shared_context_keys"]
        assert "key2" in status["shared_context_keys"]


class TestAgentOrchestratorPostScanWorkflow:
    """Test post-scan workflow"""

    @pytest.mark.asyncio
    async def test_execute_post_scan_workflow(self):
        """Test executing post-scan workflow"""
        orchestrator = AgentOrchestrator()

        scan_results = {"target": "example.com", "findings": [{"id": "CVE-2021-44228", "severity": "critical"}]}

        # Mock PostScanAgent in the correct module
        with patch("agents.post_scan_agent.PostScanAgent") as MockPostScan:
            mock_instance = AsyncMock()
            mock_instance.run = AsyncMock(return_value={"verified": True})
            MockPostScan.return_value = mock_instance

            results = await orchestrator.execute_post_scan_workflow("example.com", scan_results)

            assert results is not None
            mock_instance.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_scan_workflow_no_findings(self):
        """Test post-scan workflow with no findings generates samples"""
        orchestrator = AgentOrchestrator()

        scan_results = {"target": "example.com", "findings": []}

        # Mock PostScanAgent in the correct module
        with patch("agents.post_scan_agent.PostScanAgent") as MockPostScan:
            mock_instance = AsyncMock()
            mock_instance.run = AsyncMock(return_value={"verified": True})
            MockPostScan.return_value = mock_instance

            await orchestrator.execute_post_scan_workflow("example.com", scan_results)

            # Should generate sample findings
            mock_instance.run.assert_called_once()

    def test_generate_sample_findings(self):
        """Test sample findings generation"""
        orchestrator = AgentOrchestrator()

        findings = orchestrator._generate_sample_findings("example.com")

        assert len(findings) == 3
        assert findings[0]["id"] == "CVE-2021-44228"
        assert findings[0]["severity"] == "critical"


class TestAgentOrchestratorEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_route_message_malformed_recipient(self):
        """Test routing with malformed recipient"""
        orchestrator = AgentOrchestrator()

        msg = AgentMessage(sender="Test", recipient="malformed[", content="Test")

        # Should not raise
        await orchestrator.route_message(msg)

    @pytest.mark.asyncio
    async def test_route_message_nonexistent_agent_direct(self):
        """Test direct message to nonexistent agent"""
        orchestrator = AgentOrchestrator()

        msg = AgentMessage(sender="Test", recipient="Agent[nonexistent]", content="Test")

        # Should not raise
        await orchestrator.route_message(msg)

    def test_unregister_agent_not_in_role_index(self):
        """Test unregistering agent that's not in role index"""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("Test", AgentRole.RESEARCHER)

        orchestrator.register_agent(agent)
        # Manually remove from role index to simulate inconsistency
        orchestrator.agent_by_role[AgentRole.RESEARCHER] = []

        # Should not raise
        orchestrator.unregister_agent(agent.id)

    @pytest.mark.asyncio
    async def test_research_coordination_no_researchers(self):
        """Test research coordination with no researchers"""
        orchestrator = AgentOrchestrator()
        analyst = MockAgent("A1", AgentRole.ANALYST)
        orchestrator.register_agent(analyst)

        thread_id = await orchestrator.start_research_coordination("Topic", {})

        assert thread_id.startswith("research_")
        # No researchers to notify
        assert analyst.message_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_conversation_with_partial_invalid_ids(self):
        """Test conversation with mix of valid and invalid agent IDs"""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("A1", AgentRole.RESEARCHER)
        orchestrator.register_agent(agent1)

        conversation = await orchestrator.facilitate_conversation("Topic", [agent1.id, "invalid-id"], rounds=1)

        # Should only send to valid agent
        assert agent1.message_queue.qsize() == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
