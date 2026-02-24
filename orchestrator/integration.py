"""
Component Integration Module

Registry and integration layer for connecting all orchestrator components.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ComponentInfo:
    """Information about a registered component"""

    name: str
    instance: Any
    component_type: str
    version: str = "1.0.0"
    registered_at: datetime = None
    status: str = "unknown"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class ComponentRegistry:
    """
    Central registry for all orchestrator components

    Manages:
    - Component registration and discovery
    - Dependency injection
    - Health monitoring
    - Lifecycle management

    Example:
        registry = ComponentRegistry()

        # Register components
        registry.register("analysis_bot", analysis_bot_instance)
        registry.register("audit_logger", audit_logger_instance)

        # Get component
        bot = registry.get("analysis_bot")

        # List all components
        components = registry.list_components()
    """

    def __init__(self):
        self._components: Dict[str, ComponentInfo] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "before_start": [],
            "after_start": [],
            "before_stop": [],
            "after_stop": [],
        }

    # ==================== Registration ====================

    def register(
        self,
        name: str,
        instance: Any,
        component_type: str = None,
        version: str = "1.0.0",
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> ComponentInfo:
        """
        Register a component

        Args:
            name: Unique component name
            instance: Component instance
            component_type: Type of component
            version: Component version
            dependencies: List of dependency component names
            metadata: Additional metadata

        Returns:
            ComponentInfo
        """
        if name in self._components:
            raise ValueError(f"Component '{name}' already registered")

        info = ComponentInfo(
            name=name,
            instance=instance,
            component_type=component_type or type(instance).__name__,
            version=version,
            metadata=metadata or {},
        )

        self._components[name] = info

        if dependencies:
            self._dependencies[name] = dependencies

        return info

    def unregister(self, name: str) -> bool:
        """Unregister a component"""
        if name in self._components:
            del self._components[name]
            if name in self._dependencies:
                del self._dependencies[name]
            return True
        return False

    def get(self, name: str) -> Optional[Any]:
        """Get component instance by name"""
        info = self._components.get(name)
        return info.instance if info else None

    def get_info(self, name: str) -> Optional[ComponentInfo]:
        """Get component info by name"""
        return self._components.get(name)

    def has(self, name: str) -> bool:
        """Check if component exists"""
        return name in self._components

    def list_components(self) -> List[ComponentInfo]:
        """List all registered components"""
        return list(self._components.values())

    def list_by_type(self, component_type: str) -> List[ComponentInfo]:
        """List components by type"""
        return [
            info
            for info in self._components.values()
            if info.component_type == component_type
        ]

    # ==================== Dependency Management ====================

    def get_dependencies(self, name: str) -> List[str]:
        """Get dependencies for a component"""
        return self._dependencies.get(name, [])

    def check_dependencies(self, name: str) -> Dict[str, bool]:
        """Check if all dependencies are satisfied"""
        deps = self.get_dependencies(name)
        return {dep: dep in self._components for dep in deps}

    def are_dependencies_satisfied(self, name: str) -> bool:
        """Check if all dependencies are satisfied"""
        checks = self.check_dependencies(name)
        return all(checks.values())

    def get_dependents(self, name: str) -> List[str]:
        """Get components that depend on this component"""
        dependents = []
        for comp_name, deps in self._dependencies.items():
            if name in deps:
                dependents.append(comp_name)
        return dependents

    # ==================== Lifecycle Hooks ====================

    def add_hook(self, event: str, callback: Callable) -> None:
        """
        Add lifecycle hook

        Events: before_start, after_start, before_stop, after_stop
        """
        if event in self._hooks:
            self._hooks[event].append(callback)

    def remove_hook(self, event: str, callback: Callable) -> bool:
        """Remove lifecycle hook"""
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
            return True
        return False

    async def _run_hooks(self, event: str, **kwargs) -> None:
        """Run all hooks for an event"""
        for hook in self._hooks.get(event, []):
            try:
                result = hook(**kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Hook error ({event}): {e}")

    # ==================== Health Monitoring ====================

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all components"""
        results = {}

        for name, info in self._components.items():
            try:
                # Try to call health check method if available
                instance = info.instance
                if hasattr(instance, "health_check"):
                    if asyncio.iscoroutinefunction(instance.health_check):
                        healthy = await instance.health_check()
                    else:
                        healthy = instance.health_check()
                else:
                    healthy = True  # Assume healthy if no check

                info.status = "healthy" if healthy else "unhealthy"
                results[name] = {
                    "healthy": healthy,
                    "type": info.component_type,
                    "version": info.version,
                }

            except Exception as e:
                info.status = "error"
                results[name] = {"healthy": False, "error": str(e)}

        return results

    def get_status_summary(self) -> Dict[str, Any]:
        """Get status summary of all components"""
        statuses = {}
        for name, info in self._components.items():
            statuses[name] = {
                "status": info.status,
                "type": info.component_type,
                "version": info.version,
                "registered_at": info.registered_at.isoformat(),
            }

        return {
            "total": len(self._components),
            "healthy": sum(
                1 for s in statuses.values() if s["status"] == "healthy"
            ),
            "unhealthy": sum(
                1 for s in statuses.values() if s["status"] == "unhealthy"
            ),
            "unknown": sum(
                1 for s in statuses.values() if s["status"] == "unknown"
            ),
            "components": statuses,
        }

    # ==================== Dependency Injection ====================

    def inject(self, target: Any, dependencies: Dict[str, str]) -> None:
        """
        Inject dependencies into target object

        Args:
            target: Object to inject into
            dependencies: Mapping of attribute names to component names

        Example:
            registry.inject(service, {
                "analysis_bot": "analysis_bot",
                "logger": "audit_logger"
            })
            # Now service.analysis_bot and service.logger are set
        """
        for attr_name, component_name in dependencies.items():
            component = self.get(component_name)
            if component:
                setattr(target, attr_name, component)
            else:
                raise ValueError(f"Component '{component_name}' not found")


