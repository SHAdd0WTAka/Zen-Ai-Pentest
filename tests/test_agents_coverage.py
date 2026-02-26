"""Agents Module Tests"""
import pytest
from unittest.mock import Mock, patch

from agents.agent_base import BaseAgent, AgentState, AgentRole


def test_agent_state_enum():
    """Test AgentState enum."""
    assert AgentState.IDLE.value == "idle"
    assert AgentState.BUSY.value == "busy"


def test_agent_role_enum():
    """Test AgentRole enum."""
    assert AgentRole.RESEARCHER.value == "researcher"
    assert AgentRole.ANALYST.value == "analyst"
