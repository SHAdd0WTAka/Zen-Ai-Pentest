"""
Tests for core/container.py
Target: 90%+ Coverage
"""
import pytest
from unittest.mock import MagicMock, patch
import inspect


class TestValue:
    """Test Value provider"""
    
    def test_value_provider(self):
        """Test Value provider returns constant"""
        from core.container import Value, Container
        
        container = Container()
        provider = Value("test_value")
        
        assert provider.get(container) == "test_value"
    
    def test_value_provider_any_type(self):
        """Test Value provider with different types"""
        from core.container import Value, Container
        
        container = Container()
        
        assert Value(123).get(container) == 123
        assert Value([1, 2, 3]).get(container) == [1, 2, 3]
        assert Value({"key": "value"}).get(container) == {"key": "value"}


class TestFactory:
    """Test Factory provider"""
    
    def test_factory_creates_new_instance(self):
        """Test Factory creates new instance each time"""
        from core.container import Factory, Container
        
        container = Container()
        counter = [0]
        
        def factory():
            counter[0] += 1
            return counter[0]
        
        provider = Factory(factory)
        
        assert provider.get(container) == 1
        assert provider.get(container) == 2
        assert provider.get(container) == 3
    
    def test_factory_with_args(self):
        """Test Factory with arguments"""
        from core.container import Factory, Container
        
        container = Container()
        
        def factory(a, b):
            return a + b
        
        provider = Factory(factory, 1, 2)
        assert provider.get(container) == 3


class TestSingleton:
    """Test Singleton provider"""
    
    def test_singleton_same_instance(self):
        """Test Singleton returns same instance"""
        from core.container import Singleton, Container
        
        container = Container()
        counter = [0]
        
        def factory():
            counter[0] += 1
            return counter[0]
        
        provider = Singleton(factory)
        
        assert provider.get(container) == 1
        assert provider.get(container) == 1  # Same instance
        assert provider.get(container) == 1
    
    def test_singleton_reset(self):
        """Test Singleton reset"""
        from core.container import Singleton, Container
        
        container = Container()
        counter = [0]
        
        def factory():
            counter[0] += 1
            return counter[0]
        
        provider = Singleton(factory)
        
        assert provider.get(container) == 1
        provider.reset()
        assert provider.get(container) == 2  # New instance after reset


class TestContainerBasic:
    """Test Container basic operations"""
    
    def test_container_register_and_get(self):
        """Test registering and getting provider"""
        from core.container import Container, Value
        
        container = Container()
        container.register("test", Value("value"))
        
        assert container.get("test") == "value"
    
    def test_container_register_chaining(self):
        """Test register returns container for chaining"""
        from core.container import Container, Value
        
        container = Container()
        result = container.register("a", Value(1)).register("b", Value(2))
        
        assert result is container
        assert container.get("a") == 1
        assert container.get("b") == 2
    
    def test_container_has(self):
        """Test has method"""
        from core.container import Container, Value
        
        container = Container()
        container.register("test", Value("value"))
        
        assert container.has("test") is True
        assert container.has("missing") is False
    
    def test_container_get_missing(self):
        """Test getting missing provider raises error"""
        from core.container import Container
        
        container = Container()
        
        with pytest.raises(KeyError):
            container.get("missing")


class TestContainerRegisterMethods:
    """Test Container register convenience methods"""
    
    def test_register_singleton(self):
        """Test register_singleton"""
        from core.container import Container
        
        container = Container()
        counter = [0]
        
        def factory():
            counter[0] += 1
            return counter[0]
        
        container.register_singleton("singleton", factory)
        
        assert container.get("singleton") == 1
        assert container.get("singleton") == 1  # Same instance
    
    def test_register_factory(self):
        """Test register_factory"""
        from core.container import Container
        
        container = Container()
        counter = [0]
        
        def factory():
            counter[0] += 1
            return counter[0]
        
        container.register_factory("factory", factory)
        
        assert container.get("factory") == 1
        assert container.get("factory") == 2  # New instance
    
    def test_register_value(self):
        """Test register_value"""
        from core.container import Container
        
        container = Container()
        container.register_value("config", {"debug": True})
        
        assert container.get("config") == {"debug": True}


class TestContainerRemove:
    """Test Container remove operations"""
    
    def test_remove_provider(self):
        """Test removing provider"""
        from core.container import Container, Value
        
        container = Container()
        container.register("test", Value("value"))
        container.remove("test")
        
        assert container.has("test") is False
    
    def test_remove_missing(self):
        """Test removing missing provider doesn't error"""
        from core.container import Container
        
        container = Container()
        container.remove("missing")  # Should not raise
    
    def test_remove_returns_container(self):
        """Test remove returns container for chaining"""
        from core.container import Container, Value
        
        container = Container()
        result = container.register("a", Value(1)).remove("a")
        
        assert result is container


