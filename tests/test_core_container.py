"""
Tests for core/container.py - Dependency Injection Container

Comprehensive tests for Container, Provider classes, Scope, and injection utilities.
"""

import pytest
from unittest.mock import Mock

from core.container import (
    Provider,
    Singleton,
    Factory,
    Value,
    Container,
    Scope,
    get_container,
    set_container,
    inject,
    scope,
    _global_container,
)


# ==================== Test Fixtures ====================

@pytest.fixture
def fresh_container():
    """Create a fresh Container instance"""
    return Container()


@pytest.fixture
def reset_global_container():
    """Reset global container after test"""
    original = _global_container
    set_container(Container())
    yield
    set_container(original)


class SimpleService:
    """Simple service for testing"""
    def __init__(self, name: str = "default"):
        self.name = name
        self.init_count = 0


class DependentService:
    """Service with dependencies"""
    def __init__(self, simple: SimpleService):
        self.simple = simple


class CounterService:
    """Service that counts instantiations"""
    instance_count = 0

    def __init__(self):
        CounterService.instance_count += 1
        self.id = CounterService.instance_count


# ==================== Provider Tests ====================

class TestProvider:
    """Test base Provider class"""

    def test_provider_not_instantiable(self):
        """Test that Provider cannot be instantiated directly"""
        # Provider is instantiable but get() raises NotImplementedError
        provider = Provider(lambda: None, "arg")
        container = Container()
        with pytest.raises(NotImplementedError):
            provider.get(container)


class TestSingleton:
    """Test Singleton provider"""

    def test_singleton_creates_once(self, fresh_container):
        """Test singleton creates instance only once"""
        CounterService.instance_count = 0

        provider = Singleton(CounterService)
        fresh_container.register("counter", provider)

        instance1 = fresh_container.get("counter")
        instance2 = fresh_container.get("counter")

        assert instance1 is instance2
        assert CounterService.instance_count == 1
        assert instance1.id == 1

    def test_singleton_with_args(self, fresh_container):
        """Test singleton with constructor arguments"""
        provider = Singleton(SimpleService, "custom_name")
        fresh_container.register("service", provider)

        instance = fresh_container.get("service")

        assert instance.name == "custom_name"

    def test_singleton_reset(self, fresh_container):
        """Test singleton reset functionality"""
        CounterService.instance_count = 0

        provider = Singleton(CounterService)
        fresh_container.register("counter", provider)

        instance1 = fresh_container.get("counter")
        provider.reset()
        instance2 = fresh_container.get("counter")

        assert instance1 is not instance2
        assert CounterService.instance_count == 2

    def test_singleton_dependency_resolution(self, fresh_container):
        """Test singleton with dependency resolution"""
        fresh_container.register("simple", Singleton(SimpleService, "injected"))
        fresh_container.register("dependent", Singleton(DependentService, "@simple"))

        dependent = fresh_container.get("dependent")

        assert isinstance(dependent.simple, SimpleService)
        assert dependent.simple.name == "injected"


class TestFactory:
    """Test Factory provider"""

    def test_factory_creates_each_time(self, fresh_container):
        """Test factory creates new instance each time"""
        CounterService.instance_count = 0

        provider = Factory(CounterService)
        fresh_container.register("counter", provider)

        instance1 = fresh_container.get("counter")
        instance2 = fresh_container.get("counter")

        assert instance1 is not instance2
        assert CounterService.instance_count == 2

    def test_factory_with_args(self, fresh_container):
        """Test factory with constructor arguments"""
        provider = Factory(SimpleService, name="factory_name")
        fresh_container.register("service", provider)

        instance1 = fresh_container.get("service")
        instance2 = fresh_container.get("service")

        assert instance1.name == "factory_name"
        assert instance2.name == "factory_name"
        assert instance1 is not instance2


class TestValue:
    """Test Value provider"""

    def test_value_returns_constant(self, fresh_container):
        """Test value provider returns constant"""
        config = {"debug": True, "port": 8080}
        provider = Value(config)
        fresh_container.register("config", provider)

        result = fresh_container.get("config")

        assert result is config
        assert result["debug"] is True

    def test_value_with_primitive(self, fresh_container):
        """Test value provider with primitive types"""
        fresh_container.register("name", Value("test_name"))
        fresh_container.register("count", Value(42))

        assert fresh_container.get("name") == "test_name"
        assert fresh_container.get("count") == 42


# ==================== Container Tests ====================

class TestContainerRegistration:
    """Test Container registration methods"""

    def test_register_provider(self, fresh_container):
        """Test registering a provider"""
        provider = Value("test")

        result = fresh_container.register("key", provider)

        assert result is fresh_container  # Fluent interface
        assert "key" in fresh_container._providers

    def test_register_singleton(self, fresh_container):
        """Test register_singleton convenience method"""
        result = fresh_container.register_singleton("service", SimpleService)

        assert result is fresh_container
        assert isinstance(fresh_container._providers["service"], Singleton)

    def test_register_factory(self, fresh_container):
        """Test register_factory convenience method"""
        result = fresh_container.register_factory("service", SimpleService)

        assert result is fresh_container
        assert isinstance(fresh_container._providers["service"], Factory)

    def test_register_value(self, fresh_container):
        """Test register_value convenience method"""
        result = fresh_container.register_value("config", {"key": "value"})

        assert result is fresh_container
        assert isinstance(fresh_container._providers["config"], Value)


