"""
Extended Agents Tests
"""
from unittest.mock import patch


class TestAgentBaseExtended:
    """Erweiterte Agent Base Tests"""

    def test_agent_message_creation(self):
        from agents.agent_base import AgentMessage
        msg = AgentMessage(
            sender="researcher",
            content="Test message",
            message_type="findings"
        )
        assert msg.sender == "researcher"
        assert msg.content == "Test message"
        assert msg.message_type == "findings"

    def test_agent_role_enum(self):
        from agents.agent_base import AgentRole
        assert AgentRole.RESEARCHER == "researcher"
        assert AgentRole.ANALYST == "analyst"
        assert AgentRole.EXPLOIT == "exploit"

    def test_base_agent_creation_mock(self):
        from agents.agent_base import BaseAgent, AgentRole
        with patch.object(BaseAgent, '__abstractmethods__', set()):
            agent = BaseAgent(role=AgentRole.RESEARCHER, name="TestAgent")
            assert agent.role == AgentRole.RESEARCHER
            assert agent.name == "TestAgent"


class TestResearchAgent:
    """Research Agent Tests"""

    def test_research_agent_import(self):
        from agents.research_agent import ResearchAgent
        assert ResearchAgent is not None

    def test_research_agent_creation_mock(self):
        from agents.research_agent import ResearchAgent
        with patch.object(ResearchAgent, '__init__', lambda self: None):
            agent = ResearchAgent.__new__(ResearchAgent)
            assert agent is not None


class TestAnalysisAgent:
    """Analysis Agent Tests"""

    def test_analysis_agent_import(self):
        from agents.analysis_agent import AnalysisAgent
        assert AnalysisAgent is not None

    def test_analysis_agent_creation_mock(self):
        from agents.analysis_agent import AnalysisAgent
        with patch.object(AnalysisAgent, '__init__', lambda self: None):
            agent = AnalysisAgent.__new__(AnalysisAgent)
            assert agent is not None


class TestExploitAgent:
    """Exploit Agent Tests"""

    def test_exploit_agent_import(self):
        from agents.exploit_agent import ExploitAgent
        assert ExploitAgent is not None


class TestPostScanAgent:
    """Post Scan Agent Tests"""

    def test_post_scan_agent_import(self):
        from agents.post_scan_agent import PostScanAgent
        assert PostScanAgent is not None

    def test_verified_finding_creation(self):
        from agents.post_scan_agent import VerifiedFinding
        finding = VerifiedFinding(
            title="Test",
            severity="high",
            verified=True
        )
        assert finding.title == "Test"
        assert finding.verified is True


class TestAgentOrchestrator:
    """Agent Orchestrator Tests"""

    def test_orchestrator_creation(self):
        from agents.agent_orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        assert orch is not None

    def test_orchestrator_has_agents(self):
        from agents.agent_orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        assert hasattr(orch, 'agents')
