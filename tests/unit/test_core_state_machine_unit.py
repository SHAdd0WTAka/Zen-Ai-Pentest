"""
Unit Tests for State Machine - Core Functionality
Phase 1: Test Coverage Improvement
"""

import asyncio
import os
import sys
from datetime import timedelta
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestStateType:
    """Test StateType Enum"""

    def test_state_types_exist(self):
        from core.state_machine import StateType

        assert hasattr(StateType, "SIMPLE")
        assert hasattr(StateType, "COMPOSITE")
        assert hasattr(StateType, "PARALLEL")
        assert hasattr(StateType, "HISTORY")
        assert hasattr(StateType, "FINAL")

    def test_state_type_values(self):
        from core.state_machine import StateType

        assert StateType.SIMPLE.value == "simple"
        assert StateType.COMPOSITE.value == "composite"
        assert StateType.FINAL.value == "final"


class TestHistoryType:
    """Test HistoryType Enum"""

    def test_history_types_exist(self):
        from core.state_machine import HistoryType

        assert hasattr(HistoryType, "SHALLOW")
        assert hasattr(HistoryType, "DEEP")


class TestStateEvent:
    """Test StateEvent class"""

    def test_event_creation(self):
        from core.state_machine import StateEvent

        event = StateEvent(name="test_event", payload={"key": "value"})
        assert event.name == "test_event"
        assert event.payload == {"key": "value"}
        assert event.timestamp is not None

    def test_event_to_dict(self):
        from core.state_machine import StateEvent

        event = StateEvent(name="test", payload={"data": 123})
        data = event.to_dict()
        assert data["name"] == "test"
        assert data["payload"] == {"data": 123}


class TestStateContext:
    """Test StateContext class"""

    @pytest.mark.asyncio
    async def test_context_set_get(self):
        from core.state_machine import StateContext

        context = StateContext(session_id="test_session")

        await context.set("key1", "value1")
        result = await context.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_context_get_default(self):
        from core.state_machine import StateContext

        context = StateContext()

        result = await context.get("nonexistent", "default")
        assert result == "default"

    @pytest.mark.asyncio
    async def test_context_update(self):
        from core.state_machine import StateContext

        context = StateContext()

        await context.update({"a": 1, "b": 2})
        assert await context.get("a") == 1
        assert await context.get("b") == 2

    def test_context_session_id(self):
        from core.state_machine import StateContext

        context = StateContext(session_id="my_session")
        assert context.session_id == "my_session"


class TestState:
    """Test State class"""

    def test_state_creation(self):
        from core.state_machine import State, StateType

        state = State(name="test_state", state_type=StateType.SIMPLE)
        assert state.name == "test_state"
        assert state.state_type == StateType.SIMPLE
        assert not state.is_active()

    def test_state_with_parent(self):
        from core.state_machine import State, StateType

        parent = State(name="parent", state_type=StateType.SIMPLE)
        child = State(name="child", state_type=StateType.SIMPLE, parent=parent)

        assert child.parent == parent

    def test_state_entry_exit_handlers(self):
        from core.state_machine import State, StateType

        state = State(name="test", state_type=StateType.SIMPLE)

        def entry_handler():
            pass

        def exit_handler():
            pass

        state.on_entry(entry_handler)
        state.on_exit(exit_handler)

        # Check that actions were added (list of handlers)
        assert len(state.entry_actions) == 1
        assert len(state.exit_actions) == 1


class TestTransition:
    """Test Transition class"""

    def test_transition_creation(self):
        from core.state_machine import State, StateType, Transition

        from_state = State(name="from", state_type=StateType.SIMPLE)
        to_state = State(name="to", state_type=StateType.SIMPLE)

        transition = Transition(
            source="from",
            target="to",
            event="test_event",
        )

        assert transition.source == "from"
        assert transition.target == "to"
        assert transition.event == "test_event"

    def test_transition_can_fire(self):
        from core.state_machine import StateContext, StateEvent, Transition

        transition = Transition(
            source="idle",
            target="running",
            event="correct_event",
        )

        event = StateEvent(name="correct_event")
        context = StateContext()

        assert transition.can_fire(event, context) is True

    def test_transition_cannot_fire_wrong_event(self):
        from core.state_machine import StateContext, StateEvent, Transition

        transition = Transition(
            source="idle",
            target="running",
            event="expected_event",
        )

        event = StateEvent(name="wrong_event")
        context = StateContext()

        assert transition.can_fire(event, context) is False


class TestAdvancedStateMachine:
    """Test AdvancedStateMachine class"""

    def test_machine_creation(self):
        from core.state_machine import AdvancedStateMachine

        machine = AdvancedStateMachine(name="test_machine")
        assert machine.name == "test_machine"
        assert machine.get_current_state() is None

    def test_add_state(self):
        from core.state_machine import AdvancedStateMachine, State, StateType

        machine = AdvancedStateMachine()
        state = State(name="idle", state_type=StateType.SIMPLE)

        result = machine.add_state(state)
        assert result == state
        assert "idle" in machine.states

    def test_add_transition(self):
        from core.state_machine import (
            AdvancedStateMachine,
            State,
            StateType,
            Transition,
        )

        machine = AdvancedStateMachine()

        from_state = State(name="from", state_type=StateType.SIMPLE)
        to_state = State(name="to", state_type=StateType.SIMPLE)
        machine.add_state(from_state)
        machine.add_state(to_state)

        transition = Transition(
            source="from",
            target="to",
            event="go",
        )
        machine.add_transition(transition)

        assert len(machine.transitions) == 1

    @pytest.mark.asyncio
    async def test_start_machine(self):
        from core.state_machine import AdvancedStateMachine, State, StateType

        machine = AdvancedStateMachine()
        state = State(name="idle", state_type=StateType.SIMPLE)
        machine.add_state(state)

        await machine.start("idle")
        assert machine.get_current_state() == "idle"
        assert machine._running is True

    @pytest.mark.asyncio
    async def test_stop_machine(self):
        from core.state_machine import AdvancedStateMachine, State, StateType

        machine = AdvancedStateMachine()
        state = State(name="idle", state_type=StateType.SIMPLE)
        machine.add_state(state)

        await machine.start("idle")
        await machine.stop()

        assert machine._running is False

    def test_get_metrics(self):
        from core.state_machine import AdvancedStateMachine

        machine = AdvancedStateMachine()

        metrics = machine.get_metrics()
        assert "name" in metrics
        assert "state_count" in metrics
        assert "transition_count" in metrics


class TestPentestStateMachine:
    """Test PentestStateMachine class"""

    def test_pentest_machine_creation(self):
        from core.state_machine import PentestStateMachine

        machine = PentestStateMachine()
        assert machine.name == "PentestStateMachine"
        assert "idle" in machine.states
        assert "reconnaissance" in machine.states

    def test_pentest_states_setup(self):
        from core.state_machine import PentestStateMachine, StateType

        machine = PentestStateMachine()

        idle_state = machine.states["idle"]
        assert idle_state.state_type == StateType.SIMPLE

        # reporting state is a simple state in this implementation
        final_state = machine.states["reporting"]
        assert final_state.state_type == StateType.SIMPLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
