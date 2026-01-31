"""
Dependency Injection Container
Provides loose coupling and testability
"""

import inspect
import logging
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Provider:
    """Base provider class"""

    def __init__(self, factory: Callable, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs
        self._instance: Optional[Any] = None

    def get(self, container: "Container") -> Any:
        """Get instance from provider"""
        raise NotImplementedError()

    def _resolve_dependencies(self, container: "Container") -> tuple:
        """Resolve positional and keyword dependencies"""
        resolved_args = []
        for arg in self.args:
            if isinstance(arg, Provider):
                resolved_args.append(arg.get(container))
            elif isinstance(arg, str) and arg.startswith("@"):
                # Reference to another provider
                ref_name = arg[1:]
                resolved_args.append(container.get(ref_name))
            else:
                resolved_args.append(arg)

        resolved_kwargs = {}
        for key, value in self.kwargs.items():
            if isinstance(value, Provider):
                resolved_kwargs[key] = value.get(container)
            elif isinstance(value, str) and value.startswith("@"):
                ref_name = value[1:]
                resolved_kwargs[key] = container.get(ref_name)
            else:
                resolved_kwargs[key] = value

        return resolved_args, resolved_kwargs


class Singleton(Provider):
    """Singleton provider - creates instance once"""

    def get(self, container: "Container") -> Any:
        if self._instance is None:
            args, kwargs = self._resolve_dependencies(container)
            self._instance = self.factory(*args, **kwargs)
        return self._instance

    def reset(self):
        """Reset singleton instance (useful for testing)"""
        self._instance = None


class Factory(Provider):
    """Factory provider - creates new instance each time"""

    def get(self, container: "Container") -> Any:
        args, kwargs = self._resolve_dependencies(container)
        return self.factory(*args, **kwargs)


class Value(Provider):
    """Value provider - returns constant value"""

    def __init__(self, value: Any):
        self._value = value

    def get(self, container: "Container") -> Any:
        return self._value


class Container:
    """
    Dependency Injection Container

    Usage:
        container = Container()
        container.register('config', Value({'debug': True}))
        container.register('db', Singleton(Database, config='@config'))

        db = container.get('db')
    """

    def __init__(self):
        self._providers: dict[str, Provider] = {}
        self._cache: dict[str, Any] = {}

    def register(self, name: str, provider: Provider) -> "Container":
        """Register a provider"""
        self._providers[name] = provider
        return self

    def register_singleton(
        self, name: str, factory: Callable, *args, **kwargs
    ) -> "Container":
        """Register a singleton provider"""
        return self.register(name, Singleton(factory, *args, **kwargs))

    def register_factory(
        self, name: str, factory: Callable, *args, **kwargs
    ) -> "Container":
        """Register a factory provider"""
        return self.register(name, Factory(factory, *args, **kwargs))

    def register_value(self, name: str, value: Any) -> "Container":
        """Register a constant value"""
        return self.register(name, Value(value))

    def get(self, name: str) -> Any:
        """Get instance from container"""
        if name not in self._providers:
            raise KeyError(f"No provider registered for '{name}'")

        provider = self._providers[name]
        return provider.get(self)

    def has(self, name: str) -> bool:
        """Check if provider exists"""
        return name in self._providers

    def remove(self, name: str) -> "Container":
        """Remove a provider"""
        if name in self._providers:
            del self._providers[name]
        if name in self._cache:
            del self._cache[name]
        return self

    def reset(self) -> "Container":
        """Reset all singletons"""
        for provider in self._providers.values():
            if isinstance(provider, Singleton):
                provider.reset()
        self._cache.clear()
        return self

    def inject(self, func: Callable) -> Callable:
        """
        Decorator to inject dependencies based on type hints

        @container.inject
        def my_function(db: Database = inject('db')):
            pass
        """
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            for param_name, param in sig.parameters.items():
                if (
                    param_name not in bound.arguments
                    or bound.arguments[param_name] is None
                ):
                    # Try to resolve from container
                    if self.has(param_name):
                        bound.arguments[param_name] = self.get(param_name)

            return func(*bound.args, **bound.kwargs)

        return wrapper

    def create_scope(self) -> "Scope":
        """Create a new scope for request-level instances"""
        return Scope(self)


class Scope:
    """
    Request-scoped container
    Creates instances per request/scope
    """

    def __init__(self, parent: Container):
        self._parent = parent
        self._scoped: dict[str, Any] = {}

    def get(self, name: str) -> Any:
        """Get instance, preferring scoped version"""
        if name in self._scoped:
            return self._scoped[name]

        instance = self._parent.get(name)

        # If it's a scoped service, cache it
        if self._is_scoped(name):
            self._scoped[name] = instance

        return instance

    def set(self, name: str, instance: Any) -> "Scope":
        """Set scoped instance"""
        self._scoped[name] = instance
        return self

    def _is_scoped(self, name: str) -> bool:
        """Check if service is scoped"""
        # Could be configured per service
        return name.endswith("_scoped")

    def dispose(self):
        """Clean up scoped instances"""
        # Call dispose on instances if they have the method
        for instance in self._scoped.values():
            if hasattr(instance, "dispose") and callable(getattr(instance, "dispose")):
                try:
                    instance.dispose()
                except Exception as e:
                    logger.error(f"Error disposing {instance}: {e}")

        self._scoped.clear()


# Global container instance
_global_container: Optional[Container] = None


def get_container() -> Container:
    """Get global container instance"""
    global _global_container
    if _global_container is None:
        _global_container = Container()
    return _global_container


def set_container(container: Container):
    """Set global container instance"""
    global _global_container
    _global_container = container


def inject(name: str) -> Any:
    """
    Marker for dependency injection.
    Use with type hints to indicate injection point.
    """

    class InjectMarker:
        def __init__(self, dep_name: str):
            self.dep_name = dep_name

        def resolve(self) -> Any:
            return get_container().get(self.dep_name)

    return InjectMarker(name)


# Context manager for scoped operations
from contextlib import asynccontextmanager


@asynccontextmanager
async def scope():
    """Create a scoped context"""
    container = get_container()
    scope = container.create_scope()
    try:
        yield scope
    finally:
        scope.dispose()
