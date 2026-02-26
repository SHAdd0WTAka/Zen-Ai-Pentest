"""Tests for core/state_machine.py - State Machine."""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from core.state_machine import (
    StateType,
    HistoryType,
    StateEvent,
    TransitionGuard,
    StateAction,
    StateContext,
    State,
    Transition,
)


class TestStateType:
    """Test StateType enum."""

    def test_enum_values(self):
        """Test state type values."""
        assert StateType.SIMPLE.value == "simple"
        assert StateType.COMPOSITE.value == "composite"
        assert StateType.PARALLEL.value == "parallel"
        assert StateType.HISTORY.value == "history"
        assert StateType.FINAL.value == "final"


class TestHistoryType:
    """Test HistoryType enum."""

    def test_enum_values(self):
        """Test history type values."""
        assert HistoryType.SHALLOW.value == "shallow"
        assert HistoryType.DEEP.value == "deep"


class TestStateEvent:
    """Test StateEvent dataclass."""

    def test_default_creation(self):
        """Test creating event with defaults."""
        event = StateEvent(name="test_event")
        
        assert event.name == "test_event"
        assert event.payload == {}
        assert isinstance(event.timestamp, datetime)
        assert event.source is None

    def test_full_creation(self):
        """Test creating event with all fields."""
        ts = datetime.now()
        event = StateEvent(
            name="test",
            payload={"key": "value"},
            timestamp=ts,
            source="test_source"
        )
        
        assert event.name == "test"
        assert event.payload == {"key": "value"}
        assert event.timestamp == ts
        assert event.source == "test_source"

    def test_to_dict(self):
        """Test serialization to dict."""
        event = StateEvent(
            name="test",
            payload={"key": "value"},
            source="source"
        )
        d = event.to_dict()
        
        assert d["name"] == "test"
        assert d["payload"] == {"key": "value"}
        assert d["source"] == "source"
        assert isinstance(d["timestamp"], str)


class TestTransitionGuard:
    """Test TransitionGuard class."""

    def test_guard_creation(self):
        """Test creating a guard."""
        condition = lambda event, context: True
        guard = TransitionGuard(condition, "Always true", priority=5)
        
        assert guard.condition is condition
        assert guard.description == "Always true"
        assert guard.priority == 5

    def test_guard_evaluate_true(self):
        """Test guard evaluation returning True."""
        condition = lambda event, context: True
        guard = TransitionGuard(condition)
        
        result = guard.evaluate(MagicMock(), MagicMock())
        assert result is True

    def test_guard_evaluate_false(self):
        """Test guard evaluation returning False."""
        condition = lambda event, context: False
        guard = TransitionGuard(condition)
        
        result = guard.evaluate(MagicMock(), MagicMock())
        assert result is False

    def test_guard_evaluate_exception(self):
        """Test guard handles exception gracefully."""
        condition = lambda event, context: 1/0  # Raises ZeroDivisionError
        guard = TransitionGuard(condition)
        
        result = guard.evaluate(MagicMock(), MagicMock())
        assert result is False


class TestStateAction:
    """Test StateAction dataclass."""

    def test_default_creation(self):
        """Test creating action with defaults."""
        action_func = lambda state, context: None
        action = StateAction(action_func)
        
        assert action.action is action_func
        assert action.async_execution is False
        assert action.timeout_seconds is None
        assert action.retry_on_failure is False
        assert action.max_retries == 3

    def test_custom_creation(self):
        """Test creating action with custom values."""
        action_func = lambda state, context: None
        action = StateAction(
            action_func,
            async_execution=True,
            timeout_seconds=30.0,
            retry_on_failure=True,
            max_retries=5
        )
        
        assert action.async_execution is True
        assert action.timeout_seconds == 30.0
        assert action.retry_on_failure is True
        assert action.max_retries == 5


class TestStateContext:
    """Test StateContext class."""

    def test_init_default(self):
        """Test initialization with default session."""
        ctx = StateContext()
        
        assert ctx.session_id is not None
        assert isinstance(ctx.session_id, str)
        assert ctx.data == {}
        assert ctx.start_time is not None

    def test_init_custom_session(self):
        """Test initialization with custom session."""
        ctx = StateContext(session_id="custom_123")
        
        assert ctx.session_id == "custom_123"

    def test_log_event(self):
        """Test logging events."""
        ctx = StateContext()
        event = StateEvent(name="test_event", payload={"key": "value"})
        
        ctx.log_event(event)
        
        assert len(ctx.event_log) == 1
        logged = ctx.event_log[0]
        assert logged["name"] == "test_event"
        assert logged["context_session"] == ctx.session_id

    def test_log_multiple_events(self):
        """Test logging multiple events."""
        ctx = StateContext()
        
        for i in range(5):
            ctx.log_event(StateEvent(name=f"event_{i}"))
        
        assert len(ctx.event_log) == 5


