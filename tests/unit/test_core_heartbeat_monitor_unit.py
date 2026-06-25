"""
Unit Tests for Heartbeat Monitor Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestHeartbeatMonitor:
    """Test Heartbeat Monitor"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import heartbeat_monitor

        assert heartbeat_monitor is not None

    def test_heartbeat_monitor_creation(self):
        """Test heartbeat monitor creation"""
        from core.heartbeat_monitor import HeartbeatMonitor

        monitor = HeartbeatMonitor()
        assert monitor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
