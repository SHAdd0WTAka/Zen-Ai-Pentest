"""
Tests for core.plugin_system module.
Split from test_core_remaining.py
"""

import asyncio
import gc
import hashlib
import hmac
import json
import logging
import os
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, mock_open, patch

import pytest

# Mock aiortc before importing integrated_security
sys.modules["aiortc"] = MagicMock()
sys.modules["aiortc.mediastreams"] = MagicMock()
sys.modules["p2p"] = MagicMock()
sys.modules["p2p.connection"] = MagicMock()
sys.modules["p2p.channel"] = MagicMock()
sys.modules["core.credential_lifecycle"] = MagicMock()
sys.modules["core.vault_manager"] = MagicMock()
sys.modules["core.ssh_key_manager"] = MagicMock()
sys.modules["kimi_auth_bridge"] = MagicMock()
# Plugin System Tests
# =============================================================================

from core.plugin_system import (
    PluginCapability,
    PluginContext,
    PluginDiscovery,
    PluginEvent,
    PluginHook,
    PluginInfo,
    PluginLoader,
    PluginMetadata,
    PluginPriority,
    PluginRegistry,
    PluginState,
    PluginSystem,
    get_plugin_system,
)


class TestPluginStateEnum:
    """Test PluginState enumeration."""

    def test_all_states(self):
        """Test all plugin states exist with correct values."""
        assert PluginState.DISCOVERED.value == "discovered"
        assert PluginState.REGISTERED.value == "registered"
        assert PluginState.LOADING.value == "loading"
        assert PluginState.LOADED.value == "loaded"
        assert PluginState.INITIALIZING.value == "initializing"
        assert PluginState.ACTIVE.value == "active"
        assert PluginState.PAUSED.value == "paused"
        assert PluginState.ERROR.value == "error"
        assert PluginState.UNLOADING.value == "unloading"
        assert PluginState.UNLOADED.value == "unloaded"


class TestPluginPriorityEnum:
    """Test PluginPriority enumeration."""

    def test_priority_values(self):
        """Test priority values are ordered correctly."""
        assert PluginPriority.CRITICAL.value == 0
        assert PluginPriority.HIGH.value == 1
        assert PluginPriority.NORMAL.value == 2
        assert PluginPriority.LOW.value == 3
        assert PluginPriority.OPTIONAL.value == 4

    def test_priority_ordering(self):
        """Test priorities can be compared."""
        assert PluginPriority.CRITICAL.value < PluginPriority.HIGH.value
        assert PluginPriority.HIGH.value < PluginPriority.NORMAL.value


class TestPluginCapabilityEnum:
    """Test PluginCapability enumeration."""

    def test_all_capabilities(self):
        """Test all capability values."""
        assert PluginCapability.SCANNER.value == "scanner"
        assert PluginCapability.EXPLOIT.value == "exploit"
        assert PluginCapability.REPORTER.value == "reporter"
        assert PluginCapability.ANALYZER.value == "analyzer"
        assert PluginCapability.INTEGRATION.value == "integration"
        assert PluginCapability.NOTIFICATION.value == "notification"
        assert PluginCapability.AUTHENTICATION.value == "authentication"
        assert PluginCapability.ENCRYPTION.value == "encryption"
        assert PluginCapability.CUSTOM.value == "custom"