class TestState:
    """Test State class."""

    def test_init_simple(self):
        """Test simple state initialization."""
        state = State("idle")
        
        assert state.name == "idle"
        assert state.state_type == StateType.SIMPLE
        assert state.parent is None
        assert state.sub_states == {}
        assert state._active is False

    def test_init_composite(self):
        """Test composite state initialization."""
        state = State("parent", StateType.COMPOSITE)
        
        assert state.name == "parent"
        assert state.state_type == StateType.COMPOSITE

    def test_add_sub_state(self):
        """Test adding sub-state."""
        parent = State("parent", StateType.COMPOSITE)
        child = State("child")
        
        parent.add_sub_state(child)
        
        assert "child" in parent.sub_states
        assert child.parent is parent
        assert parent.initial_sub_state == "child"

    def test_add_multiple_sub_states(self):
        """Test adding multiple sub-states."""
        parent = State("parent", StateType.COMPOSITE)
        child1 = State("child1")
        child2 = State("child2")
        
        parent.add_sub_state(child1)
        parent.add_sub_state(child2)
        
        assert len(parent.sub_states) == 2
        assert parent.initial_sub_state == "child1"  # First one

    def test_on_entry_decorator(self):
        """Test on_entry decorator pattern."""
        state = State("test")
        action = lambda state, ctx: None
        
        result = state.on_entry(action)
        
        assert result is state  # Returns self for chaining
        assert len(state.entry_actions) == 1

    def test_on_exit_decorator(self):
        """Test on_exit decorator pattern."""
        state = State("test")
        action = lambda state, ctx: None
        
        result = state.on_exit(action)
        
        assert result is state
        assert len(state.exit_actions) == 1

    def test_while_in_state_decorator(self):
        """Test while_in_state decorator pattern."""
        state = State("test")
        action = lambda state, ctx: None
        
        result = state.while_in_state(action)
        
        assert result is state
        assert len(state.while_in_state_actions) == 1
        assert state.while_in_state_actions[0].async_execution is True

    def test_is_active_default(self):
        """Test is_active returns False by default."""
        state = State("test")
        
        assert state.is_active() is False

    def test_get_duration_none(self):
        """Test get_duration returns None when not entered."""
        state = State("test")
        
        assert state.get_duration() is None

    def test_to_dict(self):
        """Test state serialization."""
        state = State("test", StateType.COMPOSITE)
        state._active = True
        state.add_sub_state(State("child"))
        
        d = state.to_dict()
        
        assert d["name"] == "test"
        assert d["type"] == "composite"
        assert d["active"] is True
        assert "child" in d["sub_states"]


class TestTransition:
    """Test Transition class."""

    def test_simple_transition(self):
        """Test simple transition creation."""
        t = Transition("idle", "active", event="start")
        
        assert t.source == "idle"
        assert t.target == "active"
        assert t.event == "start"
        assert t.guards == []
        assert t.priority == 0
        assert t.auto_trigger is False

    def test_transition_with_priority(self):
        """Test transition with priority."""
        t = Transition("a", "b", priority=10)
        
        assert t.priority == 10

    def test_transition_auto_trigger(self):
        """Test auto-trigger transition."""
        t = Transition("a", "b", auto_trigger=True)
        
        assert t.auto_trigger is True

    def test_transition_with_delay(self):
        """Test transition with delay."""
        t = Transition("a", "b", delay_seconds=5.0)
        
        assert t.delay_seconds == 5.0

    def test_can_fire_matching_event(self):
        """Test can_fire with matching event."""
        t = Transition("idle", "active", event="start")
        event = StateEvent(name="start")
        context = MagicMock()
        
        result = t.can_fire(event, context)
        
        assert result is True

    def test_can_fire_non_matching_event(self):
        """Test can_fire with non-matching event."""
        t = Transition("idle", "active", event="start")
        event = StateEvent(name="stop")
        context = MagicMock()
        
        result = t.can_fire(event, context)
        
        assert result is False

    def test_can_fire_with_guards(self):
        """Test can_fire with guards."""
        guard = TransitionGuard(lambda e, c: True)
        t = Transition("idle", "active", event="start", guards=[guard])
        event = StateEvent(name="start")
        context = MagicMock()
        
        result = t.can_fire(event, context)
        
        assert result is True

    def test_can_fire_with_failing_guard(self):
        """Test can_fire with failing guard."""
        guard = TransitionGuard(lambda e, c: False)
        t = Transition("idle", "active", event="start", guards=[guard])
        event = StateEvent(name="start")
        context = MagicMock()
        
        result = t.can_fire(event, context)
        
        assert result is False

    def test_can_fire_no_event_required(self):
        """Test can_fire when no event required."""
        t = Transition("idle", "active")  # No event
        event = StateEvent(name="anything")
        context = MagicMock()
        
        result = t.can_fire(event, context)
        
        assert result is True


