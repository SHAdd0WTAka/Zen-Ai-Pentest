"""Test plugin system"""

import pytest


class TestPluginSystem:
    """Test plugin system"""

    def test_import(self):
        from core.plugin_system import PluginState

        assert PluginState is not None

    def test_priority_import(self):
        from core.plugin_system import PluginPriority

        assert PluginPriority is not None

    def test_capability_import(self):
        from core.plugin_system import PluginCapability

        assert PluginCapability is not None