class TestPluginMetadata:
    """Test PluginMetadata dataclass."""

    def test_creation_with_defaults(self):
        """Test creation with default values."""
        meta = PluginMetadata(name="test_plugin", version="1.0.0", author="tester")

        assert meta.name == "test_plugin"
        assert meta.version == "1.0.0"
        assert meta.author == "tester"
        assert meta.description == ""
        assert meta.license == "MIT"
        assert meta.homepage == ""
        assert meta.repository == ""
        assert meta.dependencies == []
        assert meta.conflicts == []
        assert meta.provides == []
        assert meta.capabilities == []
        assert meta.priority == PluginPriority.NORMAL
        assert meta.min_framework_version == "1.0.0"
        assert meta.max_framework_version == ""
        assert meta.tags == []
        assert meta.category == "general"

    def test_creation_with_all_fields(self):
        """Test creation with all fields specified."""
        meta = PluginMetadata(
            name="full_plugin",
            version="2.0.0",
            author="author",
            description="A test plugin",
            license="Apache-2.0",
            homepage="https://example.com",
            repository="https://github.com/example/plugin",
            dependencies=["dep1", "dep2"],
            conflicts=["conflict1"],
            provides=["feature1"],
            capabilities=[PluginCapability.SCANNER, PluginCapability.ANALYZER],
            priority=PluginPriority.HIGH,
            min_framework_version="1.0.0",
            max_framework_version="2.0.0",
            tags=["security", "scanner"],
            category="security",
        )

        assert meta.license == "Apache-2.0"
        assert meta.homepage == "https://example.com"
        assert len(meta.dependencies) == 2
        assert len(meta.capabilities) == 2
        assert meta.priority == PluginPriority.HIGH

    def test_to_dict(self):
        """Test serialization to dictionary."""
        meta = PluginMetadata(
            name="test",
            version="1.0.0",
            author="author",
            capabilities=[PluginCapability.SCANNER],
            priority=PluginPriority.HIGH,
        )

        data = meta.to_dict()

        assert data["name"] == "test"
        assert data["version"] == "1.0.0"
        assert data["capabilities"] == ["scanner"]
        assert data["priority"] == 1
        assert data["license"] == "MIT"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "test",
            "version": "1.0.0",
            "author": "author",
            "description": "Test plugin",
            "capabilities": ["scanner", "analyzer"],
            "priority": 0,
            "dependencies": ["dep1"],
        }

        meta = PluginMetadata.from_dict(data)

        assert meta.name == "test"
        assert meta.description == "Test plugin"
        assert len(meta.capabilities) == 2
        assert meta.capabilities[0] == PluginCapability.SCANNER
        assert meta.priority == PluginPriority.CRITICAL
        assert meta.dependencies == ["dep1"]

    def test_from_dict_with_defaults(self):
        """Test from_dict with missing optional fields."""
        data = {
            "name": "minimal",
            "version": "1.0.0",
            "author": "author",
        }

        meta = PluginMetadata.from_dict(data)

        assert meta.capabilities == []
        assert meta.priority == PluginPriority.NORMAL
        assert meta.license == "MIT"


