"""Test state machine"""

import pytest


class TestStateMachine:
    """Test state machine"""

    def test_import(self):
        from core.state_machine import StateMachine

        assert StateMachine is not None

    def test_creation(self):
        from core.state_machine import StateMachine

        sm = StateMachine()
        assert sm is not None

    def test_has_add_state(self):
        from core.state_machine import StateMachine

        sm = StateMachine()
        assert hasattr(sm, "add_state")
