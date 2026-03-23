"""
Unit Tests for Plugin Manager
"""

import pytest

from core.plugin_manager import (
    BasePlugin,
    HookManager,
    PluginManager,
    PluginType,
)


class MockPlugin(BasePlugin):
    """Test plugin for unit tests"""

    NAME = "test_plugin"
    VERSION = "1.0.0"
    DESCRIPTION = "Test plugin"
    AUTHOR = "Test"
    PLUGIN_TYPE = PluginType.TOOL

    async def initialize(self) -> bool:
        return True

    async def execute(self, **kwargs):
        return {"status": "success", "plugin": self.NAME}


@pytest.mark.asyncio
async def test_plugin_manager_initialization():
    """Test plugin manager can be initialized"""
    manager = PluginManager(plugin_dirs=["test_plugins"])
    assert manager is not None
    assert manager.plugins == {}


@pytest.mark.asyncio
async def test_plugin_discovery():
    """Test plugin discovery"""
    manager = PluginManager()
    discovered = manager.discover_plugins()

    assert isinstance(discovered, list)


@pytest.mark.asyncio
async def test_hook_manager():
    """Test hook system"""
    hooks = HookManager()

    # Register hook
    async def test_callback(data):
        return f"processed_{data}"

    hooks.register_hook("test_hook", test_callback, priority=1)

    # Execute hook
    results = await hooks.execute_hook("test_hook", "data")

    assert len(results) == 1
    assert results[0] == "processed_data"


@pytest.mark.asyncio
async def test_filter_manager():
    """Test filter system"""
    hooks = HookManager()

    # Register filters
    async def add_prefix(data, **kwargs):
        return f"prefix_{data}"

    async def add_suffix(data, **kwargs):
        return f"{data}_suffix"

    hooks.register_filter("test_filter", add_prefix, priority=1)
    hooks.register_filter("test_filter", add_suffix, priority=2)

    # Apply filter
    result = await hooks.apply_filter("test_filter", "data")

    assert "prefix_" in result
    assert "_suffix" in result