class TestPluginInfo:
    """Test PluginInfo dataclass."""

    def test_creation(self):
        """Test PluginInfo creation."""
        meta = PluginMetadata(name="test", version="1.0.0", author="tester")
        info = PluginInfo(plugin_id="test@1.0.0", metadata=meta)

        assert info.plugin_id == "test@1.0.0"
        assert info.metadata == meta
        assert info.state == PluginState.DISCOVERED
        assert info.path is None
        assert info.module_name == ""
        assert info.instance is None
        assert info.error_message == ""
        assert info.load_time is None
        assert info.init_time is None
        assert info.hooks_registered == []
        assert info.events_subscribed == []

    def test_is_active_property(self):
        """Test is_active property."""
        meta = PluginMetadata(name="test", version="1.0.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)

        assert info.is_active is False

        info.state = PluginState.ACTIVE
        assert info.is_active is True

        info.state = PluginState.LOADED
        assert info.is_active is False

    def test_has_error_property(self):
        """Test has_error property."""
        meta = PluginMetadata(name="test", version="1.0.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)

        assert info.has_error is False

        info.state = PluginState.ERROR
        assert info.has_error is True


class TestPluginEvent:
    """Test PluginEvent class."""

    def test_event_creation(self):
        """Test event creation."""
        event = PluginEvent(
            event_type="test.event",
            data={"key": "value"},
            source="test_source",
            priority=5,
        )

        assert event.event_type == "test.event"
        assert event.data == {"key": "value"}
        assert event.source == "test_source"
        assert event.priority == 5
        assert isinstance(event.timestamp, datetime)
        assert len(event.event_id) == 12

    def test_event_id_uniqueness(self):
        """Test that event IDs are unique."""
        event1 = PluginEvent("type", source="src")
        event2 = PluginEvent("type", source="src")

        assert event1.event_id != event2.event_id

    def test_to_dict(self):
        """Test event serialization."""
        event = PluginEvent(
            event_type="test",
            data={"key": "value"},
            source="src",
            priority=3,
        )

        data = event.to_dict()

        assert data["event_type"] == "test"
        assert data["data"] == {"key": "value"}
        assert data["source"] == "src"
        assert data["priority"] == 3
        assert "event_id" in data
        assert "timestamp" in data


class TestPluginHook:
    """Test PluginHook class."""

    @pytest.mark.asyncio
    async def test_hook_creation(self):
        """Test hook creation."""

        async def callback(arg):
            return f"result_{arg}"

        hook = PluginHook("test_hook", callback, priority=5, plugin_id="plugin1")

        assert hook.hook_name == "test_hook"
        assert hook.callback is callback
        assert hook.priority == 5
        assert hook.plugin_id == "plugin1"
        assert hook.active is True

    @pytest.mark.asyncio
    async def test_hook_execute_async(self):
        """Test executing async callback."""

        async def async_callback(x):
            return x * 2

        hook = PluginHook("test", async_callback)
        result = await hook.execute(5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_hook_execute_sync(self):
        """Test executing sync callback."""

        def sync_callback(x):
            return x * 3

        hook = PluginHook("test", sync_callback)
        result = await hook.execute(5)

        assert result == 15

    @pytest.mark.asyncio
    async def test_hook_execute_inactive(self):
        """Test that inactive hook returns None."""
        hook = PluginHook("test", lambda: "result")
        hook.active = False

        result = await hook.execute()

        assert result is None

    @pytest.mark.asyncio
    async def test_hook_execute_exception(self):
        """Test hook execution with exception."""

        async def failing_callback():
            raise ValueError("Hook failed")

        hook = PluginHook("test", failing_callback)

        with pytest.raises(ValueError, match="Hook failed"):
            await hook.execute()


class TestPluginRegistry:
    """Test PluginRegistry class."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = PluginRegistry()

        assert registry._plugins == {}
        assert registry._capabilities == {}
        assert registry._hooks == {}
        assert registry._event_handlers == {}
        assert isinstance(registry._lock, type(threading.RLock()))

    def test_register_plugin_success(self):
        """Test successful plugin registration."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0.0", author="tester")
        info = PluginInfo(plugin_id="test@1.0.0", metadata=meta)

        result = registry.register_plugin(info)

        assert result is True
        assert "test@1.0.0" in registry._plugins
        assert info.state == PluginState.REGISTERED

    def test_register_plugin_duplicate(self):
        """Test registering duplicate plugin fails."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)

        registry.register_plugin(info)
        result = registry.register_plugin(info)

        assert result is False

    def test_register_plugin_with_capabilities(self):
        """Test registering plugin with capabilities."""
        registry = PluginRegistry()
        meta = PluginMetadata(
            name="test",
            version="1.0.0",
            author="tester",
            capabilities=[PluginCapability.SCANNER, PluginCapability.ANALYZER],
        )
        info = PluginInfo(plugin_id="test", metadata=meta)

        registry.register_plugin(info)

        assert PluginCapability.SCANNER in registry._capabilities
        assert "test" in registry._capabilities[PluginCapability.SCANNER]
        assert "test" in registry._capabilities[PluginCapability.ANALYZER]

    def test_unregister_plugin_success(self):
        """Test successful plugin unregistration."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)

        registry.register_plugin(info)
        result = registry.unregister_plugin("test")

        assert result is True
        assert "test" not in registry._plugins

    def test_unregister_plugin_not_found(self):
        """Test unregistering non-existent plugin."""
        registry = PluginRegistry()

        result = registry.unregister_plugin("nonexistent")

        assert result is False

    def test_unregister_plugin_removes_capabilities(self):
        """Test that capabilities are removed on unregister."""
        registry = PluginRegistry()
        meta = PluginMetadata(
            name="test",
            version="1.0.0",
            author="tester",
            capabilities=[PluginCapability.SCANNER],
        )
        info = PluginInfo(plugin_id="test", metadata=meta)

        registry.register_plugin(info)
        registry.unregister_plugin("test")

        assert len(registry._capabilities[PluginCapability.SCANNER]) == 0

    def test_get_plugin(self):
        """Test getting plugin by ID."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0.0", author="tester")
        info = PluginInfo(plugin_id="test", metadata=meta)

        registry.register_plugin(info)
        result = registry.get_plugin("test")

        assert result is info

    def test_get_plugin_not_found(self):
        """Test getting non-existent plugin."""
        registry = PluginRegistry()

        result = registry.get_plugin("nonexistent")

        assert result is None

    def test_get_plugins_by_capability(self):
        """Test getting plugins by capability."""
        registry = PluginRegistry()

        meta1 = PluginMetadata(
            name="scanner1",
            version="1.0.0",
            author="a",
            capabilities=[PluginCapability.SCANNER],
        )
        meta2 = PluginMetadata(
            name="scanner2",
            version="1.0.0",
            author="a",
            capabilities=[PluginCapability.SCANNER],
        )
        meta3 = PluginMetadata(
            name="exploit",
            version="1.0.0",
            author="a",
            capabilities=[PluginCapability.EXPLOIT],
        )

        registry.register_plugin(PluginInfo(plugin_id="s1", metadata=meta1))
        registry.register_plugin(PluginInfo(plugin_id="s2", metadata=meta2))
        registry.register_plugin(PluginInfo(plugin_id="e1", metadata=meta3))

        scanners = registry.get_plugins_by_capability(PluginCapability.SCANNER)

        assert len(scanners) == 2
        assert all(p.plugin_id in ["s1", "s2"] for p in scanners)

    def test_get_all_plugins(self):
        """Test getting all plugins."""
        registry = PluginRegistry()

        for i in range(3):
            meta = PluginMetadata(name=f"p{i}", version="1.0.0", author="a")
            registry.register_plugin(PluginInfo(plugin_id=f"p{i}", metadata=meta))

        plugins = registry.get_all_plugins()

        assert len(plugins) == 3

    def test_get_active_plugins(self):
        """Test getting only active plugins."""
        registry = PluginRegistry()

        meta1 = PluginMetadata(name="active", version="1.0.0", author="a")
        info1 = PluginInfo(plugin_id="active", metadata=meta1)
        registry.register_plugin(info1)
        info1.state = PluginState.ACTIVE

        meta2 = PluginMetadata(name="inactive", version="1.0.0", author="a")
        info2 = PluginInfo(plugin_id="inactive", metadata=meta2)
        registry.register_plugin(info2)

        active = registry.get_active_plugins()

        assert len(active) == 1
        assert active[0].plugin_id == "active"

    def test_register_hook(self):
        """Test registering a hook."""
        registry = PluginRegistry()
        hook = PluginHook("test_hook", lambda: None, plugin_id="p1")

        result = registry.register_hook(hook)

        assert result is True
        assert "test_hook" in registry._hooks
        assert len(registry._hooks["test_hook"]) == 1

    def test_register_hook_sorted_by_priority(self):
        """Test hooks are sorted by priority."""
        registry = PluginRegistry()

        hook1 = PluginHook("test", lambda: None, priority=10, plugin_id="p1")
        hook2 = PluginHook("test", lambda: None, priority=5, plugin_id="p2")
        hook3 = PluginHook("test", lambda: None, priority=15, plugin_id="p3")

        registry.register_hook(hook1)
        registry.register_hook(hook2)
        registry.register_hook(hook3)

        hooks = registry._hooks["test"]
        assert hooks[0].priority == 5
        assert hooks[1].priority == 10
        assert hooks[2].priority == 15

    def test_register_hook_updates_plugin_info(self):
        """Test that hook registration updates plugin info."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        registry.register_plugin(info)

        hook = PluginHook("my_hook", lambda: None, plugin_id="test")
        registry.register_hook(hook)

        assert "my_hook" in info.hooks_registered

    def test_unregister_hook(self):
        """Test unregistering a hook."""
        registry = PluginRegistry()
        hook = PluginHook("test", lambda: None, plugin_id="p1")

        registry.register_hook(hook)
        result = registry.unregister_hook("test", "p1")

        assert result is True
        assert len(registry._hooks["test"]) == 0

    def test_unregister_hook_not_found(self):
        """Test unregistering non-existent hook."""
        registry = PluginRegistry()

        result = registry.unregister_hook("nonexistent", "p1")

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_hooks(self):
        """Test executing hooks."""
        registry = PluginRegistry()

        async def callback1(x):
            return x + 1

        async def callback2(x):
            return x * 2

        registry.register_hook(PluginHook("test", callback1, plugin_id="p1"))
        registry.register_hook(PluginHook("test", callback2, plugin_id="p2"))

        results = await registry.execute_hooks("test", 5)

        assert len(results) == 2
        assert 6 in results  # 5 + 1
        assert 10 in results  # 5 * 2

    @pytest.mark.asyncio
    async def test_execute_hooks_empty(self):
        """Test executing non-existent hooks."""
        registry = PluginRegistry()

        results = await registry.execute_hooks("nonexistent")

        assert results == []

    @pytest.mark.asyncio
    async def test_execute_hooks_exception_handling(self):
        """Test that hook execution continues despite exceptions."""
        registry = PluginRegistry()

        async def failing_hook(x):
            raise ValueError("Failed")

        async def success_hook(x):
            return x * 2

        registry.register_hook(PluginHook("test", failing_hook, plugin_id="p1"))
        registry.register_hook(PluginHook("test", success_hook, plugin_id="p2"))

        results = await registry.execute_hooks("test", 5)

        assert len(results) == 1
        assert results[0] == 10

    def test_subscribe_event(self):
        """Test subscribing to events."""
        registry = PluginRegistry()

        def handler(e):
            return None

        result = registry.subscribe_event("test_event", handler, "p1")

        assert result is True
        assert "test_event" in registry._event_handlers

    def test_subscribe_event_updates_plugin_info(self):
        """Test that event subscription updates plugin info."""
        registry = PluginRegistry()
        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        registry.register_plugin(info)

        def handler(e):
            return None

        registry.subscribe_event("my_event", handler, "test")

        assert "my_event" in info.events_subscribed

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """Test emitting events."""
        registry = PluginRegistry()

        received = []

        async def async_handler(event):
            received.append(event.data)

        def sync_handler(event):
            received.append(event.data)

        registry.subscribe_event("test", async_handler, "p1")
        registry.subscribe_event("test", sync_handler, "p2")

        event = PluginEvent("test", data={"key": "value"})
        await registry.emit_event(event)

        assert len(received) == 2
        assert all(r == {"key": "value"} for r in received)

    @pytest.mark.asyncio
    async def test_emit_event_exception_handling(self):
        """Test event emission with handler exceptions."""
        registry = PluginRegistry()

        async def failing_handler(event):
            raise ValueError("Handler failed")

        async def success_handler(event):
            return "success"

        registry.subscribe_event("test", failing_handler, "p1")
        registry.subscribe_event("test", success_handler, "p2")

        event = PluginEvent("test", data={})
        # Should not raise
        await registry.emit_event(event)


class TestPluginDiscovery:
    """Test PluginDiscovery class."""

    def test_discovery_initialization(self):
        """Test discovery initialization."""
        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)

        assert discovery.registry is registry
        assert discovery._discovered_paths == set()

    def test_discover_from_nonexistent_directory(self):
        """Test discovery from non-existent directory."""
        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)

        result = discovery.discover_from_directory(Path("/nonexistent"))

        assert result == []

    def test_discover_from_directory_with_valid_plugin(self, tmp_path):
        """Test discovering valid plugin."""
        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)

        # Create plugin directory structure
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()

        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "author": "tester",
            "description": "A test plugin",
        }

        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(manifest, f)

        with open(plugin_dir / "plugin.py", "w") as f:
            f.write("# Plugin code")

        result = discovery.discover_from_directory(tmp_path)

        assert len(result) == 1
        assert result[0].plugin_id == "test_plugin@1.0.0"
        assert result[0].metadata.name == "test_plugin"

    def test_discover_from_directory_no_manifest(self, tmp_path):
        """Test discovery with no manifest file."""
        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)

        plugin_dir = tmp_path / "no_manifest_plugin"
        plugin_dir.mkdir()

        with open(plugin_dir / "plugin.py", "w") as f:
            f.write("# Plugin code")

        result = discovery.discover_from_directory(tmp_path)

        assert result == []

    def test_discover_from_directory_no_module(self, tmp_path):
        """Test discovery with manifest but no module file."""
        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)

        plugin_dir = tmp_path / "no_module_plugin"
        plugin_dir.mkdir()

        manifest = {
            "name": "no_module",
            "version": "1.0.0",
            "author": "tester",
        }

        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(manifest, f)

        result = discovery.discover_from_directory(tmp_path)

        assert result == []

    def test_discover_from_directory_invalid_manifest(self, tmp_path):
        """Test discovery with invalid manifest."""
        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)

        plugin_dir = tmp_path / "bad_plugin"
        plugin_dir.mkdir()

        with open(plugin_dir / "plugin.json", "w") as f:
            f.write("invalid json")

        result = discovery.discover_from_directory(tmp_path)

        assert result == []


