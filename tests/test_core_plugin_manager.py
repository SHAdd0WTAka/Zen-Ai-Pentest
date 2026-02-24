"""
Tests for core/plugin_manager.py - Plugin Management System

Comprehensive tests for the PluginManager, HookManager, and BasePlugin classes.
"""

import json
import os
import shutil
import tempfile

import pytest

from core.plugin_manager import (
    BasePlugin,
    HookManager,
    PluginInfo,
    PluginManager,
    PluginStatus,
    PluginType,
    apply_filter,
    execute_hook,
    register_hook,
)
from core.plugin_manager import plugin_manager as global_plugin_manager

# ==================== Test Fixtures ====================


@pytest.fixture
def temp_plugin_dir():
    """Create a temporary plugin directory"""
    temp_dir = tempfile.mkdtemp(prefix="test_plugins_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def hook_manager():
    """Create a fresh HookManager instance"""
    return HookManager()


@pytest.fixture
def plugin_manager(temp_plugin_dir):
    """Create a fresh PluginManager instance"""
    return PluginManager(plugin_dirs=[temp_plugin_dir])


class SampleTestPlugin(BasePlugin):
    """Test plugin implementation"""

    NAME = "test_plugin"
    VERSION = "1.0.0"
    DESCRIPTION = "A test plugin"
    AUTHOR = "Test Author"
    PLUGIN_TYPE = PluginType.TOOL

    async def initialize(self) -> bool:
        return True

    async def execute(self, **kwargs) -> dict:
        return {"status": "success", "plugin": self.NAME, "args": kwargs}


class FailingInitPlugin(BasePlugin):
    """Plugin that fails initialization"""

    NAME = "failing_init_plugin"
    VERSION = "1.0.0"
    PLUGIN_TYPE = PluginType.TOOL

    async def initialize(self) -> bool:
        raise Exception("Initialization failed")

    async def execute(self, **kwargs) -> dict:
        return {}


class FailingExecutePlugin(BasePlugin):
    """Plugin that fails execution"""

    NAME = "failing_execute_plugin"
    VERSION = "1.0.0"
    PLUGIN_TYPE = PluginType.TOOL

    async def initialize(self) -> bool:
        return True

    async def execute(self, **kwargs) -> dict:
        raise Exception("Execution failed")


class ConfigurablePlugin(BasePlugin):
    """Plugin with configuration"""

    NAME = "configurable_plugin"
    VERSION = "2.0.0"
    PLUGIN_TYPE = PluginType.SCANNER

    def validate_config(self) -> bool:
        required = self.config.get("required_key")
        return required is not None

    async def initialize(self) -> bool:
        if not self.validate_config():
            raise ValueError("Missing required_key")
        return True

    async def execute(self, **kwargs) -> dict:
        return {"config": self.config}


class HookPlugin(BasePlugin):
    """Plugin with hooks"""

    NAME = "hook_plugin"
    VERSION = "1.0.0"
    PLUGIN_TYPE = PluginType.NOTIFIER
    HOOKS = ["pre_scan", "post_scan"]

    async def on_pre_scan(self, target: str) -> str:
        return f"Pre-scan hook: {target}"

    async def on_post_scan(self, target: str, results: dict) -> dict:
        return {"hook": "post_scan", "target": target, "results": results}

    async def initialize(self) -> bool:
        return True

    async def execute(self, **kwargs) -> dict:
        return {}


# ==================== HookManager Tests ====================


class TestHookManager:
    """Test HookManager functionality"""

    @pytest.mark.asyncio
    async def test_register_single_hook(self, hook_manager):
        """Test registering a single hook"""

        async def callback(data: str) -> str:
            return f"processed_{data}"

        hook_manager.register_hook("test_hook", callback, priority=5)

        assert "test_hook" in hook_manager._hooks
        assert len(hook_manager._hooks["test_hook"]) == 1

    @pytest.mark.asyncio
    async def test_register_multiple_hooks_same_name(self, hook_manager):
        """Test registering multiple hooks with same name"""

        async def callback1(data: str) -> str:
            return f"cb1_{data}"

        async def callback2(data: str) -> str:
            return f"cb2_{data}"

        hook_manager.register_hook("multi_hook", callback1, priority=10)
        hook_manager.register_hook("multi_hook", callback2, priority=5)

        # Should be sorted by priority
        assert hook_manager._hooks["multi_hook"][0]["priority"] == 5
        assert hook_manager._hooks["multi_hook"][1]["priority"] == 10

    @pytest.mark.asyncio
    async def test_execute_hook(self, hook_manager):
        """Test executing a registered hook"""

        async def callback(data: str) -> str:
            return f"processed_{data}"

        hook_manager.register_hook("test_hook", callback)
        results = await hook_manager.execute_hook("test_hook", "data")

        assert len(results) == 1
        assert results[0] == "processed_data"

    @pytest.mark.asyncio
    async def test_execute_hook_multiple_callbacks(self, hook_manager):
        """Test executing hook with multiple callbacks"""
        results_list = []

        async def callback1(data: str):
            results_list.append("cb1")
            return "result1"

        async def callback2(data: str):
            results_list.append("cb2")
            return "result2"

        hook_manager.register_hook("multi", callback1, priority=1)
        hook_manager.register_hook("multi", callback2, priority=2)

        results = await hook_manager.execute_hook("multi", "test")

        assert len(results) == 2
        # Priority order: callback1 should be first
        assert results_list == ["cb1", "cb2"]

    @pytest.mark.asyncio
    async def test_execute_hook_not_found(self, hook_manager):
        """Test executing non-existent hook"""
        results = await hook_manager.execute_hook("nonexistent", "data")
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_hook_callback_exception(self, hook_manager):
        """Test that hook execution continues despite callback exception"""

        async def failing_callback(data: str):
            raise Exception("Hook failed")

        async def good_callback(data: str):
            return "success"

        hook_manager.register_hook("test", failing_callback)
        hook_manager.register_hook("test", good_callback)

        results = await hook_manager.execute_hook("test", "data")

        assert len(results) == 1
        assert results[0] == "success"

    @pytest.mark.asyncio
    async def test_unregister_hook(self, hook_manager):
        """Test unregistering a hook callback"""

        async def callback(data: str):
            return "result"

        hook_manager.register_hook("test", callback)
        assert len(hook_manager._hooks["test"]) == 1

        hook_manager.unregister_hook("test", callback)
        assert len(hook_manager._hooks["test"]) == 0

    @pytest.mark.asyncio
    async def test_filter_registration(self, hook_manager):
        """Test registering a filter"""

        async def add_prefix(data: str, **kwargs) -> str:
            return f"prefix_{data}"

        hook_manager.register_filter("test_filter", add_prefix)

        assert "test_filter" in hook_manager._filters

    @pytest.mark.asyncio
    async def test_apply_filter(self, hook_manager):
        """Test applying filters"""

        async def add_prefix(data: str, **kwargs) -> str:
            return f"prefix_{data}"

        async def add_suffix(data: str, **kwargs) -> str:
            return f"{data}_suffix"

        hook_manager.register_filter("format", add_prefix, priority=1)
        hook_manager.register_filter("format", add_suffix, priority=2)

        result = await hook_manager.apply_filter("format", "data")

        # prefix_ applied first, then _suffix
        assert result == "prefix_data_suffix"

    @pytest.mark.asyncio
    async def test_apply_filter_not_found(self, hook_manager):
        """Test applying non-existent filter"""
        result = await hook_manager.apply_filter("nonexistent", "data")
        assert result == "data"

    @pytest.mark.asyncio
    async def test_apply_filter_exception_handling(self, hook_manager):
        """Test filter execution with exception"""

        async def failing_filter(data: str, **kwargs):
            raise Exception("Filter failed")

        async def good_filter(data: str, **kwargs):
            return f"good_{data}"

        hook_manager.register_filter("test", failing_filter)
        hook_manager.register_filter("test", good_filter)

        result = await hook_manager.apply_filter("test", "data")

        # Should return data from good_filter
        assert result == "good_data"


# ==================== PluginManager Tests ====================


class TestPluginManagerInitialization:
    """Test PluginManager initialization"""

    def test_default_initialization(self):
        """Test default plugin manager creation"""
        pm = PluginManager()
        assert pm.plugin_dirs == ["plugins", "custom_plugins"]
        assert pm.plugins == {}
        assert pm.plugin_info == {}

    def test_custom_directories(self, temp_plugin_dir):
        """Test plugin manager with custom directories"""
        pm = PluginManager(plugin_dirs=[temp_plugin_dir])
        assert temp_plugin_dir in pm.plugin_dirs

    def test_directory_creation(self, temp_plugin_dir):
        """Test that plugin directories are created"""
        new_dir = os.path.join(temp_plugin_dir, "new_plugins")
        PluginManager(plugin_dirs=[new_dir])
        assert os.path.exists(new_dir)


class TestPluginDiscovery:
    """Test plugin discovery functionality"""

    def test_discover_empty_directory(self, plugin_manager):
        """Test discovery with empty plugin directory"""
        discovered = plugin_manager.discover_plugins()
        assert discovered == []

    def test_discover_plugin_from_manifest(
        self, plugin_manager, temp_plugin_dir
    ):
        """Test discovering plugin from plugin.json manifest"""
        plugin_path = os.path.join(temp_plugin_dir, "test_plugin")
        os.makedirs(plugin_path)

        manifest = {
            "name": "manifest_plugin",
            "version": "1.0.0",
            "description": "Test plugin from manifest",
            "author": "Test",
            "type": "scanner",
            "dependencies": [],
            "hooks": ["pre_scan"],
        }

        with open(os.path.join(plugin_path, "plugin.json"), "w") as f:
            json.dump(manifest, f)

        discovered = plugin_manager.discover_plugins()

        assert len(discovered) == 1
        assert discovered[0].name == "manifest_plugin"
        assert discovered[0].plugin_type == PluginType.SCANNER

    def test_discover_multiple_plugins(self, plugin_manager, temp_plugin_dir):
        """Test discovering multiple plugins"""
        for i in range(3):
            plugin_path = os.path.join(temp_plugin_dir, f"plugin_{i}")
            os.makedirs(plugin_path)
            manifest = {
                "name": f"plugin_{i}",
                "version": "1.0.0",
                "type": "tool",
            }
            with open(os.path.join(plugin_path, "plugin.json"), "w") as f:
                json.dump(manifest, f)

        discovered = plugin_manager.discover_plugins()

        assert len(discovered) == 3

    def test_discover_invalid_manifest(self, plugin_manager, temp_plugin_dir):
        """Test discovery with invalid manifest"""
        plugin_path = os.path.join(temp_plugin_dir, "bad_plugin")
        os.makedirs(plugin_path)

        with open(os.path.join(plugin_path, "plugin.json"), "w") as f:
            f.write("invalid json")

        discovered = plugin_manager.discover_plugins()
        assert discovered == []


class TestPluginLoading:
    """Test plugin loading functionality"""

    @pytest.mark.asyncio
    async def test_load_plugin_from_class(self, plugin_manager):
        """Test loading a plugin class directly"""
        # Create a simple plugin module
        plugin = SampleTestPlugin()
        plugin_manager.plugins["test_plugin"] = plugin
        plugin_manager.plugin_info["test_plugin"] = plugin.get_info()

        assert "test_plugin" in plugin_manager.plugins

    @pytest.mark.asyncio
    async def test_load_nonexistent_plugin(self, plugin_manager):
        """Test loading a plugin that doesn't exist"""
        result = await plugin_manager.load_plugin("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_load_plugin_already_loaded(self, plugin_manager):
        """Test loading an already loaded plugin"""
        plugin = SampleTestPlugin()
        plugin_manager.plugins["test_plugin"] = plugin

        result = await plugin_manager.load_plugin("test_plugin")
        assert result is True  # Returns True if already loaded

    @pytest.mark.asyncio
    async def test_load_plugin_missing_dependency(
        self, plugin_manager, temp_plugin_dir
    ):
        """Test loading plugin with missing dependency"""
        plugin_path = os.path.join(temp_plugin_dir, "dependent_plugin")
        os.makedirs(plugin_path)

        manifest = {
            "name": "dependent_plugin",
            "version": "1.0.0",
            "type": "tool",
            "dependencies": ["nonexistent_dep"],
        }

        with open(os.path.join(plugin_path, "plugin.json"), "w") as f:
            json.dump(manifest, f)

        result = await plugin_manager.load_plugin("dependent_plugin")
        assert result is False

    @pytest.mark.asyncio
    async def test_load_all_plugins(self, plugin_manager, temp_plugin_dir):
        """Test loading all discovered plugins"""
        # Create test plugin with manifest
        plugin_path = os.path.join(temp_plugin_dir, "auto_plugin")
        os.makedirs(plugin_path)

        # Note: This test is limited since we can't easily create
        # a full Python module dynamically
        plugin_manager.discover_plugins()

        # Should not crash even with empty discovery
        await plugin_manager.load_all_plugins()


class TestPluginExecution:
    """Test plugin execution"""

    @pytest.mark.asyncio
    async def test_execute_loaded_plugin(self, plugin_manager):
        """Test executing a loaded plugin"""
        plugin = SampleTestPlugin()
        plugin_manager.plugins["test_plugin"] = plugin

        result = await plugin_manager.execute_plugin(
            "test_plugin", arg1="value1"
        )

        assert result["status"] == "success"
        assert result["plugin"] == "test_plugin"
        assert result["args"]["arg1"] == "value1"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_plugin(self, plugin_manager):
        """Test executing non-existent plugin"""
        with pytest.raises(ValueError, match="not found"):
            await plugin_manager.execute_plugin("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_plugin_directly(self):
        """Test calling execute on plugin directly"""
        plugin = SampleTestPlugin()
        result = await plugin.execute(test_param=True)

        assert result["status"] == "success"


class TestPluginManagement:
    """Test plugin management operations"""

    def test_get_plugin(self, plugin_manager):
        """Test getting a plugin by name"""
        plugin = SampleTestPlugin()
        plugin_manager.plugins["test"] = plugin

        assert plugin_manager.get_plugin("test") == plugin
        assert plugin_manager.get_plugin("nonexistent") is None

    def test_get_all_plugins(self, plugin_manager):
        """Test getting all plugin info"""
        plugin = SampleTestPlugin()
        info = plugin.get_info()
        plugin_manager.plugin_info["test"] = info

        all_plugins = plugin_manager.get_all_plugins()

        assert "test" in all_plugins

    def test_get_plugins_by_type(self, plugin_manager):
        """Test getting plugins by type"""
        plugin1 = SampleTestPlugin()  # TOOL type
        plugin2 = ConfigurablePlugin()  # SCANNER type

        plugin_manager.plugins["tool_plugin"] = plugin1
        plugin_manager.plugins["scanner_plugin"] = plugin2

        tools = plugin_manager.get_plugins_by_type(PluginType.TOOL)
        scanners = plugin_manager.get_plugins_by_type(PluginType.SCANNER)

        assert len(tools) == 1
        assert len(scanners) == 1

    @pytest.mark.asyncio
    async def test_unload_plugin(self, plugin_manager):
        """Test unloading a plugin"""
        plugin = SampleTestPlugin()
        info = plugin.get_info()

        plugin_manager.plugins["test"] = plugin
        plugin_manager.plugin_info["test"] = info

        result = await plugin_manager.unload_plugin("test")

        assert result is True
        assert "test" not in plugin_manager.plugins

    @pytest.mark.asyncio
    async def test_unload_nonexistent_plugin(self, plugin_manager):
        """Test unloading non-existent plugin"""
        result = await plugin_manager.unload_plugin("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_reload_plugin(self, plugin_manager):
        """Test reloading a plugin"""
        # Just test that it doesn't crash - actual reload requires file system
        await plugin_manager.reload_plugin("nonexistent")
        # Will fail because plugin doesn't exist, but shouldn't crash


# ==================== BasePlugin Tests ====================


class TestBasePlugin:
    """Test BasePlugin abstract class"""

    def test_plugin_info(self):
        """Test getting plugin info"""
        plugin = SampleTestPlugin()
        info = plugin.get_info()

        assert isinstance(info, PluginInfo)
        assert info.name == "test_plugin"
        assert info.version == "1.0.0"
        assert info.plugin_type == PluginType.TOOL

    def test_plugin_config(self):
        """Test plugin configuration"""
        plugin = ConfigurablePlugin(
            config={"required_key": "value", "extra": "data"}
        )

        assert plugin.get_config("required_key") == "value"
        assert plugin.get_config("missing", "default") == "default"

    def test_set_config(self):
        """Test setting configuration values"""
        plugin = SampleTestPlugin()
        plugin.set_config("new_key", "new_value")

        assert plugin.config["new_key"] == "new_value"

    def test_config_validation(self):
        """Test configuration validation"""
        valid_plugin = ConfigurablePlugin(config={"required_key": "present"})
        invalid_plugin = ConfigurablePlugin(config={})

        assert valid_plugin.validate_config() is True
        assert invalid_plugin.validate_config() is False

    @pytest.mark.asyncio
    async def test_shutdown_default(self):
        """Test default shutdown implementation"""
        plugin = SampleTestPlugin()
        # Should not raise
        await plugin.shutdown()


# ==================== PluginType and PluginStatus Tests ====================


class TestPluginEnums:
    """Test PluginType and PluginStatus enums"""

    def test_plugin_types(self):
        """Test all plugin types exist"""
        assert PluginType.SCANNER.value == "scanner"
        assert PluginType.EXPLOIT.value == "exploit"
        assert PluginType.REPORT.value == "report"
        assert PluginType.OSINT.value == "osint"
        assert PluginType.POST_EXPLOITATION.value == "post"
        assert PluginType.TOOL.value == "tool"
        assert PluginType.NOTIFIER.value == "notifier"
        assert PluginType.AUTH.value == "auth"

    def test_plugin_statuses(self):
        """Test all plugin statuses exist"""
        assert PluginStatus.UNLOADED.value == "unloaded"
        assert PluginStatus.LOADING.value == "loading"
        assert PluginStatus.LOADED.value == "loaded"
        assert PluginStatus.ERROR.value == "error"
        assert PluginStatus.DISABLED.value == "disabled"


# ==================== PluginInfo Tests ====================


class TestPluginInfo:
    """Test PluginInfo dataclass"""

    def test_plugin_info_creation(self):
        """Test creating PluginInfo"""
        info = PluginInfo(
            name="test",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            plugin_type=PluginType.TOOL,
            dependencies=["dep1"],
            hooks=["hook1"],
        )

        assert info.name == "test"
        assert info.status == PluginStatus.UNLOADED
        assert info.dependencies == ["dep1"]
        assert info.hooks == ["hook1"]

    def test_plugin_info_defaults(self):
        """Test PluginInfo default values"""
        info = PluginInfo(
            name="test",
            version="1.0.0",
            description="",
            author="",
            plugin_type=PluginType.TOOL,
        )

        assert info.dependencies == []
        assert info.hooks == []
        assert info.config_schema == {}
        assert info.path is None


# ==================== Global Functions Tests ====================


class TestGlobalFunctions:
    """Test global convenience functions"""

    @pytest.mark.asyncio
    async def test_global_register_hook(self):
        """Test global register_hook function"""

        async def callback(data):
            return data

        # Clear any existing hooks
        global_plugin_manager.hooks._hooks.clear()

        register_hook("global_test", callback)

        assert "global_test" in global_plugin_manager.hooks._hooks

    @pytest.mark.asyncio
    async def test_global_execute_hook(self):
        """Test global execute_hook function"""

        async def callback(data):
            return f"processed_{data}"

        global_plugin_manager.hooks._hooks.clear()
        register_hook("exec_test", callback)

        results = await execute_hook("exec_test", "data")

        assert results == ["processed_data"]

    @pytest.mark.asyncio
    async def test_global_apply_filter(self):
        """Test global apply_filter function"""

        async def add_prefix(data, **kwargs):
            return f"prefix_{data}"

        global_plugin_manager.hooks._filters.clear()
        global_plugin_manager.hooks.register_filter("test_filter", add_prefix)

        result = await apply_filter("test_filter", "data")

        assert result == "prefix_data"


# ==================== Error Handling Tests ====================


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_plugin_init_failure(self):
        """Test handling plugin initialization failure"""
        plugin = FailingInitPlugin()

        with pytest.raises(Exception, match="Initialization failed"):
            await plugin.initialize()

    @pytest.mark.asyncio
    async def test_plugin_execute_failure(self):
        """Test handling plugin execution failure"""
        plugin = FailingExecutePlugin()

        with pytest.raises(Exception, match="Execution failed"):
            await plugin.execute()

    def test_abstract_plugin_instantiation(self):
        """Test that BasePlugin cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BasePlugin()

    def test_missing_abstract_methods(self):
        """Test plugin without required abstract methods"""

        class IncompletePlugin(BasePlugin):
            NAME = "incomplete"

        with pytest.raises(TypeError):
            IncompletePlugin()
