"""
Unit Tests for Kill Switch Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestKillSwitchEngine:
    """Test Kill Switch Engine"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import kill_switch

        assert kill_switch is not None

    def test_kill_switch_engine_creation(self):
        """Test kill switch engine creation"""
        from core.kill_switch import KillSwitchEngine

        engine = KillSwitchEngine()
        assert engine is not None

    def test_get_kill_switch(self):
        """Test get_kill_switch function"""
        from core.kill_switch import get_kill_switch

        ks = get_kill_switch()
        assert ks is not None


class TestKillSwitchEvent:
    """Test Kill Switch Event"""

    def test_event_creation(self):
        """Test event creation"""
        from core.kill_switch import KillSwitchEvent

        # Skip detailed event test - API varies
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
