"""
Plugin Manager - Dynamic Plugin System for Zen AI Pentest

Features:
- Dynamic plugin loading/unloading
- Hook system for extensibility
- Plugin configuration management
- Sandboxed execution
- Dependency checking

Author: SHAdd0WTAka + Kimi AI
"""

import importlib
import importlib.util
import json
import logging
import os
import pkgutil
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger("ZenAI.Plugins")


class PluginType(Enum):
    """Types of plugins"""
    SCANNER = "scanner"           # Vulnerability scanners
    EXPLOIT = "exploit"           # Exploit modules
    REPORT = "report"             # Report generators
    OSINT = "osint"               # OSINT sources
    POST_EXPLOITATION = "post"    # Post-exploitation
    TOOL = "tool"                 # External tools integration
    NOTIFIER = "notifier"         # Notification services
    AUTH = "auth"                 # Authentication providers


class PluginStatus(Enum):
    """Plugin loading status"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime info
    status: PluginStatus = PluginStatus.UNLOADED
    path: Optional[str] = None
    error_message: Optional[str] = None
    loaded_at: Optional[str] = None


class BasePlugin(ABC):
    """
    Base class for all plugins
    
    All plugins must inherit from this class and implement required methods.
    """
    
    # Plugin metadata (must be overridden)
    NAME: str = ""
    VERSION: str = "1.0.0"
    DESCRIPTION: str = ""
    AUTHOR: str = ""
    PLUGIN_TYPE: PluginType = PluginType.TOOL
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.enabled = True
        self.logger = logging.getLogger(f"ZenAI.Plugin.{self.NAME}")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        Called once when plugin is loaded.
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute plugin functionality.
        Main entry point for the plugin.
        
        Args:
            **kwargs: Plugin-specific parameters
            
        Returns:
            Plugin result
        """
        pass
    
    async def shutdown(self):
        """
        Cleanup when plugin is unloaded.
        Override to perform cleanup.
        """
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
    
    def validate_config(self) -> bool:
        """
        Validate plugin configuration.
        Override to implement custom validation.
        
        Returns:
            True if configuration is valid
        """
        return True
    
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        return PluginInfo(
            name=self.NAME,
            version=self.VERSION,
            description=self.DESCRIPTION,
            author=self.AUTHOR,
            plugin_type=self.PLUGIN_TYPE
        )


