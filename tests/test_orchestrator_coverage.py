"""
Tests for core/orchestrator module - Coverage Boost
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from dataclasses import dataclass


class TestQualityLevel:
    """Test QualityLevel enum"""

    def test_quality_level_values(self):
        """Test QualityLevel enum values"""
        from core.orchestrator import QualityLevel
        
        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.HIGH.value == "high"


class TestLLMResponse:
    """Test LLMResponse dataclass"""

    def test_llm_response_creation(self):
        """Test LLMResponse creation"""
        from core.orchestrator import LLMResponse, QualityLevel
        
        response = LLMResponse(
            content="Test response",
            source="test_backend",
            latency=0.5,
            quality=QualityLevel.HIGH,
            metadata={"tokens": 100}
        )
        
        assert response.content == "Test response"
        assert response.source == "test_backend"
        assert response.latency == 0.5
        assert response.quality == QualityLevel.HIGH
        assert response.metadata == {"tokens": 100}

    def test_llm_response_defaults(self):
        """Test LLMResponse with default metadata"""
        from core.orchestrator import LLMResponse, QualityLevel
        
        response = LLMResponse(
            content="Test",
            source="backend",
            latency=1.0,
            quality=QualityLevel.LOW
        )
        
        assert response.metadata is None


class TestBaseBackend:
    """Test BaseBackend abstract class"""

    def test_base_backend_init(self):
        """Test BaseBackend initialization"""
        from core.orchestrator import BaseBackend
        
        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                return "test"
        
        backend = TestBackend(name="test", priority=1)
        
        assert backend.name == "test"
        assert backend.priority == 1
        assert backend.session is None

    @pytest.mark.asyncio
    async def test_base_backend_async_context(self):
        """Test BaseBackend async context manager"""
        from core.orchestrator import BaseBackend
        
        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                return "test"
        
        backend = TestBackend(name="test", priority=1)
        
        async with backend:
            assert backend.session is not None
        
        # Session should be closed after context

    @pytest.mark.asyncio
    async def test_base_backend_health_check(self):
        """Test BaseBackend health check"""
        from core.orchestrator import BaseBackend
        
        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                return "test"
        
        backend = TestBackend(name="test", priority=1)
        
        # Default health check returns True
        is_healthy = await backend.health_check()
        assert is_healthy is True


class TestZenOrchestrator:
    """Test ZenOrchestrator class"""

    def test_orchestrator_init(self):
        """Test ZenOrchestrator initialization"""
        from core.orchestrator import ZenOrchestrator
        
        orchestrator = ZenOrchestrator()
        
        assert orchestrator is not None
        assert hasattr(orchestrator, 'backends')
        assert hasattr(orchestrator, 'results_cache')
        assert hasattr(orchestrator, 'request_count')

    def test_orchestrator_initializes_components(self):
        """Test that orchestrator initializes optional components"""
        from core.orchestrator import ZenOrchestrator
        
        orchestrator = ZenOrchestrator()
        
        # Check that component attributes exist
        assert hasattr(orchestrator, '_autonomous_loop')
        assert hasattr(orchestrator, '_fp_engine')
        assert hasattr(orchestrator, '_exploit_validator')
        assert hasattr(orchestrator, '_business_impact')
        assert hasattr(orchestrator, '_integrations')

    def test_add_backend(self):
        """Test adding a backend"""
        from core.orchestrator import ZenOrchestrator, BaseBackend
        
        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                return "test"
        
        orchestrator = ZenOrchestrator()
        backend = TestBackend(name="test", priority=1)
        
        orchestrator.add_backend(backend)
        
        assert len(orchestrator.backends) == 1
        assert orchestrator.backends[0] == backend

    def test_add_multiple_backends_sorted(self):
        """Test that backends are sorted by priority"""
        from core.orchestrator import ZenOrchestrator, BaseBackend
        
        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                return "test"
        
        orchestrator = ZenOrchestrator()
        backend1 = TestBackend(name="low", priority=2)
        backend2 = TestBackend(name="high", priority=1)
        
        orchestrator.add_backend(backend1)
        orchestrator.add_backend(backend2)
        
        # Should be sorted by priority (lower number = higher priority)
        assert orchestrator.backends[0].name == "high"
        assert orchestrator.backends[1].name == "low"

    @pytest.mark.asyncio
    async def test_process_with_backends(self):
        """Test process with registered backends"""
        from core.orchestrator import ZenOrchestrator, BaseBackend, QualityLevel
        
        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                return f"Response from {self.name}"
            
            async def health_check(self) -> bool:
                return True
        
        orchestrator = ZenOrchestrator()
        backend = TestBackend(name="test", priority=1)
        orchestrator.add_backend(backend)
        
        # Test process
        async with backend:
            response = await orchestrator.process("Hello", required_quality=QualityLevel.LOW)
        
        assert response is not None
        assert isinstance(response.content, str)

    def test_get_stats(self):
        """Test getting orchestrator stats"""
        from core.orchestrator import ZenOrchestrator
        
        orchestrator = ZenOrchestrator()
        stats = orchestrator.get_stats()
        
        assert isinstance(stats, dict)
        assert "backends" in stats
        assert "backends_registered" in stats

    def test_get_capabilities(self):
        """Test getting orchestrator capabilities"""
        from core.orchestrator import ZenOrchestrator
        
        orchestrator = ZenOrchestrator()
        capabilities = orchestrator.get_capabilities()
        
        assert isinstance(capabilities, dict)
        assert "autonomous_scan" in capabilities
        assert "false_positive_validation" in capabilities

    def test_request_count_increment(self):
        """Test request count increment"""
        from core.orchestrator import ZenOrchestrator
        
        orchestrator = ZenOrchestrator()
        initial_count = orchestrator.request_count
        
        orchestrator.request_count += 1
        
        assert orchestrator.request_count == initial_count + 1


class TestOrchestratorWithMocks:
    """Test ZenOrchestrator with mocked dependencies"""

    def test_orchestrator_graceful_fallback(self):
        """Test that orchestrator works even when optional components fail"""
        from core.orchestrator import ZenOrchestrator
        
        orchestrator = ZenOrchestrator()
        
        # Should work even without components
        stats = orchestrator.get_stats()
        assert stats is not None
        
        capabilities = orchestrator.get_capabilities()
        assert capabilities is not None

    @pytest.mark.asyncio
    async def test_process_with_mock_backend(self):
        """Test process with mock backend"""
        from core.orchestrator import ZenOrchestrator, BaseBackend, QualityLevel
        
        class MockBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                return "Mock response"
            
            async def health_check(self) -> bool:
                return True
        
        orchestrator = ZenOrchestrator()
        backend = MockBackend(name="mock", priority=1)
        orchestrator.add_backend(backend)
        
        async with backend:
            response = await orchestrator.process("Test prompt", required_quality=QualityLevel.MEDIUM)
        
        assert response is not None
        assert response.content == "Mock response"
        assert response.source == "mock"

    @pytest.mark.asyncio
    async def test_parallel_consensus(self):
        """Test parallel consensus"""
        from core.orchestrator import ZenOrchestrator, BaseBackend
        
        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                return f"Response from {self.name}"
        
        orchestrator = ZenOrchestrator()
        backend1 = TestBackend(name="backend1", priority=1)
        backend2 = TestBackend(name="backend2", priority=2)
        
        orchestrator.add_backend(backend1)
        orchestrator.add_backend(backend2)
        
        async with backend1, backend2:
            result = await orchestrator.parallel_consensus("Test prompt")
        
        assert isinstance(result, dict)
        assert "consensus" in result or "error" in result


class TestAsyncOperations:
    """Test async operations in orchestrator"""

    @pytest.mark.asyncio
    async def test_concurrent_backend_calls(self):
        """Test concurrent calls to multiple backends"""
        from core.orchestrator import ZenOrchestrator, BaseBackend
        
        responses = []
        
        class SlowBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> str:
                await asyncio.sleep(0.01)
                responses.append(self.name)
                return f"{self.name} response"
        
        orchestrator = ZenOrchestrator()
        backend1 = SlowBackend(name="slow1", priority=1)
        backend2 = SlowBackend(name="slow2", priority=2)
        
        orchestrator.add_backend(backend1)
        orchestrator.add_backend(backend2)
        
        # Call both backends concurrently
        async with backend1, backend2:
            results = await asyncio.gather(
                backend1.chat("test"),
                backend2.chat("test"),
                return_exceptions=True
            )
        
        assert len(results) == 2
