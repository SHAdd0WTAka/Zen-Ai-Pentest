"""Smoke tests for core/plugin_manager.py"""

import pytest

from core.plugin_manager import BasePlugin, HookManager, PluginInfo, PluginManager, PluginStatus, PluginType, plugin_manager


class TestPluginType:
    def test_values(self):
        assert PluginType.SCANNER.value == "scanner"
        assert PluginType.EXPLOIT.value == "exploit"
        assert PluginType.REPORT.value == "report"


class TestPluginStatus:
    def test_values(self):
        assert PluginStatus.UNLOADED.name == "UNLOADED"
        assert PluginStatus.LOADED.name == "LOADED"
        assert PluginStatus.ERROR.name == "ERROR"


class TestPluginInfo:
    def test_defaults(self):
        info = PluginInfo(name="test", version="1.0", description="desc", author="me", plugin_type=PluginType.TOOL)
        assert info.name == "test"
        assert info.status == PluginStatus.UNLOADED
        assert info.dependencies == []

    def test_with_deps(self):
        info = PluginInfo(
            name="a", version="1", description="", author="", plugin_type=PluginType.SCANNER, dependencies=["dep1"]
        )
        assert info.dependencies == ["dep1"]


class TestHookManager:
    def test_init(self):
        hm = HookManager()
        assert hm._hooks == {}
        assert hm._filters == {}

    def test_register_unregister_hook(self):
        hm = HookManager()

        def cb():
            return None

        hm.register_hook("scan.done", cb)
        assert "scan.done" in hm._hooks
        assert len(hm._hooks["scan.done"]) == 1
        hm.unregister_hook("scan.done", cb)
        assert len(hm._hooks["scan.done"]) == 0

    def test_register_filter(self):
        hm = HookManager()

        def cb(x, **kw):
            return x

        hm.register_filter("sanitize", cb)
        assert "sanitize" in hm._filters


class TestPluginManager:
    def test_init(self):
        pm = PluginManager(plugin_dirs=["/tmp/non_existent_plugins"])
        assert pm.plugins == {}
        assert pm.plugin_info == {}
        assert isinstance(pm.hooks, HookManager)


class TestBasePlugin:
    def test_abstract(self):
        assert BasePlugin.__abstractmethods__ is not None
        assert "initialize" in BasePlugin.__abstractmethods__
        assert "execute" in BasePlugin.__abstractmethods__


class TestGlobalInstance:
    def test_plugin_manager_exists(self):
        assert isinstance(plugin_manager, PluginManager)
