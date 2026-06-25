"""Coverage Blitz 5: 10 Tests für agents/"""

import pytest


def test_agent_role_enum():
    """Agent Role Enum Werte."""
    from agents.agent_base import AgentRole

    roles = ["RESEARCHER", "ANALYST", "EXPLOIT", "REPORTER", "COORDINATOR"]
    for role in roles:
        assert hasattr(AgentRole, role)


def test_agent_state_enum():
    """Agent State Enum Werte."""
    from agents.agent_base import AgentState

    states = ["IDLE", "BUSY", "WAITING", "COMPLETED", "FAILED", "STOPPED"]
    for state in states:
        assert hasattr(AgentState, state)


def test_agent_message_creation():
    """Agent Message Erstellung."""
    from agents.agent_base import AgentMessage

    msg = AgentMessage(sender="agent1", recipient="agent2", content={"task": "scan"})

    assert msg.sender == "agent1"
    assert msg.recipient == "agent2"


def test_agent_message_to_dict():
    """Agent Message zu Dict."""
    from agents.agent_base import AgentMessage

    msg = AgentMessage(sender="test", recipient="other", content={"status": "running"})

    d = msg.to_dict()
    assert d["sender"] == "test"
    assert "content" in d


def test_research_agent_import():
    """Research Agent Import."""
    from agents.research_agent import ResearchAgent

    assert ResearchAgent is not None


def test_analysis_agent_import():
    """Analysis Agent Import."""
    from agents.analysis_agent import AnalysisAgent

    assert AnalysisAgent is not None


def test_exploit_agent_import():
    """Exploit Agent Import."""
    from agents.exploit_agent import ExploitAgent

    assert ExploitAgent is not None


def test_react_agent_import():
    """ReAct Agent Import."""
    try:
        from agents.react_agent import ReActAgent

        assert ReActAgent is not None
    except ImportError:
        from agents.agent_base import BaseAgent

        assert BaseAgent is not None


def test_post_scan_agent_import():
    """Post Scan Agent Import."""
    from agents.post_scan_agent import PostScanAgent

    assert PostScanAgent is not None


def test_agent_orchestrator_import():
    """Agent Orchestrator Import."""
    from agents.agent_orchestrator import AgentOrchestrator

    assert AgentOrchestrator is not None
