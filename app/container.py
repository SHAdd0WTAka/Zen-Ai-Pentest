"""
Dependency Injection Container

Manages dependencies between components using DI pattern.
"""

import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DependencyContainer:
    """
    Simple dependency injection container

    Provides:
    - Service registration
    - Lazy initialization
    - Singleton management
    - Dependency resolution

    Example:
        container = DependencyContainer()

        # Register services
        container.register_instance("config", config)
        container.register_factory("db", create_database)

        # Resolve dependencies
        db = container.resolve("db")
    """

    def __init__(self):
        self._registrations: Dict[str, Dict[str, Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}

    def register_instance(self, name: str, instance: Any) -> None:
        """
        Register a pre-created instance (singleton)

        Args:
            name: Service name
            instance: Service instance
        """
        self._singletons[name] = instance
        logger.debug(f"Registered instance: {name}")

    def register_factory(
        self, name: str, factory: Callable[[], T], singleton: bool = True
    ) -> None:
        """
        Register a factory function

        Args:
            name: Service name
            factory: Factory function
            singleton: Whether to cache the result
        """
        self._factories[name] = {"factory": factory, "singleton": singleton}
        logger.debug(f"Registered factory: {name} (singleton={singleton})")

    def register_class(
        self, name: str, cls: Type[T], singleton: bool = True, **kwargs
    ) -> None:
        """
        Register a class for automatic instantiation

        Args:
            name: Service name
            cls: Class to instantiate
            singleton: Whether to cache the instance
            **kwargs: Constructor arguments
        """

        def factory():
            return cls(**kwargs)

        self.register_factory(name, factory, singleton)

    def resolve(self, name: str) -> Any:
        """
        Resolve a dependency

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            KeyError: If service not found
        """
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]

        # Check factories
        if name in self._factories:
            reg = self._factories[name]
            instance = reg["factory"]()

            # Cache if singleton
            if reg["singleton"]:
                self._singletons[name] = instance
                del self._factories[name]  # Remove factory after first use

            return instance

        raise KeyError(f"Service not found: {name}")

    def resolve_optional(self, name: str, default: Any = None) -> Any:
        """
        Resolve a dependency with default

        Args:
            name: Service name
            default: Default value if not found

        Returns:
            Service instance or default
        """
        try:
            return self.resolve(name)
        except KeyError:
            return default

    def has(self, name: str) -> bool:
        """Check if service is registered"""
        return name in self._singletons or name in self._factories

    def remove(self, name: str) -> bool:
        """Remove a registration"""
        if name in self._singletons:
            del self._singletons[name]
            return True
        if name in self._factories:
            del self._factories[name]
            return True
        return False

    def clear(self) -> None:
        """Clear all registrations"""
        self._singletons.clear()
        self._factories.clear()

    def get_registered_names(self) -> list:
        """Get list of registered service names"""
        return list(self._singletons.keys()) + list(self._factories.keys())


class ServiceProvider:
    """
    Provides access to services via attribute access

    Example:
        services = ServiceProvider(container)
        db = services.db  # Same as container.resolve("db")
    """

    def __init__(self, container: DependencyContainer):
        self._container = container
        self._cache: Dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Get service by attribute access"""
        if name.startswith("_"):
            raise AttributeError(name)

        # Check cache
        if name in self._cache:
            return self._cache[name]

        # Resolve from container
        service = self._container.resolve_optional(name)
        if service is not None:
            self._cache[name] = service
            return service

        raise AttributeError(f"Service not found: {name}")

    def __dir__(self):
        """List available services"""
        return self._container.get_registered_names()


# Global container instance
_global_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get global dependency container"""
    global _global_container
    if _global_container is None:
        _global_container = DependencyContainer()
    return _global_container


def set_container(container: DependencyContainer) -> None:
    """Set global dependency container"""
    global _global_container
    _global_container = container


def reset_container() -> None:
    """Reset global container"""
    global _global_container
    _global_container = None