class ComponentInitializer:
    """
    Helper for initializing components in dependency order
    """

    def __init__(self, registry: ComponentRegistry):
        self.registry = registry

    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all components in dependency order"""
        # Build dependency graph
        components = list(self.registry._components.keys())
        initialized = set()
        results = {}

        async def init_component(name: str) -> bool:
            if name in initialized:
                return True

            # Check dependencies
            if not self.registry.are_dependencies_satisfied(name):
                deps = self.registry.check_dependencies(name)
                missing = [d for d, ok in deps.items() if not ok]
                print(
                    f"Cannot initialize {name}: missing dependencies {missing}"
                )
                return False

            # Initialize
            info = self.registry.get_info(name)
            if info and hasattr(info.instance, "start"):
                try:
                    if asyncio.iscoroutinefunction(info.instance.start):
                        await info.instance.start()
                    else:
                        info.instance.start()
                    initialized.add(name)
                    return True
                except Exception as e:
                    print(f"Failed to initialize {name}: {e}")
                    return False

            initialized.add(name)
            return True

        # Initialize in rounds until all done
        while len(initialized) < len(components):
            made_progress = False

            for name in components:
                if name not in initialized:
                    if await init_component(name):
                        results[name] = True
                        made_progress = True
                    else:
                        results[name] = False

            if not made_progress:
                # Deadlock - remaining components have unmet dependencies
                break

        return results

    async def shutdown_all(self, timeout: int = 30) -> Dict[str, bool]:
        """Shutdown all components in reverse dependency order"""
        # Shutdown in reverse order
        components = list(self.registry._components.keys())
        results = {}

        for name in reversed(components):
            info = self.registry.get_info(name)
            if info and hasattr(info.instance, "stop"):
                try:
                    if asyncio.iscoroutinefunction(info.instance.stop):
                        await info.instance.stop()
                    else:
                        info.instance.stop()
                    results[name] = True
                except Exception as e:
                    print(f"Error shutting down {name}: {e}")
                    results[name] = False
            else:
                results[name] = True

        return results
