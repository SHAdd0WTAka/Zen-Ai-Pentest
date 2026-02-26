"""Phase 1: Final Core Tests - Target 80% Coverage.

Angepasst an tatsächliche APIs.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from core.orchestrator import (
    ZenOrchestrator,
    QualityLevel,
    LLMResponse,
    AgentMemory,
)

from core.state_machine import (
    StateType,
    HistoryType,
    StateEvent,
    TransitionGuard,
    StateAction,
    StateContext,
    State,
    Transition,
    AdvancedStateMachine,
    PentestStateMachine,
)


# ========== Orchestrator Tests ==========

class TestQualityLevel:
    """Tests for QualityLevel enum."""

    def test_all_quality_levels(self):
        """Test all quality levels exist."""
        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.HIGH.value == "high"

    def test_quality_level_count(self):
        """Test number of quality levels."""
        levels = list(QualityLevel)
        assert len(levels) == 3


class TestLLMResponse:
    """Tests for LLMResponse."""

    def test_llm_response_creation(self):
        """Test LLMResponse creation."""
        response = LLMResponse(
            content="Test response",
            source="gpt-4",
            latency=1.5,
            quality=QualityLevel.HIGH,
        )
        assert response.content == "Test response"
        assert response.source == "gpt-4"
        assert response.latency == 1.5

    def test_llm_response_default_metadata(self):
        """Test LLMResponse default metadata."""
        response = LLMResponse(
            content="Test",
            source="test",
            latency=1.0,
            quality=QualityLevel.LOW,
        )
        assert response.metadata is None or isinstance(response.metadata, dict)


class TestAgentMemory:
    """Tests for AgentMemory."""

    def test_agent_memory_default(self):
        """Test AgentMemory default values."""
        memory = AgentMemory()
        assert memory.goal == ""
        assert memory.target == ""
        assert memory.max_short_term == 100

    def test_agent_memory_custom(self):
        """Test AgentMemory with custom values."""
        memory = AgentMemory(
            goal="Test goal",
            target="example.com",
            max_short_term=50
        )
        assert memory.goal == "Test goal"
        assert memory.target == "example.com"
        assert memory.max_short_term == 50


class TestZenOrchestrator:
    """Tests for ZenOrchestrator."""

    def test_orchestrator_creation(self):
        """Test orchestrator creation."""
        orch = ZenOrchestrator()
        assert orch is not None


# ========== State Machine Tests ==========

class TestStateType:
    """Tests for StateType enum."""

    def test_all_state_types(self):
        """Test all state types exist."""
        assert StateType.SIMPLE.value == "simple"
        assert StateType.COMPOSITE.value == "composite"
        assert StateType.PARALLEL.value == "parallel"
        assert StateType.HISTORY.value == "history"
        assert StateType.FINAL.value == "final"

    def test_state_type_count(self):
        """Test number of state types."""
        types = list(StateType)
        assert len(types) == 5


class TestHistoryType:
    """Tests for HistoryType enum."""

    def test_all_history_types(self):
        """Test all history types exist."""
        assert HistoryType.SHALLOW.value == "shallow"
        assert HistoryType.DEEP.value == "deep"

    def test_history_type_count(self):
        """Test number of history types."""
        types = list(HistoryType)
        assert len(types) == 2


class TestStateEvent:
    """Tests for StateEvent."""

    def test_event_creation(self):
        """Test event creation."""
        event = StateEvent(name="test_event")
        assert event.name == "test_event"

    def test_event_timestamp(self):
        """Test event has timestamp."""
        event = StateEvent(name="test")
        assert hasattr(event, 'timestamp')


class TestStateContext:
    """Tests for StateContext."""

    def test_context_creation(self):
        """Test context creation."""
        ctx = StateContext()
        assert ctx is not None

    def test_context_with_session(self):
        """Test context with session ID."""
        ctx = StateContext(session_id="session-123")
        assert ctx.session_id == "session-123"


class TestState:
    """Tests for State."""

    def test_state_creation_simple(self):
        """Test simple state creation."""
        state = State(name="idle")
        assert state.name == "idle"

    def test_state_creation_typed(self):
        """Test state with specific type."""
        state = State(name="final", state_type=StateType.FINAL)
        assert state.state_type == StateType.FINAL


class TestTransition:
    """Tests for Transition."""

    def test_transition_creation(self):
        """Test transition creation."""
        transition = Transition(source="s1", target="s2")
        assert transition.source == "s1"
        assert transition.target == "s2"


class TestTransitionGuard:
    """Tests for TransitionGuard."""

    def test_guard_creation(self):
        """Test guard creation."""
        def condition(event, context):
            return True
        
        guard = TransitionGuard(condition=condition)
        assert guard is not None


class TestStateAction:
    """Tests for StateAction."""

    def test_action_creation(self):
        """Test action creation."""
        def action_func(state, context):
            pass
        
        action = StateAction(action=action_func)
        assert action is not None


class TestAdvancedStateMachine:
    """Tests for AdvancedStateMachine."""

    @pytest.fixture
    def sm(self):
        return AdvancedStateMachine()

    def test_sm_creation(self, sm):
        """Test SM creation."""
        assert sm is not None
        assert sm.name == "StateMachine"

    def test_sm_custom_name(self):
        """Test SM with custom name."""
        sm = AdvancedStateMachine(name="CustomSM")
        assert sm.name == "CustomSM"

    def test_add_state(self, sm):
        """Test adding state."""
        result = sm.add_state("idle")
        assert result is not None

    def test_states_dict_exists(self, sm):
        """Test states dict exists."""
        assert hasattr(sm, 'states')


class TestPentestStateMachine:
    """Tests for PentestStateMachine."""

    def test_psm_creation(self):
        """Test PSM creation."""
        psm = PentestStateMachine()
        assert psm is not None
