#!/usr/bin/env python3
"""
Zen-AI-Pentest Plugin System
Haupt-Plugin-System für das Framework

Features:
- Plugin Registry und Discovery
- Dynamisches Plugin-Loading
- Event-System für Plugin-Kommunikation
- Hook-System für Erweiterungen
- Plugin-Abhängigkeitsmanagement

Author: Plugin-System Developer
Version: 1.0.0
"""

import asyncio
import hashlib
import importlib
import importlib.util
import inspect
import json
import logging
import pkgutil
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

logger = logging.getLogger("ZenAI.PluginSystem")


class PluginState(Enum):
    """Plugin-Zustände im Lifecycle"""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"


class PluginPriority(Enum):
    """Plugin-Prioritäten für Ladereihenfolge"""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    OPTIONAL = 4


class PluginCapability(Enum):
    """Plugin-Fähigkeiten für Capability-basiertes System"""

    SCANNER = "scanner"
    EXPLOIT = "exploit"
    REPORTER = "reporter"
    ANALYZER = "analyzer"
    INTEGRATION = "integration"
    NOTIFICATION = "notification"
    AUTHENTICATION = "authentication"
    ENCRYPTION = "encryption"
    CUSTOM = "custom"


@dataclass
class PluginMetadata:
    """Plugin-Metadaten"""

    name: str
    version: str
    author: str
    description: str = ""
    license: str = "MIT"
    homepage: str = ""
    repository: str = ""
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    capabilities: List[PluginCapability] = field(default_factory=list)
    priority: PluginPriority = PluginPriority.NORMAL
    min_framework_version: str = "1.0.0"
    max_framework_version: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "dependencies": self.dependencies,
            "conflicts": self.conflicts,
            "provides": self.provides,
            "capabilities": [c.value for c in self.capabilities],
            "priority": self.priority.value,
            "min_framework_version": self.min_framework_version,
            "max_framework_version": self.max_framework_version,
            "tags": self.tags,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginMetadata":
        return cls(
            name=data["name"],
            version=data["version"],
            author=data["author"],
            description=data.get("description", ""),
            license=data.get("license", "MIT"),
            homepage=data.get("homepage", ""),
            repository=data.get("repository", ""),
            dependencies=data.get("dependencies", []),
            conflicts=data.get("conflicts", []),
            provides=data.get("provides", []),
            capabilities=[PluginCapability(c) for c in data.get("capabilities", [])],
            priority=PluginPriority(data.get("priority", 2)),
            min_framework_version=data.get("min_framework_version", "1.0.0"),
            max_framework_version=data.get("max_framework_version", ""),
            tags=data.get("tags", []),
            category=data.get("category", "general"),
        )