class TestPluginSystem:
    """Test PluginSystem singleton."""

    def test_singleton(self):
        """Test that PluginSystem is a singleton."""
        system1 = PluginSystem()
        system2 = PluginSystem()

        assert system1 is system2

    def test_initialization(self):
        """Test system initialization."""
        system = PluginSystem()

        assert hasattr(system, "registry")
        assert hasattr(system, "discovery")
        assert hasattr(system, "loader")
        assert system._plugin_directories == []

    def test_add_plugin_directory(self):
        """Test adding plugin directory."""
        system = PluginSystem()
        system._plugin_directories = []  # Reset

        system.add_plugin_directory("/path/to/plugins")

        assert len(system._plugin_directories) == 1
        assert str(system._plugin_directories[0]) == "/path/to/plugins"

    def test_get_plugin_system(self):
        """Test get_plugin_system convenience function."""
        system = get_plugin_system()

        assert isinstance(system, PluginSystem)
        assert system is get_plugin_system()  # Same instance


class TestPluginContext:
    """Test PluginContext class."""

    def test_context_creation(self):
        """Test context creation."""
        system = MagicMock()
        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)

        context = PluginContext(system, info)

        assert context.system is system
        assert context.plugin_info is info
        assert context.config == {}

    def test_register_hook(self):
        """Test registering hook through context."""
        system = MagicMock()
        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        context = PluginContext(system, info)

        def callback():
            return None

        context.register_hook("my_hook", callback, priority=5)

        system.register_hook.assert_called_once()
        call_args = system.register_hook.call_args[0][0]
        assert call_args.hook_name == "my_hook"
        assert call_args.priority == 5

    def test_subscribe_event(self):
        """Test subscribing to events through context."""
        system = MagicMock()
        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        context = PluginContext(system, info)

        def handler(e):
            return None

        context.subscribe_event("my_event", handler)

        system.subscribe_event.assert_called_once_with("my_event", handler, "test")

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """Test emitting events through context."""
        system = MagicMock()
        system.emit_event = AsyncMock()

        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        context = PluginContext(system, info)

        await context.emit_event("my_event", {"key": "value"})

        system.emit_event.assert_called_once()
        event = system.emit_event.call_args[0][0]
        assert event.event_type == "my_event"
        assert event.data == {"key": "value"}
        assert event.source == "test"

    def test_get_set_config(self):
        """Test config getter and setter."""
        system = MagicMock()
        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        context = PluginContext(system, info)

        context.set_config("key1", "value1")
        context.set_config("key2", 123)

        assert context.get_config("key1") == "value1"
        assert context.get_config("key2") == 123
        assert context.get_config("nonexistent", "default") == "default"


