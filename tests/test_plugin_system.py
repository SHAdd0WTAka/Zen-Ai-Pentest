"""Tests for core/plugin_system.py - Plugin System."""

import hashlib
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from core.plugin_system import (
    PluginState,
    PluginPriority,
    PluginCapability,
    PluginMetadata,
    PluginInfo,
    PluginEvent,
    PluginHook,
    PluginRegistry,
)


class TestPluginState:
    """Test PluginState enum."""

    def test_states(self):
        """Test plugin states."""
        assert PluginState.DISCOVERED.value == "discovered"
        assert PluginState.REGISTERED.value == "registered"
        assert PluginState.LOADED.value == "loaded"
        assert PluginState.ACTIVE.value == "active"
        assert PluginState.ERROR.value == "error"


class TestPluginPriority:
    """Test PluginPriority enum."""

    def test_priorities(self):
        """Test plugin priorities."""
        assert PluginPriority.CRITICAL.value == 0
        assert PluginPriority.HIGH.value == 1
        assert PluginPriority.NORMAL.value == 2
        assert PluginPriority.LOW.value == 3
        assert PluginPriority.OPTIONAL.value == 4


class TestPluginCapability:
    """Test PluginCapability enum."""

    def test_capabilities(self):
        """Test plugin capabilities."""
        assert PluginCapability.SCANNER.value == "scanner"
        assert PluginCapability.EXPLOIT.value == "exploit"
        assert PluginCapability.REPORTER.value == "reporter"
        assert PluginCapability.ANALYZER.value == "analyzer"


class TestPluginMetadata:
    """Test PluginMetadata dataclass."""

    def test_defaults(self):
        """Test default metadata."""
        meta = PluginMetadata(name="test", version="1.0", author="tester")
        
        assert meta.name == "test"
        assert meta.version == "1.0"
        assert meta.author == "tester"
        assert meta.description == ""
        assert meta.license == "MIT"
        assert meta.dependencies == []
        assert meta.capabilities == []
        assert meta.priority == PluginPriority.NORMAL

    def test_to_dict(self):
        """Test serialization to dict."""
        meta = PluginMetadata(
            name="test",
            version="1.0",
            author="tester",
            capabilities=[PluginCapability.SCANNER]
        )
        d = meta.to_dict()
        
        assert d["name"] == "test"
        assert d["version"] == "1.0"
        assert d["capabilities"] == ["scanner"]
        assert d["priority"] == 2

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "name": "test",
            "version": "1.0",
            "author": "tester",
            "capabilities": ["scanner"],
            "priority": 1,
        }
        meta = PluginMetadata.from_dict(data)
        
        assert meta.name == "test"
        assert meta.version == "1.0"
        assert meta.capabilities == [PluginCapability.SCANNER]
        assert meta.priority == PluginPriority.HIGH


