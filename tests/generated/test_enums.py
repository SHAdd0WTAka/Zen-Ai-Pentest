"""Generated Enum Tests - Auto-generated."""

import pytest


def test_scanstatus_values():
    """Test ScanStatus enum values."""
    from database.models import ScanStatus
    assert ScanStatus.PENDING.value == "pending"
    assert ScanStatus.RUNNING.value == "running"
    assert ScanStatus.COMPLETED.value == "completed"
    assert ScanStatus.FAILED.value == "failed"
    assert ScanStatus.CANCELLED.value == "cancelled"

def test_severity_values():
    """Test Severity enum values."""
    from database.models import Severity
    assert Severity.INFO.value == "info"
    assert Severity.LOW.value == "low"
    assert Severity.MEDIUM.value == "medium"
    assert Severity.HIGH.value == "high"
    assert Severity.CRITICAL.value == "critical"

def test_agentstate_values():
    """Test AgentState enum values."""
    from agents.agent_base import AgentState
    assert AgentState.IDLE.value == "idle"
    assert AgentState.BUSY.value == "busy"
    assert AgentState.STOPPED.value == "stopped"

def test_agentrole_values():
    """Test AgentRole enum values."""
    from agents.agent_base import AgentRole
    assert AgentRole.RESEARCHER.value == "researcher"
    assert AgentRole.ANALYST.value == "analyst"
    assert AgentRole.EXPLOIT.value == "exploit"

def test_cachebackend_values():
    """Test CacheBackend enum values."""
    from core.cache import CacheBackend
    assert CacheBackend.MEMORY.value == "memory"
    assert CacheBackend.REDIS.value == "redis"
    assert CacheBackend.SQLITE.value == "sqlite"
