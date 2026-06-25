"""
Unit Tests for Memory Guard Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestMemoryGuard:
    """Test Memory Guard"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import memory_guard

        assert memory_guard is not None

    def test_memory_guard_creation(self):
        """Test memory guard creation"""
        from core.memory_guard import MemoryGuard

        guard = MemoryGuard()
        assert guard is not None


class TestMemoryGuardFeatures:
    """Test Memory Guard Features"""

    def test_memory_guard_exists(self):
        """Test memory guard exists"""
        from core.memory_guard import MemoryGuard

        guard = MemoryGuard()
        assert guard is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
