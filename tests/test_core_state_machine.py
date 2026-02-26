"""Tests für core/state_machine.py - Target: 80%+ Coverage."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from core.state_machine import (
    StateType,
    HistoryType,
    StateEvent,
    State,
    Transition,
    TransitionGuard,
    StateAction,
    AdvancedStateMachine,
    PentestStateMachine,
)


class TestStateType:
    """Tests für StateType Enum."""

    def test_state_type_values(self):
        """Test StateType enum values."""
        assert StateType.INITIAL.value == "initial"
        assert StateType.NORMAL.value == "normal"
        assert StateType.FINAL.value == "final"
        assert StateType.CHOICE.value == "choice"


class TestHistoryType:
    """Tests für HistoryType Enum."""

    def test_history_type_values(self):
        """Test HistoryType enum values."""
        assert HistoryType.NONE.value == "none"
        assert HistoryType.SHALLOW.value == "shallow"
        assert HistoryType.DEEP.value == "deep"


class TestStateEvent:
    """Tests für StateEvent."""

    def test_state_event_init(self):
        """Test StateEvent initialization."""
        event = StateEvent(name="test_event", payload={"key": "value"})
        assert event.name == "test_event"
        assert event.payload == {"key": "value"}

    def test_state_event_defaults(self):
        """Test StateEvent default values."""
        event = StateEvent(name="test_event")
        assert event.name == "test_event"
        assert event.payload == {}


class TestState:
    """Tests für State."""

    def test_state_init(self):
        """Test State initialization."""
        state = State(name="test_state")
        assert state.name == "test_state"
        assert state.state_type == StateType.NORMAL

    def test_state_with_type(self):
        """Test State with specific type."""
        state = State(name="initial", state_type=StateType.INITIAL)
        assert state.state_type == StateType.INITIAL

    def test_state_is_initial(self):
        """Test is_initial property."""
        state = State(name="initial", state_type=StateType.INITIAL)
        assert state.is_initial is True

    def test_state_is_final(self):
        """Test is_final property."""
        state = State(name="final", state_type=StateType.FINAL)
        assert state.is_final is True


class TestTransition:
    """Tests für Transition."""

    def test_transition_init(self):
        """Test Transition initialization."""
        transition = Transition(
            source="state1",
            target="state2",
            event="go",
        )
        assert transition.source == "state1"
        assert transition.target == "state2"
        assert transition.event == "go"


class TestAdvancedStateMachine:
    """Tests für AdvancedStateMachine."""

    @pytest.fixture
    def sm(self):
        """Create a test state machine."""
        return AdvancedStateMachine()

    def test_state_machine_init(self, sm):
        """Test state machine initialization."""
        assert sm is not None
        assert sm.current_state is None

    def test_add_state(self, sm):
        """Test adding a state."""
        state = sm.add_state("idle")
        assert state.name == "idle"
        assert "idle" in sm.states

    def test_add_transition(self, sm):
        """Test adding a transition."""
        sm.add_state("idle")
        sm.add_state("running")
        sm.add_transition("idle", "running", "start")
        assert len(sm.transitions) == 1

    def test_set_initial_state(self, sm):
        """Test setting initial state."""
        sm.add_state("idle")
        sm.set_initial_state("idle")
        assert sm.current_state.name == "idle"

    def test_trigger_transition(self, sm):
        """Test triggering a transition."""
        sm.add_state("idle")
        sm.add_state("running")
        sm.add_transition("idle", "running", "start")
        sm.set_initial_state("idle")
        sm.trigger("start")
        assert sm.current_state.name == "running"


class TestPentestStateMachine:
    """Tests für PentestStateMachine."""

    def test_pentest_sm_init(self):
        """Test PentestStateMachine initialization."""
        sm = PentestStateMachine()
        assert sm is not None