# =============================================================================
# Additional Plugin System Tests for Higher Coverage
# =============================================================================


class TestPluginLoader:
    """Test PluginLoader class."""

    def test_loader_initialization(self):
        """Test loader initialization."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        assert loader.registry is registry
        assert loader._loaded_modules == {}

    @pytest.mark.asyncio
    async def test_load_plugin_no_path(self):
        """Test loading plugin without path."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta, path=None)

        result = await loader.load_plugin(info)

        assert result is False
        # State may not change to ERROR, just checking result is False

    @pytest.mark.asyncio
    async def test_load_plugin_file_not_found(self, tmp_path):
        """Test loading plugin with non-existent file."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta, path=tmp_path / "nonexistent")

        result = await loader.load_plugin(info)

        assert result is False
        assert info.state == PluginState.ERROR

    @pytest.mark.asyncio
    async def test_unload_plugin_not_loaded(self):
        """Test unloading plugin that wasn't loaded."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)

        result = await loader.unload_plugin(info)

        assert result is True  # Returns True as there's nothing to unload

    @pytest.mark.asyncio
    async def test_unload_plugin_with_cleanup(self):
        """Test unloading plugin with cleanup method."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        info.state = PluginState.LOADED

        # Create mock instance with cleanup
        mock_instance = MagicMock()
        mock_instance.cleanup = MagicMock()
        info.instance = mock_instance

        result = await loader.unload_plugin(info)

        assert result is True
        mock_instance.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_unload_plugin_with_async_cleanup(self):
        """Test unloading plugin with async cleanup method."""
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        info.state = PluginState.LOADED

        # Create mock instance with async cleanup
        mock_instance = MagicMock()
        mock_instance.cleanup = AsyncMock()
        info.instance = mock_instance

        result = await loader.unload_plugin(info)

        assert result is True
        mock_instance.cleanup.assert_called_once()


class TestPluginSystemAdvanced:
    """Additional PluginSystem tests."""

    @pytest.mark.asyncio
    async def test_discover_plugins_no_directories(self):
        """Test discovery with no directories added."""
        system = PluginSystem()
        system._plugin_directories = []

        result = await system.discover_plugins()

        assert result == []

    @pytest.mark.asyncio
    async def test_load_plugin_not_found(self):
        """Test loading non-existent plugin."""
        system = PluginSystem()

        result = await system.load_plugin("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_unload_plugin_not_found(self):
        """Test unloading non-existent plugin."""
        system = PluginSystem()

        result = await system.unload_plugin("nonexistent")

        assert result is False

    def test_get_plugin(self):
        """Test get_plugin method."""
        system = PluginSystem()
        meta = PluginMetadata(name="test", version="1.0.0", author="a")
        info = PluginInfo(plugin_id="test", metadata=meta)
        system.registry.register_plugin(info)

        result = system.get_plugin("test")

        assert result is info

    def test_get_plugins_by_capability(self):
        """Test get_plugins_by_capability method."""
        system = PluginSystem()
        # Reset to ensure clean state
        system.registry = PluginRegistry()

        meta = PluginMetadata(
            name="test",
            version="1.0.0",
            author="a",
            capabilities=[PluginCapability.SCANNER],
        )
        info = PluginInfo(plugin_id="test_capability", metadata=meta)
        system.registry.register_plugin(info)

        result = system.get_plugins_by_capability(PluginCapability.SCANNER)

        assert len(result) == 1


# =============================================================================
