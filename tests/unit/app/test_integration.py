"""
Integration Tests

Tests the integration between all components.
"""

import pytest
import asyncio

# Import app components
try:
    from app import create_app, ApplicationFactory
    from app.container import DependencyContainer, ServiceProvider
    from app.lifecycle import ApplicationLifecycle, LifecyclePhase
except ImportError:
    import sys
    sys.path.insert(0, "../../..")
    from app import create_app, ApplicationFactory
    from app.container import DependencyContainer, ServiceProvider
    from app.lifecycle import ApplicationLifecycle, LifecyclePhase


class TestDependencyContainer:
    """Test dependency injection container"""
    
    def test_register_and_resolve_instance(self):
        """Test registering and resolving an instance"""
        container = DependencyContainer()
        
        config = {"debug": True}
        container.register_instance("config", config)
        
        resolved = container.resolve("config")
        assert resolved is config
        assert resolved["debug"] is True
    
    def test_register_factory(self):
        """Test registering a factory"""
        container = DependencyContainer()
        
        call_count = 0
        def create_service():
            nonlocal call_count
            call_count += 1
            return {"instance": call_count}
        
        container.register_factory("service", create_service, singleton=False)
        
        # Each resolve should create new instance
        s1 = container.resolve("service")
        s2 = container.resolve("service")
        
        assert call_count == 2
        assert s1 is not s2
    
    def test_singleton_factory(self):
        """Test singleton factory"""
        container = DependencyContainer()
        
        call_count = 0
        def create_singleton():
            nonlocal call_count
            call_count += 1
            return {"id": call_count}
        
        container.register_factory("singleton", create_singleton, singleton=True)
        
        # First resolve creates instance
        s1 = container.resolve("singleton")
        # Second resolve returns cached instance
        s2 = container.resolve("singleton")
        
        assert call_count == 1
        assert s1 is s2
    
    def test_resolve_optional(self):
        """Test optional dependency resolution"""
        container = DependencyContainer()
        
        # Existing service
        container.register_instance("exists", "value")
        assert container.resolve_optional("exists") == "value"
        
        # Non-existing service
        assert container.resolve_optional("missing") is None
        assert container.resolve_optional("missing", "default") == "default"
    
    def test_has_service(self):
        """Test service existence check"""
        container = DependencyContainer()
        
        assert container.has("missing") is False
        
        container.register_instance("exists", "value")
        assert container.has("exists") is True


class TestServiceProvider:
    """Test service provider"""
    
    def test_attribute_access(self):
        """Test accessing services via attributes"""
        container = DependencyContainer()
        container.register_instance("config", {"debug": True})
        
        provider = ServiceProvider(container)
        
        assert provider.config == {"debug": True}
    
    def test_attribute_caching(self):
        """Test service caching"""
        container = DependencyContainer()
        
        call_count = 0
        def create_service():
            nonlocal call_count
            call_count += 1
            return {"count": call_count}
        
        container.register_factory("service", create_service, singleton=True)
        provider = ServiceProvider(container)
        
        # Multiple accesses should use cache
        s1 = provider.service
        s2 = provider.service
        
        assert s1 is s2
        assert call_count == 1


class TestApplicationLifecycle:
    """Test application lifecycle"""
    
    @pytest.mark.asyncio
    async def test_startup_hooks(self):
        """Test startup hook execution"""
        lifecycle = ApplicationLifecycle()
        
        execution_order = []
        
        def hook1():
            execution_order.append("hook1")
        
        def hook2():
            execution_order.append("hook2")
        
        lifecycle.on_start("hook2", hook2, priority=20)
        lifecycle.on_start("hook1", hook1, priority=10)
        
        results = await lifecycle.start()
        
        assert execution_order == ["hook1", "hook2"]
        assert results["hook1"]["success"] is True
        assert results["hook2"]["success"] is True
        assert lifecycle.phase == LifecyclePhase.RUNNING
    
    @pytest.mark.asyncio
    async def test_shutdown_hooks(self):
        """Test shutdown hook execution"""
        lifecycle = ApplicationLifecycle()
        
        execution_order = []
        
        def hook1():
            execution_order.append("hook1")
        
        def hook2():
            execution_order.append("hook2")
        
        lifecycle.on_stop("hook2", hook2, priority=20)
        lifecycle.on_stop("hook1", hook1, priority=10)
        
        await lifecycle.start()
        execution_order.clear()
        
        await lifecycle.stop()
        
        # Shutdown in reverse priority order
        assert execution_order == ["hook2", "hook1"]
        assert lifecycle.phase == LifecyclePhase.STOPPED
    
    @pytest.mark.asyncio
    async def test_async_hooks(self):
        """Test async hook execution"""
        lifecycle = ApplicationLifecycle()
        
        async def async_hook():
            await asyncio.sleep(0.01)
            return "async_result"
        
        lifecycle.on_start("async", async_hook)
        
        results = await lifecycle.start()
        
        assert results["async"]["result"] == "async_result"
    
    @pytest.mark.asyncio
    async def test_hook_failure_handling(self):
        """Test handling of hook failures"""
        lifecycle = ApplicationLifecycle()
        
        def success_hook():
            return "success"
        
        def fail_hook():
            raise Exception("Hook failed")
        
        lifecycle.on_start("fail", fail_hook)
        lifecycle.on_start("success", success_hook)
        
        results = await lifecycle.start()
        
        assert results["fail"]["success"] is False
        assert results["success"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_component_storage(self):
        """Test component storage during lifecycle"""
        lifecycle = ApplicationLifecycle()
        
        def create_component():
            return {"id": "component1"}
        
        lifecycle.on_start("comp", create_component)
        
        await lifecycle.start()
        
        component = lifecycle.get_component("comp")
        assert component["id"] == "component1"
    
    def test_status_reporting(self):
        """Test status reporting"""
        lifecycle = ApplicationLifecycle()
        
        def hook1(): pass
        def hook2(): pass
        
        lifecycle.on_start("h1", hook1)
        lifecycle.on_start("h2", hook2)
        lifecycle.on_stop("h1", hook1)
        lifecycle.on_stop("h2", hook2)
        
        status = lifecycle.get_status()
        
        assert status["phase"] == "initializing"
        assert status["startup_hooks"] == 2
        assert status["shutdown_hooks"] == 2


class TestApplicationFactory:
    """Test application factory"""
    
    def test_create_app(self):
        """Test app creation"""
        factory = ApplicationFactory()
        app = factory.create(debug=False, enable_docs=False)
        
        assert app is not None
        assert app.title == "Zen-AI-Pentest API"
    
    def test_app_routes(self):
        """Test route registration"""
        factory = ApplicationFactory()
        app = factory.create(debug=False, enable_docs=True)
        
        routes = [route.path for route in app.routes]
        
        assert "/health" in routes
        assert "/ready" in routes
        assert "/live" in routes


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
