"""Agents Module Tests"""

from unittest.mock import Mock, patch

import pytest

from agents.agent_base import AgentRole, AgentState, BaseAgent


def test_agent_state_enum():
    """Test AgentState enum."""
    assert AgentState.IDLE.value == "idle"
    assert AgentState.BUSY.value == "busy"


def test_agent_role_enum():
    """Test AgentRole enum."""
    assert AgentRole.RESEARCHER.value == "researcher"
    assert AgentRole.ANALYST.value == "analyst"
