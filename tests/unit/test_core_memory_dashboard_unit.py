"""
Unit Tests for Memory Dashboard Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestMemoryDashboard:
    """Test Memory Dashboard"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import memory_dashboard

        assert memory_dashboard is not None

    def test_dashboard_import(self):
        """Test dashboard import"""
        from core.memory_dashboard import MemoryDashboard

        assert MemoryDashboard is not None


class TestMemoryMetrics:
    """Test Memory Metrics"""

    def test_dashboard_exists(self):
        """Test dashboard exists"""
        from core import memory_dashboard

        assert memory_dashboard is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