@dataclass
class PluginInfo:
    """Laufzeit-Informationen über ein Plugin"""

    plugin_id: str
    metadata: PluginMetadata
    state: PluginState = PluginState.DISCOVERED
    path: Optional[Path] = None
    module_name: str = ""
    instance: Optional[Any] = None
    error_message: str = ""
    load_time: Optional[datetime] = None
    init_time: Optional[datetime] = None
    hooks_registered: List[str] = field(default_factory=list)
    events_subscribed: List[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return self.state == PluginState.ACTIVE

    @property
    def has_error(self) -> bool:
        return self.state == PluginState.ERROR


class PluginEvent:
    """Event für Plugin-Kommunikation"""

    def __init__(self, event_type: str, data: Any = None, source: str = "", priority: int = 1):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.priority = priority
        self.timestamp = datetime.now()
        self.event_id = hashlib.md5(f"{event_type}:{self.timestamp.isoformat()}:{source}".encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
        }


class PluginHook:
    """Hook für Plugin-Erweiterungen"""

    def __init__(self, hook_name: str, callback: Callable, priority: int = 10, plugin_id: str = ""):
        self.hook_name = hook_name
        self.callback = callback
        self.priority = priority
        self.plugin_id = plugin_id
        self.active = True

    async def execute(self, *args, **kwargs) -> Any:
        """Hook ausführen"""
        if not self.active:
            return None

        try:
            if asyncio.iscoroutinefunction(self.callback):
                return await self.callback(*args, **kwargs)
            else:
                return self.callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Hook {self.hook_name} execution failed: {e}")
            raise


class PluginRegistry:
    """Zentrale Plugin-Registry"""

    def __init__(self):
        self._plugins: Dict[str, PluginInfo] = {}
        self._capabilities: Dict[PluginCapability, Set[str]] = defaultdict(set)
        self._hooks: Dict[str, List[PluginHook]] = defaultdict(list)
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=10)

    def register_plugin(self, plugin_info: PluginInfo) -> bool:
        """Plugin in Registry registrieren"""
        with self._lock:
            if plugin_info.plugin_id in self._plugins:
                logger.warning(f"Plugin {plugin_info.plugin_id} already registered")
                return False

            self._plugins[plugin_info.plugin_id] = plugin_info

            # Capabilities registrieren
            for cap in plugin_info.metadata.capabilities:
                self._capabilities[cap].add(plugin_info.plugin_id)

            plugin_info.state = PluginState.REGISTERED
            logger.info(f"Plugin registered: {plugin_info.plugin_id}")
            return True

    def unregister_plugin(self, plugin_id: str) -> bool:
        """Plugin aus Registry entfernen"""
        with self._lock:
            if plugin_id not in self._plugins:
                return False

            plugin_info = self._plugins[plugin_id]

            # Capabilities entfernen
            for cap in plugin_info.metadata.capabilities:
                self._capabilities[cap].discard(plugin_id)

            # Hooks entfernen
            for hook_name in list(self._hooks.keys()):
                self._hooks[hook_name] = [h for h in self._hooks[hook_name] if h.plugin_id != plugin_id]

            # Event-Handler entfernen
            for event_type in list(self._event_handlers.keys()):
                self._event_handlers[event_type] = [
                    h for h in self._event_handlers[event_type] if getattr(h, "__plugin_id__", None) != plugin_id
                ]

            del self._plugins[plugin_id]
            logger.info(f"Plugin unregistered: {plugin_id}")
            return True

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Plugin-Info abrufen"""
        with self._lock:
            return self._plugins.get(plugin_id)

    def get_plugins_by_capability(self, capability: PluginCapability) -> List[PluginInfo]:
        """Plugins nach Capability suchen"""
        with self._lock:
            plugin_ids = self._capabilities.get(capability, set())
            return [self._plugins[pid] for pid in plugin_ids if pid in self._plugins]

    def get_all_plugins(self) -> List[PluginInfo]:
        """Alle registrierten Plugins"""
        with self._lock:
            return list(self._plugins.values())

    def get_active_plugins(self) -> List[PluginInfo]:
        """Alle aktiven Plugins"""
        with self._lock:
            return [p for p in self._plugins.values() if p.is_active]

    def register_hook(self, hook: PluginHook) -> bool:
        """Hook registrieren"""
        with self._lock:
            self._hooks[hook.hook_name].append(hook)
            # Nach Priorität sortieren
            self._hooks[hook.hook_name].sort(key=lambda h: h.priority)

            # Plugin-Info aktualisieren
            if hook.plugin_id in self._plugins:
                self._plugins[hook.plugin_id].hooks_registered.append(hook.hook_name)

            return True

    def unregister_hook(self, hook_name: str, plugin_id: str) -> bool:
        """Hook deregistrieren"""
        with self._lock:
            if hook_name not in self._hooks:
                return False

            self._hooks[hook_name] = [h for h in self._hooks[hook_name] if h.plugin_id != plugin_id]
            return True

    async def execute_hooks(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Alle Hooks für einen Namen ausführen"""
        with self._lock:
            hooks = self._hooks.get(hook_name, []).copy()

        results = []
        for hook in hooks:
            try:
                result = await hook.execute(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook {hook_name} failed: {e}")

        return results

    def subscribe_event(self, event_type: str, handler: Callable, plugin_id: str = "") -> bool:
        """Event-Handler registrieren"""
        with self._lock:
            handler.__plugin_id__ = plugin_id
            self._event_handlers[event_type].append(handler)

            # Plugin-Info aktualisieren
            if plugin_id in self._plugins:
                self._plugins[plugin_id].events_subscribed.append(event_type)

            return True

    async def emit_event(self, event: PluginEvent) -> None:
        """Event an alle Handler senden"""
        with self._lock:
            handlers = self._event_handlers.get(event.event_type, []).copy()

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler for {event.event_type} failed: {e}")


class PluginDiscovery:
    """Plugin Discovery-Mechanismus"""

    PLUGIN_FILE_NAMES = ["plugin.py", "__init__.py", "zen_plugin.py"]
    PLUGIN_CONFIG_NAMES = ["plugin.json", "zen_plugin.json", "manifest.json"]

    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._discovered_paths: Set[Path] = set()

    def discover_from_directory(self, directory: Path) -> List[PluginInfo]:
        """Plugins aus Verzeichnis entdecken"""
        discovered = []

        if not directory.exists():
            logger.warning(f"Plugin directory not found: {directory}")
            return discovered

        for item in directory.iterdir():
            if item.is_dir():
                plugin_info = self._discover_plugin_directory(item)
                if plugin_info:
                    discovered.append(plugin_info)
                    self._discovered_paths.add(item)

        return discovered

    def _discover_plugin_directory(self, plugin_dir: Path) -> Optional[PluginInfo]:
        """Einzelnes Plugin-Verzeichnis analysieren"""
        # Konfiguration laden
        config_file = None
        for config_name in self.PLUGIN_CONFIG_NAMES:
            config_path = plugin_dir / config_name
            if config_path.exists():
                config_file = config_path
                break

        if not config_file:
            logger.debug(f"No plugin config found in {plugin_dir}")
            return None

        try:
            with open(config_file, "r") as f:
                config = json.load(f)

            metadata = PluginMetadata.from_dict(config)

            # Plugin-ID generieren
            plugin_id = f"{metadata.name}@{metadata.version}"

            # Plugin-Modul finden
            module_file = None
            for file_name in self.PLUGIN_FILE_NAMES:
                file_path = plugin_dir / file_name
                if file_path.exists():
                    module_file = file_path
                    break

            if not module_file:
                logger.warning(f"No plugin module found in {plugin_dir}")
                return None

            plugin_info = PluginInfo(plugin_id=plugin_id, metadata=metadata, path=plugin_dir, module_name=plugin_dir.name)

            return plugin_info

        except Exception as e:
            logger.error(f"Failed to discover plugin in {plugin_dir}: {e}")
            return None

    def discover_from_package(self, package_name: str) -> List[PluginInfo]:
        """Plugins aus Python-Paket entdecken"""
        discovered = []

        try:
            package = importlib.import_module(package_name)
            package_path = Path(package.__file__).parent

            for _, name, ispkg in pkgutil.iter_modules([str(package_path)]):
                if ispkg:
                    plugin_dir = package_path / name
                    plugin_info = self._discover_plugin_directory(plugin_dir)
                    if plugin_info:
                        discovered.append(plugin_info)

        except ImportError as e:
            logger.error(f"Failed to import package {package_name}: {e}")

        return discovered


class PluginLoader:
    """Plugin Loader für dynamisches Laden"""

    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._loaded_modules: Dict[str, Any] = {}

    async def load_plugin(self, plugin_info: PluginInfo) -> bool:
        """Plugin laden"""
        if not plugin_info.path:
            logger.error(f"Plugin {plugin_info.plugin_id} has no path")
            return False

        try:
            plugin_info.state = PluginState.LOADING

            # Modul laden
            module_name = f"zen_plugins.{plugin_info.module_name}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_info.path / "plugin.py")

            if not spec or not spec.loader:
                # Fallback zu __init__.py
                spec = importlib.util.spec_from_file_location(module_name, plugin_info.path / "__init__.py")

            if not spec or not spec.loader:
                raise ImportError(f"Cannot load module from {plugin_info.path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            self._loaded_modules[plugin_info.plugin_id] = module

            # Plugin-Klasse finden
            plugin_class = self._find_plugin_class(module)
            if plugin_class:
                plugin_info.instance = plugin_class()

            plugin_info.state = PluginState.LOADED
            plugin_info.load_time = datetime.now()

            logger.info(f"Plugin loaded: {plugin_info.plugin_id}")
            return True

        except Exception as e:
            plugin_info.state = PluginState.ERROR
            plugin_info.error_message = str(e)
            logger.error(f"Failed to load plugin {plugin_info.plugin_id}: {e}")
            return False

    def _find_plugin_class(self, module: Any) -> Optional[Type]:
        """Plugin-Klasse im Modul finden"""
        from plugin_api import BasePlugin

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
                return obj
        return None

    async def unload_plugin(self, plugin_info: PluginInfo) -> bool:
        """Plugin entladen"""
        try:
            plugin_info.state = PluginState.UNLOADING

            # Cleanup aufrufen
            if plugin_info.instance and hasattr(plugin_info.instance, "cleanup"):
                if asyncio.iscoroutinefunction(plugin_info.instance.cleanup):
                    await plugin_info.instance.cleanup()
                else:
                    plugin_info.instance.cleanup()

            # Modul entfernen
            if plugin_info.plugin_id in self._loaded_modules:
                module = self._loaded_modules[plugin_info.plugin_id]
                module_name = module.__name__
                if module_name in sys.modules:
                    del sys.modules[module_name]
                del self._loaded_modules[plugin_info.plugin_id]

            plugin_info.instance = None
            plugin_info.state = PluginState.UNLOADED

            logger.info(f"Plugin unloaded: {plugin_info.plugin_id}")
            return True

        except Exception as e:
            plugin_info.state = PluginState.ERROR
            plugin_info.error_message = str(e)
            logger.error(f"Failed to unload plugin {plugin_info.plugin_id}: {e}")
            return False


class PluginSystem:
    """Haupt-Plugin-System"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.registry = PluginRegistry()
        self.discovery = PluginDiscovery(self.registry)
        self.loader = PluginLoader(self.registry)
        self._plugin_directories: List[Path] = []
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    def add_plugin_directory(self, directory: Union[str, Path]) -> None:
        """Plugin-Verzeichnis hinzufügen"""
        path = Path(directory)
        self._plugin_directories.append(path)
        logger.info(f"Plugin directory added: {path}")

    async def discover_plugins(self) -> List[PluginInfo]:
        """Alle Plugins entdecken"""
        discovered = []

        for directory in self._plugin_directories:
            plugins = self.discovery.discover_from_directory(directory)
            discovered.extend(plugins)

        # In Registry registrieren
        for plugin_info in discovered:
            self.registry.register_plugin(plugin_info)

        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered

    async def load_plugin(self, plugin_id: str) -> bool:
        """Einzelnes Plugin laden"""
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            logger.error(f"Plugin not found: {plugin_id}")
            return False

        # Laden
        if not await self.loader.load_plugin(plugin_info):
            return False

        # Initialisieren
        plugin_info.state = PluginState.INITIALIZING

        if plugin_info.instance and hasattr(plugin_info.instance, "initialize"):
            try:
                context = PluginContext(self, plugin_info)
                if asyncio.iscoroutinefunction(plugin_info.instance.initialize):
                    await plugin_info.instance.initialize(context)
                else:
                    plugin_info.instance.initialize(context)

                plugin_info.state = PluginState.ACTIVE
                plugin_info.init_time = datetime.now()

                # Activation-Event senden
                await self.registry.emit_event(
                    PluginEvent(event_type="plugin.activated", data={"plugin_id": plugin_id}, source="plugin_system")
                )

            except Exception as e:
                plugin_info.state = PluginState.ERROR
                plugin_info.error_message = str(e)
                logger.error(f"Failed to initialize plugin {plugin_id}: {e}")
                return False
        else:
            plugin_info.state = PluginState.ACTIVE

        logger.info(f"Plugin activated: {plugin_id}")
        return True

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Plugin entladen"""
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            return False

        # Deactivation-Event senden
        await self.registry.emit_event(
            PluginEvent(event_type="plugin.deactivated", data={"plugin_id": plugin_id}, source="plugin_system")
        )

        # Entladen
        success = await self.loader.unload_plugin(plugin_info)

        if success:
            self.registry.unregister_plugin(plugin_id)

        return success

    async def load_all_plugins(self) -> Dict[str, bool]:
        """Alle Plugins laden"""
        results = {}

        # Nach Priorität sortieren
        plugins = sorted(self.registry.get_all_plugins(), key=lambda p: p.metadata.priority.value)

        for plugin_info in plugins:
            results[plugin_info.plugin_id] = await self.load_plugin(plugin_info.plugin_id)

        return results

    async def unload_all_plugins(self) -> Dict[str, bool]:
        """Alle Plugins entladen"""
        results = {}

        # In umgekehrter Reihenfolge entladen
        plugins = sorted(self.registry.get_all_plugins(), key=lambda p: p.metadata.priority.value, reverse=True)

        for plugin_info in plugins:
            results[plugin_info.plugin_id] = await self.unload_plugin(plugin_info.plugin_id)

        return results

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Plugin abrufen"""
        return self.registry.get_plugin(plugin_id)

    def get_plugins_by_capability(self, capability: PluginCapability) -> List[PluginInfo]:
        """Plugins nach Capability"""
        return self.registry.get_plugins_by_capability(capability)

    async def execute_hooks(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Hooks ausführen"""
        return await self.registry.execute_hooks(hook_name, *args, **kwargs)

    async def emit_event(self, event: PluginEvent) -> None:
        """Event senden"""
        await self.registry.emit_event(event)

    def subscribe_event(self, event_type: str, handler: Callable, plugin_id: str = "") -> None:
        """Event abonnieren"""
        self.registry.subscribe_event(event_type, handler, plugin_id)

    def register_hook(self, hook: PluginHook) -> None:
        """Hook registrieren"""
        self.registry.register_hook(hook)


class PluginContext:
    """Kontext für Plugin-Initialisierung"""

    def __init__(self, system: PluginSystem, plugin_info: PluginInfo):
        self.system = system
        self.plugin_info = plugin_info
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"ZenAI.Plugin.{plugin_info.plugin_id}")

    def register_hook(self, hook_name: str, callback: Callable, priority: int = 10) -> None:
        """Hook registrieren"""
        hook = PluginHook(hook_name=hook_name, callback=callback, priority=priority, plugin_id=self.plugin_info.plugin_id)
        self.system.register_hook(hook)

    def subscribe_event(self, event_type: str, handler: Callable) -> None:
        """Event abonnieren"""
        self.system.subscribe_event(event_type, handler, self.plugin_info.plugin_id)

    async def emit_event(self, event_type: str, data: Any = None) -> None:
        """Event senden"""
        event = PluginEvent(event_type=event_type, data=data, source=self.plugin_info.plugin_id)
        await self.system.emit_event(event)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Konfiguration abrufen"""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Konfiguration setzen"""
        self.config[key] = value


# Singleton-Instanz
def get_plugin_system() -> PluginSystem:
    """Plugin-System-Instanz abrufen"""
    return PluginSystem()


# Beispiel-Nutzung
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        system = get_plugin_system()

        # Plugin-Verzeichnis hinzufügen
        system.add_plugin_directory("./plugins")

        # Plugins entdecken
        discovered = await system.discover_plugins()
        print(f"Discovered {len(discovered)} plugins")

        # Alle Plugins laden
        results = await system.load_all_plugins()
        print(f"Load results: {results}")

        # Hooks ausführen
        results = await system.execute_hooks("test.hook", "arg1", kwarg1="value1")
        print(f"Hook results: {results}")

    asyncio.run(main())
