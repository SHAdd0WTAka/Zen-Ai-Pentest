"""Einfache Core Module Tests - Target: Coverage Boost."""

import pytest

# Test orchestrator
def test_orchestrator_import():
    """Test that orchestrator can be imported."""
    from core.orchestrator import ZenOrchestrator
    assert ZenOrchestrator is not None

def test_orchestrator_init():
    """Test ZenOrchestrator initialization."""
    from core.orchestrator import ZenOrchestrator
    orch = ZenOrchestrator()
    assert orch is not None


# Test state_machine
def test_state_machine_import():
    """Test that state_machine can be imported."""
    from core.state_machine import AdvancedStateMachine
    assert AdvancedStateMachine is not None

def test_state_machine_init():
    """Test AdvancedStateMachine initialization."""
    from core.state_machine import AdvancedStateMachine
    sm = AdvancedStateMachine()
    assert sm is not None


# Test workflow_engine
def test_workflow_engine_import():
    """Test that workflow_engine can be imported."""
    from core.workflow_engine import WorkflowEngine
    assert WorkflowEngine is not None

def test_workflow_engine_init():
    """Test WorkflowEngine initialization."""
    from core.workflow_engine import WorkflowEngine
    engine = WorkflowEngine()
    assert engine is not None


# Test cache
def test_cache_import():
    """Test that cache can be imported."""
    from core.cache import MemoryCache, CacheStats
    assert MemoryCache is not None
    assert CacheStats is not None

def test_cache_stats_init():
    """Test CacheStats initialization."""
    from core.cache import CacheStats
    stats = CacheStats()
    assert stats.hits == 0
    assert stats.misses == 0


# Test tool_manager
def test_tool_manager_import():
    """Test that tool_manager can be imported."""
    from core.tool_manager import ToolManager
    assert ToolManager is not None

def test_tool_manager_init():
    """Test ToolManager initialization."""
    from core.tool_manager import ToolManager
    tm = ToolManager()
    assert tm is not None