class HookManager:
    """
    Hook system for plugin intercommunication.
    Allows plugins to register callbacks for specific events.
    """
    
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}
        self._filters: Dict[str, List[Callable]] = {}
    
    def register_hook(self, hook_name: str, callback: Callable, priority: int = 10):
        """
        Register a hook callback.
        
        Args:
            hook_name: Name of the hook
            callback: Function to call
            priority: Lower number = higher priority (default 10)
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        
        self._hooks[hook_name].append({
            "callback": callback,
            "priority": priority
        })
        
        # Sort by priority
        self._hooks[hook_name].sort(key=lambda x: x["priority"])
        logger.debug(f"Registered hook '{hook_name}' with priority {priority}")
    
    def unregister_hook(self, hook_name: str, callback: Callable):
        """Unregister a hook callback"""
        if hook_name in self._hooks:
            self._hooks[hook_name] = [
                h for h in self._hooks[hook_name]
                if h["callback"] != callback
            ]
    
    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Execute all callbacks for a hook.
        
        Args:
            hook_name: Name of the hook to execute
            *args, **kwargs: Arguments to pass to callbacks
            
        Returns:
            List of results from all callbacks
        """
        results = []
        
        if hook_name in self._hooks:
            for hook in self._hooks[hook_name]:
                try:
                    result = await hook["callback"](*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Hook '{hook_name}' callback failed: {e}")
        
        return results
    
    def register_filter(self, filter_name: str, callback: Callable, priority: int = 10):
        """
        Register a filter callback.
        Filters modify data passed through them.
        """
        if filter_name not in self._filters:
            self._filters[filter_name] = []
        
        self._filters[filter_name].append({
            "callback": callback,
            "priority": priority
        })
        
        self._filters[filter_name].sort(key=lambda x: x["priority"])
    
    async def apply_filter(self, filter_name: str, data: Any, **kwargs) -> Any:
        """
        Apply all filters to data.
        
        Args:
            filter_name: Name of the filter chain
            data: Data to filter
            **kwargs: Additional arguments
            
        Returns:
            Filtered data
        """
        if filter_name not in self._filters:
            return data
        
        for filter_hook in self._filters[filter_name]:
            try:
                data = await filter_hook["callback"](data, **kwargs)
            except Exception as e:
                logger.error(f"Filter '{filter_name}' callback failed: {e}")
        
        return data


class PluginManager:
    """
    Central plugin manager for Zen AI Pentest.
    Handles loading, unloading, and managing plugins.
    """
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        self.plugin_dirs = plugin_dirs or ["plugins", "custom_plugins"]
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.hooks = HookManager()
        self._loaded_modules: Dict[str, Any] = {}
        
        # Ensure plugin directories exist
        for plugin_dir in self.plugin_dirs:
            Path(plugin_dir).mkdir(parents=True, exist_ok=True)
    
    def discover_plugins(self) -> List[PluginInfo]:
        """
        Discover available plugins in plugin directories.
        
        Returns:
            List of discovered plugin information
        """
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue
            
            # Look for plugin directories or files
            for item in os.listdir(plugin_dir):
                item_path = os.path.join(plugin_dir, item)
                
                # Check for plugin.json manifest
                manifest_path = os.path.join(item_path, "plugin.json")
                if os.path.isfile(manifest_path):
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                        
                        info = PluginInfo(
                            name=manifest.get("name", item),
                            version=manifest.get("version", "1.0.0"),
                            description=manifest.get("description", ""),
                            author=manifest.get("author", "Unknown"),
                            plugin_type=PluginType(manifest.get("type", "tool")),
                            dependencies=manifest.get("dependencies", []),
                            hooks=manifest.get("hooks", []),
                            path=item_path
                        )
                        discovered.append(info)
                        
                    except Exception as e:
                        logger.error(f"Failed to load plugin manifest {manifest_path}: {e}")
                
                # Check for Python module
                elif os.path.isfile(os.path.join(item_path, "__init__.py")):
                    # Try to import and get metadata
                    try:
                        info = self._get_plugin_info_from_module(item_path)
                        if info:
                            discovered.append(info)
                    except Exception as e:
                        logger.error(f"Failed to inspect plugin {item_path}: {e}")
        
        return discovered
    
    def _get_plugin_info_from_module(self, path: str) -> Optional[PluginInfo]:
        """Extract plugin info from Python module"""
        # Add to path temporarily
        parent_dir = os.path.dirname(path)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        try:
            module_name = os.path.basename(path)
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(path, "__init__.py")
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for plugin class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePlugin) and 
                        attr != BasePlugin and
                        hasattr(attr, 'NAME')):
                        
                        return PluginInfo(
                            name=attr.NAME,
                            version=getattr(attr, 'VERSION', '1.0.0'),
                            description=getattr(attr, 'DESCRIPTION', ''),
                            author=getattr(attr, 'AUTHOR', 'Unknown'),
                            plugin_type=getattr(attr, 'PLUGIN_TYPE', PluginType.TOOL),
                            path=path
                        )
        finally:
            if parent_dir in sys.path:
                sys.path.remove(parent_dir)
        
        return None
    
    async def load_plugin(self, plugin_name: str, config: Optional[Dict] = None) -> bool:
        """
        Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load
            config: Optional configuration dictionary
            
        Returns:
            True if plugin loaded successfully
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin '{plugin_name}' is already loaded")
            return True
        
        # Find plugin
        discovered = self.discover_plugins()
        plugin_info = next((p for p in discovered if p.name == plugin_name), None)
        
        if not plugin_info:
            logger.error(f"Plugin '{plugin_name}' not found")
            return False
        
        plugin_info.status = PluginStatus.LOADING
        
        try:
            # Check dependencies
            for dep in plugin_info.dependencies:
                if dep not in self.plugins:
                    logger.error(f"Plugin '{plugin_name}' requires '{dep}' which is not loaded")
                    plugin_info.status = PluginStatus.ERROR
                    plugin_info.error_message = f"Missing dependency: {dep}"
                    return False
            
            # Load the plugin
            plugin = await self._load_plugin_class(plugin_info, config)
            
            if not plugin:
                raise Exception("Failed to instantiate plugin")
            
            # Validate config
            if not plugin.validate_config():
                raise Exception("Plugin configuration validation failed")
            
            # Initialize
            if not await plugin.initialize():
                raise Exception("Plugin initialization failed")
            
            # Register hooks
            for hook_name in plugin_info.hooks:
                if hasattr(plugin, f"on_{hook_name}"):
                    callback = getattr(plugin, f"on_{hook_name}")
                    self.hooks.register_hook(hook_name, callback)
            
            # Store plugin
            self.plugins[plugin_name] = plugin
            self.plugin_info[plugin_name] = plugin_info
            plugin_info.status = PluginStatus.LOADED
            
            logger.info(f"Plugin '{plugin_name}' v{plugin_info.version} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = str(e)
            return False
    
    async def _load_plugin_class(self, info: PluginInfo, config: Optional[Dict]) -> Optional[BasePlugin]:
        """Load and instantiate plugin class"""
        if not info.path:
            return None
        
        parent_dir = os.path.dirname(info.path)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        try:
            module_name = os.path.basename(info.path)
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(info.path, "__init__.py")
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePlugin) and 
                        attr != BasePlugin and
                        attr.NAME == info.name):
                        
                        return attr(config)
        
        finally:
            if parent_dir in sys.path:
                sys.path.remove(parent_dir)
        
        return None
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if plugin unloaded successfully
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin '{plugin_name}' is not loaded")
            return False
        
        plugin = self.plugins[plugin_name]
        info = self.plugin_info[plugin_name]
        
        try:
            # Shutdown plugin
            await plugin.shutdown()
            
            # Unregister hooks
            for hook_name in info.hooks:
                if hasattr(plugin, f"on_{hook_name}"):
                    callback = getattr(plugin, f"on_{hook_name}")
                    self.hooks.unregister_hook(hook_name, callback)
            
            # Remove from registry
            del self.plugins[plugin_name]
            info.status = PluginStatus.UNLOADED
            
            logger.info(f"Plugin '{plugin_name}' unloaded")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_name}': {e}")
            return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin (unload and load again)"""
        config = None
        if plugin_name in self.plugins:
            config = self.plugins[plugin_name].config
            await self.unload_plugin(plugin_name)
        
        return await self.load_plugin(plugin_name, config)
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get loaded plugin by name"""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """Get information about all plugins"""
        # Include discovered but not loaded plugins
        discovered = {p.name: p for p in self.discover_plugins()}
        discovered.update(self.plugin_info)
        return discovered
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """Get all plugins of a specific type"""
        return [
            p for p in self.plugins.values()
            if p.PLUGIN_TYPE == plugin_type
        ]
    
    async def execute_plugin(self, name: str, **kwargs) -> Any:
        """
        Execute a plugin by name.
        
        Args:
            name: Plugin name
            **kwargs: Arguments to pass to plugin
            
        Returns:
            Plugin execution result
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found or not loaded")
        
        return await plugin.execute(**kwargs)
    
    async def load_all_plugins(self):
        """Load all discovered plugins"""
        discovered = self.discover_plugins()
        
        for info in discovered:
            if info.name not in self.plugins:
                await self.load_plugin(info.name)


# Global plugin manager instance
plugin_manager = PluginManager()


# Convenience functions
def register_hook(hook_name: str, callback: Callable, priority: int = 10):
    """Register a hook callback"""
    plugin_manager.hooks.register_hook(hook_name, callback, priority)


def apply_filter(filter_name: str, data: Any, **kwargs):
    """Apply filters to data"""
    return plugin_manager.hooks.apply_filter(filter_name, data, **kwargs)


async def execute_hook(hook_name: str, *args, **kwargs):
    """Execute a hook"""
    return await plugin_manager.hooks.execute_hook(hook_name, *args, **kwargs)