class TestContainerRetrieval:
    """Test Container retrieval methods"""

    def test_get_existing_provider(self, fresh_container):
        """Test getting registered provider"""
        fresh_container.register_value("test", "value")

        result = fresh_container.get("test")

        assert result == "value"

    def test_get_nonexistent_provider(self, fresh_container):
        """Test getting non-existent provider raises error"""
        with pytest.raises(KeyError, match="No provider registered"):
            fresh_container.get("nonexistent")

    def test_has_provider(self, fresh_container):
        """Test checking if provider exists"""
        fresh_container.register_value("exists", "value")

        assert fresh_container.has("exists") is True
        assert fresh_container.has("not_exists") is False

    def test_remove_provider(self, fresh_container):
        """Test removing a provider"""
        fresh_container.register_value("test", "value")

        result = fresh_container.remove("test")

        assert result is fresh_container
        assert fresh_container.has("test") is False

    def test_remove_nonexistent_provider(self, fresh_container):
        """Test removing non-existent provider doesn't raise"""
        result = fresh_container.remove("nonexistent")

        assert result is fresh_container


class TestContainerReset:
    """Test Container reset functionality"""

    def test_reset_singletons(self, fresh_container):
        """Test resetting all singletons"""
        CounterService.instance_count = 0

        fresh_container.register_singleton("counter", CounterService)
        instance1 = fresh_container.get("counter")

        result = fresh_container.reset()

        assert result is fresh_container
        instance2 = fresh_container.get("counter")
        assert instance1 is not instance2

    def test_reset_clears_cache(self, fresh_container):
        """Test reset clears internal cache"""
        fresh_container.register_value("test", "value")
        fresh_container._cache["cached"] = "cached_value"

        fresh_container.reset()

        assert "cached" not in fresh_container._cache


class TestContainerInjection:
    """Test Container injection decorator"""

    def test_inject_dependencies(self, fresh_container):
        """Test injecting dependencies by name"""
        fresh_container.register_value("config", {"debug": True})
        fresh_container.register_value("name", "test_service")

        @fresh_container.inject
        def my_function(config, name):
            return f"{name}: {config['debug']}"

        result = my_function()

        assert result == "test_service: True"

    def test_inject_partial_dependencies(self, fresh_container):
        """Test injecting only missing dependencies"""
        fresh_container.register_value("config", {"debug": True})

        @fresh_container.inject
        def my_function(config, extra="default"):
            return f"{config['debug']}, {extra}"

        result = my_function(extra="provided")

        assert result == "True, provided"

    def test_inject_preserves_explicit_args(self, fresh_container):
        """Test that explicit arguments are not overridden"""
        fresh_container.register_value("config", {"debug": True})

        @fresh_container.inject
        def my_function(config):
            return config

        explicit_config = {"debug": False}
        result = my_function(explicit_config)

        assert result == explicit_config


class TestDependencyResolution:
    """Test dependency resolution with @ syntax"""

    def test_resolve_positional_reference(self, fresh_container):
        """Test resolving positional dependency reference"""
        fresh_container.register_value("simple", SimpleService("ref"))
        fresh_container.register("dependent", Singleton(DependentService, "@simple"))

        result = fresh_container.get("dependent")

        assert isinstance(result.simple, SimpleService)
        assert result.simple.name == "ref"

    def test_resolve_keyword_reference(self, fresh_container):
        """Test resolving keyword dependency reference"""
        fresh_container.register_value("simple", SimpleService("kw_ref"))
        fresh_container.register("dependent", Singleton(DependentService, simple="@simple"))

        result = fresh_container.get("dependent")

        assert result.simple.name == "kw_ref"

    def test_resolve_nested_provider(self, fresh_container):
        """Test resolving nested provider references"""
        inner_provider = Value(SimpleService("inner"))
        fresh_container.register("inner", inner_provider)
        fresh_container.register("outer", Singleton(DependentService, "@inner"))

        result = fresh_container.get("outer")

        assert result.simple.name == "inner"


# ==================== Scope Tests ====================

