"""Einfache Agents Module Tests."""

import pytest

def test_agent_base_import():
    """Test that agent_base can be imported."""
    from agents.agent_base import BaseAgent, AgentState
    assert BaseAgent is not None
    assert AgentState is not None

def test_agent_orchestrator_import():
    """Test that agent_orchestrator can be imported."""
    from agents.agent_orchestrator import AgentOrchestrator
    assert AgentOrchestrator is not None

def test_agent_orchestrator_init():
    """Test AgentOrchestrator initialization."""
    from agents.agent_orchestrator import AgentOrchestrator
    orch = AgentOrchestrator()
    assert orch is not None