class TestStateMachineStructure:
    """Test AdvancedStateMachine structure (without full async testing)."""

    def test_import(self):
        """Test that AdvancedStateMachine can be imported."""
        from core.state_machine import AdvancedStateMachine
        
        assert AdvancedStateMachine is not None

    def test_init_defaults(self):
        """Test initialization with defaults."""
        from core.state_machine import AdvancedStateMachine
        
        sm = AdvancedStateMachine()
        
        assert sm.name == "StateMachine"
        assert sm.states == {}
        assert sm.transitions == []
        assert sm._current_state is None
        assert sm.enable_persistence is True
        assert sm.auto_recovery is True

    def test_init_custom(self):
        """Test initialization with custom values."""
        from core.state_machine import AdvancedStateMachine
        
        sm = AdvancedStateMachine(
            name="CustomSM",
            enable_persistence=False,
            auto_recovery=False
        )
        
        assert sm.name == "CustomSM"
        assert sm.enable_persistence is False
        assert sm.auto_recovery is False

    def test_add_state(self):
        """Test adding a state."""
        from core.state_machine import AdvancedStateMachine
        
        sm = AdvancedStateMachine()
        state = State("idle")
        
        result = sm.add_state(state)
        
        assert result is state
        assert "idle" in sm.states

    def test_add_transition(self):
        """Test adding a transition."""
        from core.state_machine import AdvancedStateMachine
        
        sm = AdvancedStateMachine()
        t = Transition("idle", "active", event="start")
        
        sm.add_transition(t)
        
        assert len(sm.transitions) == 1
        assert sm.transitions[0] is t

    def test_add_multiple_transitions_sorted(self):
        """Test that transitions are sorted by priority."""
        from core.state_machine import AdvancedStateMachine
        
        sm = AdvancedStateMachine()
        t1 = Transition("a", "b", priority=1)
        t2 = Transition("a", "c", priority=10)
        t3 = Transition("a", "d", priority=5)
        
        sm.add_transition(t1)
        sm.add_transition(t2)
        sm.add_transition(t3)
        
        assert sm.transitions[0].priority == 10
        assert sm.transitions[1].priority == 5
        assert sm.transitions[2].priority == 1

    def test_on_event_handler(self):
        """Test registering event handler."""
        from core.state_machine import AdvancedStateMachine
        
        sm = AdvancedStateMachine()
        handler = lambda event, ctx: None
        
        sm.on("custom_event", handler)
        
        assert "custom_event" in sm._event_handlers
        assert handler in sm._event_handlers["custom_event"]

    def test_on_multiple_handlers(self):
        """Test registering multiple handlers for same event."""
        from core.state_machine import AdvancedStateMachine
        
        sm = AdvancedStateMachine()
        handler1 = lambda e, c: None
        handler2 = lambda e, c: None
        
        sm.on("event", handler1)
        sm.on("event", handler2)
        
        assert len(sm._event_handlers["event"]) == 2


class TestAllExports:
    """Test that all expected exports are available."""

    def test_exports(self):
        """Test that all exports are importable."""
        from core import state_machine
        
        assert hasattr(state_machine, 'StateType')
        assert hasattr(state_machine, 'HistoryType')
        assert hasattr(state_machine, 'StateEvent')
        assert hasattr(state_machine, 'TransitionGuard')
        assert hasattr(state_machine, 'StateAction')
        assert hasattr(state_machine, 'StateContext')
        assert hasattr(state_machine, 'State')
        assert hasattr(state_machine, 'Transition')
        assert hasattr(state_machine, 'AdvancedStateMachine')