class TestScope:
    """Test Scope functionality"""

    def test_scope_creation(self, fresh_container):
        """Test creating a scope"""
        scope_instance = fresh_container.create_scope()

        assert isinstance(scope_instance, Scope)
        assert scope_instance._parent is fresh_container

    def test_scope_get_from_parent(self, fresh_container):
        """Test getting from parent when not in scope"""
        fresh_container.register_value("test", "value")
        scope_instance = fresh_container.create_scope()

        result = scope_instance.get("test")

        assert result == "value"

    def test_scope_caches_scoped_services(self, fresh_container):
        """Test that scoped services are cached"""
        CounterService.instance_count = 0
        fresh_container.register_singleton("counter_scoped", CounterService)
        scope_instance = fresh_container.create_scope()

        instance1 = scope_instance.get("counter_scoped")
        instance2 = scope_instance.get("counter_scoped")

        assert instance1 is instance2
        assert CounterService.instance_count == 1

    def test_scope_set(self, fresh_container):
        """Test setting scoped instance"""
        scope_instance = fresh_container.create_scope()
        service = SimpleService("scoped")

        result = scope_instance.set("custom", service)

        assert result is scope_instance
        assert scope_instance.get("custom") is service

    def test_scope_is_scoped_check(self, fresh_container):
        """Test _is_scoped method"""
        scope_instance = fresh_container.create_scope()

        assert scope_instance._is_scoped("service_scoped") is True
        assert scope_instance._is_scoped("regular_service") is False

    def test_scope_dispose(self, fresh_container):
        """Test scope disposal"""
        scope_instance = fresh_container.create_scope()
        scope_instance.set("test", "value")

        scope_instance.dispose()

        assert len(scope_instance._scoped) == 0

    def test_scope_dispose_with_cleanup(self, fresh_container):
        """Test scope disposal calls dispose on items"""
        mock_service = Mock()
        mock_service.dispose = Mock()

        scope_instance = fresh_container.create_scope()
        scope_instance.set("service", mock_service)

        scope_instance.dispose()

        mock_service.dispose.assert_called_once()

    def test_scope_dispose_cleanup_error_handling(self, fresh_container):
        """Test scope disposal handles cleanup errors"""
        mock_service = Mock()
        mock_service.dispose = Mock(side_effect=Exception("Dispose failed"))

        scope_instance = fresh_container.create_scope()
        scope_instance.set("service", mock_service)

        # Should not raise
        scope_instance.dispose()


# ==================== Global Container Tests ====================

class TestGlobalContainer:
    """Test global container functions"""

    def test_get_container_creates_default(self, reset_global_container):
        """Test get_container creates default if none exists"""
        container = get_container()

        assert isinstance(container, Container)

    def test_get_container_returns_same_instance(self, reset_global_container):
        """Test get_container returns same instance"""
        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_set_container(self, reset_global_container):
        """Test setting global container"""
        new_container = Container()
        new_container.register_value("test", "new_value")

        set_container(new_container)

        assert get_container() is new_container
        assert get_container().get("test") == "new_value"


# ==================== Inject Marker Tests ====================

class TestInjectMarker:
    """Test inject marker functionality"""

    def test_inject_marker_creation(self):
        """Test creating inject marker"""
        marker = inject("service_name")

        assert marker.dep_name == "service_name"

    def test_inject_marker_resolve(self, reset_global_container):
        """Test resolving inject marker"""
        get_container().register_value("test_service", "resolved_value")

        marker = inject("test_service")
        result = marker.resolve()

        assert result == "resolved_value"


# ==================== Async Scope Tests ====================

@pytest.mark.asyncio
class TestAsyncScope:
    """Test async scope context manager"""

    async def test_scope_context_manager(self, reset_global_container):
        """Test scope as async context manager"""
        async with scope() as scope_instance:
            assert isinstance(scope_instance, Scope)

    async def test_scope_cleanup_on_exit(self, reset_global_container):
        """Test scope is cleaned up on exit"""
        scope_instance = None

        async with scope() as s:
            scope_instance = s
            s.set("test", "value")

        # Scope should be disposed
        assert len(scope_instance._scoped) == 0

    async def test_scope_exception_handling(self, reset_global_container):
        """Test scope handles exceptions"""
        scope_instance = None

        try:
            async with scope() as s:
                scope_instance = s
                s.set("test", "value")
                raise ValueError("Test error")
        except ValueError:
            pass

        # Scope should still be disposed
        assert len(scope_instance._scoped) == 0


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for container system"""

    def test_complex_dependency_graph(self, fresh_container):
        """Test complex dependency graph resolution"""
        # Config
        fresh_container.register_value("config", {"db_host": "localhost"})

        # Database depends on config
        class Database:
            def __init__(self, config):
                self.host = config["db_host"]

        fresh_container.register_singleton("db", Database, "@config")

        # Repository depends on database
        class Repository:
            def __init__(self, db):
                self.db = db

        fresh_container.register_singleton("repo", Repository, "@db")

        # Resolve
        repo = fresh_container.get("repo")

        assert repo.db.host == "localhost"

    def test_mixed_provider_types(self, fresh_container):
        """Test using different provider types together"""
        fresh_container.register_value("config", {"debug": False})
        fresh_container.register_singleton("service", SimpleService, "singleton")
        fresh_container.register_factory("factory_service", SimpleService, "factory")

        # Value always same
        assert fresh_container.get("config") is fresh_container.get("config")

        # Singleton always same
        assert fresh_container.get("service") is fresh_container.get("service")

        # Factory creates new
        assert fresh_container.get("factory_service") is not fresh_container.get("factory_service")

    def test_container_chaining(self, fresh_container):
        """Test fluent interface chaining"""
        result = (
            fresh_container
            .register_value("a", 1)
            .register_value("b", 2)
            .register_singleton("service", SimpleService)
        )

        assert result is fresh_container
        assert fresh_container.get("a") == 1
        assert fresh_container.get("b") == 2