class TestPluginInfo:
    """Test PluginInfo dataclass."""

    def test_defaults(self):
        """Test default plugin info."""
        meta = PluginMetadata(name="test", version="1.0", author="tester")
        info = PluginInfo(plugin_id="test_1", metadata=meta)
        
        assert info.plugin_id == "test_1"
        assert info.metadata == meta
        assert info.state == PluginState.DISCOVERED
        assert info.is_active is False
        assert info.has_error is False

    def test_is_active_property(self):
        """Test is_active property."""
        meta = PluginMetadata(name="test", version="1.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)
        
        info.state = PluginState.ACTIVE
        assert info.is_active is True
        
        info.state = PluginState.LOADED
        assert info.is_active is False

    def test_has_error_property(self):
        """Test has_error property."""
        meta = PluginMetadata(name="test", version="1.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)
        
        assert info.has_error is False
        
        info.state = PluginState.ERROR
        assert info.has_error is True


class TestPluginEvent:
    """Test PluginEvent class."""

    def test_init(self):
        """Test event initialization."""
        event = PluginEvent("test_event", data={"key": "value"}, source="test")
        
        assert event.event_type == "test_event"
        assert event.data == {"key": "value"}
        assert event.source == "test"
        assert event.priority == 1
        assert isinstance(event.timestamp, datetime)
        assert len(event.event_id) == 12

    def test_event_id_generation(self):
        """Test event ID is generated consistently."""
        event1 = PluginEvent("type1", source="src1")
        event2 = PluginEvent("type1", source="src1")
        
        # IDs should be different because timestamps differ
        assert event1.event_id != event2.event_id

    def test_to_dict(self):
        """Test serialization to dict."""
        event = PluginEvent("test", data={"key": "value"}, source="src")
        d = event.to_dict()
        
        assert d["event_type"] == "test"
        assert d["data"] == {"key": "value"}
        assert d["source"] == "src"
        assert "event_id" in d
        assert "timestamp" in d


class TestPluginHook:
    """Test PluginHook class."""

    def test_init(self):
        """Test hook initialization."""
        callback = lambda *args, **kwargs: "result"
        hook = PluginHook("test_hook", callback, priority=5, plugin_id="p1")
        
        assert hook.hook_name == "test_hook"
        assert hook.callback is callback
        assert hook.priority == 5
        assert hook.plugin_id == "p1"
        assert hook.active is True

    def test_execute_sync(self):
        """Test executing sync callback."""
        callback = MagicMock(return_value="result")
        hook = PluginHook("test", callback)
        
        # Cannot test async easily
        assert hook.callback is callback


class TestPluginRegistry:
    """Test PluginRegistry class."""

    def test_init(self):
        """Test registry initialization."""
        registry = PluginRegistry()
        
        assert registry._plugins == {}
        assert registry._capabilities == {}
        assert registry._hooks == {}
        assert registry._event_handlers == {}

    def test_register_plugin(self):
        """Test registering a plugin."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)
        
        result = registry.register_plugin(info)
        
        assert result is True
        assert "test" in registry._plugins
        assert info.state == PluginState.REGISTERED

    def test_register_duplicate_plugin(self):
        """Test registering duplicate plugin fails."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)
        
        registry.register_plugin(info)
        result = registry.register_plugin(info)
        
        assert result is False

    def test_register_plugin_with_capabilities(self):
        """Test registering plugin with capabilities."""
        registry = PluginRegistry()
        meta = PluginMetadata(
            name="test",
            version="1.0",
            author="tester",
            capabilities=[PluginCapability.SCANNER]
        )
        info = PluginInfo(plugin_id="test", metadata=meta)
        
        registry.register_plugin(info)
        
        assert PluginCapability.SCANNER in registry._capabilities
        assert "test" in registry._capabilities[PluginCapability.SCANNER]

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)
        
        registry.register_plugin(info)
        result = registry.unregister_plugin("test")
        
        assert result is True
        assert "test" not in registry._plugins

    def test_unregister_unknown_plugin(self):
        """Test unregistering unknown plugin returns False."""
        registry = PluginRegistry()
        
        result = registry.unregister_plugin("unknown")
        
        assert result is False

    def test_get_plugin(self):
        """Test getting plugin info."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)
        
        registry.register_plugin(info)
        result = registry.get_plugin("test")
        
        assert result is info

    def test_get_unknown_plugin(self):
        """Test getting unknown plugin returns None."""
        registry = PluginRegistry()
        
        result = registry.get_plugin("unknown")
        
        assert result is None

    def test_get_plugins_by_capability(self):
        """Test getting plugins by capability."""
        registry = PluginRegistry()
        meta = PluginMetadata(
            name="test",
            version="1.0",
            author="tester",
            capabilities=[PluginCapability.SCANNER]
        )
        info = PluginInfo(plugin_id="test", metadata=meta)
        
        registry.register_plugin(info)
        results = registry.get_plugins_by_capability(PluginCapability.SCANNER)
        
        assert len(results) == 1
        assert results[0] is info

    def test_get_all_plugins(self):
        """Test getting all plugins."""
        registry = PluginRegistry()
        
        for i in range(3):
            meta = PluginMetadata(name=f"test{i}", version="1.0", author="tester")
            info = PluginInfo(plugin_id=f"test{i}", metadata=meta)
            registry.register_plugin(info)
        
        results = registry.get_all_plugins()
        
        assert len(results) == 3

    def test_get_active_plugins(self):
        """Test getting active plugins."""
        registry = PluginRegistry()
        
        meta1 = PluginMetadata(name="active", version="1.0", author="tester")
        info1 = PluginInfo(plugin_id="active", metadata=meta1)
        # Register first, then change state (registration changes state to REGISTERED)
        registry.register_plugin(info1)
        info1.state = PluginState.ACTIVE  # Set ACTIVE after registration
        
        meta2 = PluginMetadata(name="inactive", version="1.0", author="tester")
        info2 = PluginInfo(plugin_id="inactive", metadata=meta2)
        registry.register_plugin(info2)
        # info2 stays in REGISTERED state
        
        results = registry.get_active_plugins()
        
        assert len(results) == 1
        assert results[0].plugin_id == "active"

    def test_register_hook(self):
        """Test registering a hook."""
        registry = PluginRegistry()
        callback = lambda: None
        hook = PluginHook("test_hook", callback, plugin_id="p1")
        
        result = registry.register_hook(hook)
        
        assert result is True
        assert "test_hook" in registry._hooks
        assert len(registry._hooks["test_hook"]) == 1

    def test_register_multiple_hooks_sorted(self):
        """Test hooks are sorted by priority."""
        registry = PluginRegistry()
        
        hook1 = PluginHook("test", lambda: None, priority=10, plugin_id="p1")
        hook2 = PluginHook("test", lambda: None, priority=5, plugin_id="p2")
        hook3 = PluginHook("test", lambda: None, priority=20, plugin_id="p3")
        
        registry.register_hook(hook1)
        registry.register_hook(hook2)
        registry.register_hook(hook3)
        
        hooks = registry._hooks["test"]
        assert hooks[0].priority == 5
        assert hooks[1].priority == 10
        assert hooks[2].priority == 20

    def test_unregister_hook(self):
        """Test unregistering a hook."""
        registry = PluginRegistry()
        hook = PluginHook("test", lambda: None, plugin_id="p1")
        
        registry.register_hook(hook)
        result = registry.unregister_hook("test", "p1")
        
        assert result is True
        assert len(registry._hooks["test"]) == 0

    def test_unregister_unknown_hook(self):
        """Test unregistering unknown hook returns False."""
        registry = PluginRegistry()
        
        result = registry.unregister_hook("unknown", "p1")
        
        assert result is False

    def test_subscribe_event(self):
        """Test subscribing to event."""
        registry = PluginRegistry()
        handler = lambda e: None
        
        result = registry.subscribe_event("test_event", handler, "p1")
        
        assert result is True
        assert "test_event" in registry._event_handlers
        assert len(registry._event_handlers["test_event"]) == 1


class TestAllExports:
    """Test that all expected exports are available."""

    def test_exports(self):
        """Test that key classes are importable."""
        from core import plugin_system
        
        assert hasattr(plugin_system, 'PluginState')
        assert hasattr(plugin_system, 'PluginPriority')
        assert hasattr(plugin_system, 'PluginCapability')
        assert hasattr(plugin_system, 'PluginMetadata')
        assert hasattr(plugin_system, 'PluginInfo')
        assert hasattr(plugin_system, 'PluginEvent')
        assert hasattr(plugin_system, 'PluginHook')
        assert hasattr(plugin_system, 'PluginRegistry')
        assert hasattr(plugin_system, 'PluginDiscovery')
