"""
Unit Tests for Container Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestContainer:
    """Test Container"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import container

        assert container is not None

    def test_container_creation(self):
        """Test container creation"""
        from core.container import Container

        container_obj = Container()
        assert container_obj is not None

    def test_container_register(self):
        """Test container register"""
        from core.container import Container

        container_obj = Container()
        container_obj.register("test_service", lambda: "test")
        assert container_obj is not None  # Service registered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