class TestContainerReset:
    """Test Container reset"""
    
    def test_reset_singletons(self):
        """Test reset clears singleton instances"""
        from core.container import Container
        
        container = Container()
        counter = [0]
        
        def factory():
            counter[0] += 1
            return counter[0]
        
        container.register_singleton("singleton", factory)
        
        assert container.get("singleton") == 1
        container.reset()
        assert container.get("singleton") == 2  # New instance


class TestContainerDependencyResolution:
    """Test Container dependency resolution"""
    
    def test_resolve_reference(self):
        """Test resolving @reference"""
        from core.container import Container, Value, Factory
        
        container = Container()
        container.register("config", Value({"debug": True}))
        container.register("service", Factory(lambda c: c, "@config"))
        
        result = container.get("service")
        assert result == {"debug": True}
    
    def test_resolve_nested_provider(self):
        """Test resolving nested Provider"""
        from core.container import Container, Value, Factory
        
        container = Container()
        inner = Value("inner_value")
        container.register("outer", Factory(lambda x: x, inner))
        
        assert container.get("outer") == "inner_value"


class TestContainerInject:
    """Test Container inject decorator"""
    
    def test_inject_decorator(self):
        """Test inject decorator"""
        from core.container import Container, Value
        
        container = Container()
        container.register("db", Value("database"))
        
        @container.inject
        def my_function(db=None):
            return db
        
        result = my_function()
        assert result == "database"
    
    def test_inject_with_existing_arg(self):
        """Test inject doesn't override existing arg"""
        from core.container import Container, Value
        
        container = Container()
        container.register("db", Value("container_db"))
        
        @container.inject
        def my_function(db=None):
            return db
        
        result = my_function(db="provided_db")
        assert result == "provided_db"


class TestScope:
    """Test Scope class"""
    
    def test_scope_get_from_parent(self):
        """Test Scope gets from parent when not in scope"""
        from core.container import Container, Value
        
        container = Container()
        container.register("service", Value("parent_value"))
        
        scope = container.create_scope()
        assert scope.get("service") == "parent_value"
    
    def test_scope_set_and_get(self):
        """Test Scope set and get"""
        from core.container import Container
        
        container = Container()
        scope = container.create_scope()
        
        scope.set("scoped_service", "scoped_value")
        assert scope.get("scoped_service") == "scoped_value"
    
    def test_scope_overrides_parent(self):
        """Test Scope value overrides parent"""
        from core.container import Container, Value
        
        container = Container()
        container.register("service", Value("parent"))
        
        scope = container.create_scope()
        scope.set("service", "scoped")
        
        assert scope.get("service") == "scoped"
    
    def test_scope_is_scoped(self):
        """Test _is_scoped method"""
        from core.container import Container
        
        container = Container()
        scope = container.create_scope()
        
        assert scope._is_scoped("my_scoped") is True
        assert scope._is_scoped("other") is False
    
    def test_scope_dispose(self):
        """Test Scope dispose clears instances"""
        from core.container import Container
        
        container = Container()
        scope = container.create_scope()
        
        scope.set("service", "value")
        scope.dispose()
        
        # After dispose, should get from parent again
        assert len(scope._scoped) == 0
    
    def test_scope_dispose_with_dispose_method(self):
        """Test Scope dispose calls dispose on instances"""
        from core.container import Container
        
        container = Container()
        scope = container.create_scope()
        
        mock_instance = MagicMock()
        scope.set("service_scoped", mock_instance)
        
        scope.dispose()
        
        mock_instance.dispose.assert_called_once()


class TestGlobalContainer:
    """Test global container functions"""
    
    def test_get_container_singleton(self):
        """Test get_container returns singleton"""
        from core.container import get_container, set_container
        
        # Reset global container
        set_container(None)
        
        container1 = get_container()
        container2 = get_container()
        
        assert container1 is container2
    
    def test_set_container(self):
        """Test set_container sets global container"""
        from core.container import get_container, set_container, Container
        
        new_container = Container()
        set_container(new_container)
        
        assert get_container() is new_container


class TestInjectMarker:
    """Test inject marker"""
    
    def test_inject_marker(self):
        """Test inject marker creation"""
        from core.container import inject
        
        marker = inject("service")
        assert marker.dep_name == "service"


@pytest.mark.asyncio
class TestScopeAsync:
    """Test async scope context manager"""
    
    async def test_scope_context_manager(self):
        """Test scope async context manager"""
        from core.container import scope, set_container, Container
        
        set_container(Container())
        
        async with scope() as s:
            assert s is not None


class TestProviderResolveDependencies:
    """Test Provider _resolve_dependencies"""
    
    def test_resolve_dependencies_with_provider(self):
        """Test resolving dependencies with nested Provider"""
        from core.container import Provider, Container, Value
        
        class TestProvider(Provider):
            def get(self, container):
                args, kwargs = self._resolve_dependencies(container)
                return self.factory(*args, **kwargs)
        
        container = Container()
        container.register("value", Value("test"))
        
        inner_provider = Value("inner")
        provider = TestProvider(lambda x: x, inner_provider)
        
        result = provider.get(container)
        assert result == "inner"
