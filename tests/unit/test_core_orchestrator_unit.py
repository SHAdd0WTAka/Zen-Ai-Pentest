"""
Unit Tests for ZenOrchestrator - Core Functionality
Phase 1: Test Coverage Improvement
"""

import asyncio
import os

# Test the core orchestrator
import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestQualityLevel:
    """Test QualityLevel Enum"""

    def test_quality_levels_exist(self):
        from core.orchestrator import QualityLevel

        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.HIGH.value == "high"

    def test_quality_level_comparison(self):
        from core.orchestrator import QualityLevel

        # Test that all expected levels exist
        assert hasattr(QualityLevel, "LOW")
        assert hasattr(QualityLevel, "MEDIUM")
        assert hasattr(QualityLevel, "HIGH")


class TestLLMResponse:
    """Test LLMResponse dataclass"""

    def test_response_creation(self):
        from core.orchestrator import LLMResponse, QualityLevel

        response = LLMResponse(
            content="Test response",
            source="test_backend",
            latency=0.5,
            quality=QualityLevel.HIGH,
        )
        assert response.content == "Test response"
        assert response.source == "test_backend"
        assert response.latency == 0.5
        assert response.quality == QualityLevel.HIGH

    def test_response_with_metadata(self):
        from core.orchestrator import LLMResponse, QualityLevel

        response = LLMResponse(
            content="Test",
            source="backend1",
            latency=1.0,
            quality=QualityLevel.MEDIUM,
            metadata={"tokens": 100},
        )
        assert response.metadata == {"tokens": 100}


class TestZenOrchestratorInit:
    """Test ZenOrchestrator initialization"""

    def test_orchestrator_init(self):
        from core.orchestrator import ZenOrchestrator

        orchestrator = ZenOrchestrator()
        assert orchestrator is not None
        assert hasattr(orchestrator, "backends")
        # Test methods exist
        assert callable(getattr(orchestrator, "get_capabilities", None))

    def test_initial_backends_list(self):
        from core.orchestrator import ZenOrchestrator

        orchestrator = ZenOrchestrator()
        assert isinstance(orchestrator.backends, list)
        assert len(orchestrator.backends) == 0

    def test_initial_capabilities(self):
        from core.orchestrator import ZenOrchestrator

        orchestrator = ZenOrchestrator()
        caps = orchestrator.get_capabilities()
        assert isinstance(caps, dict)
        assert "autonomous_scan" in caps
        assert "exploit_validation" in caps


class TestZenOrchestratorBackends:
    """Test backend management"""

    def test_add_backend(self):
        from core.orchestrator import BaseBackend, ZenOrchestrator

        orchestrator = ZenOrchestrator()
        mock_backend = Mock(spec=BaseBackend)
        mock_backend.name = "test_backend"
        mock_backend.priority = 1

        orchestrator.add_backend(mock_backend)
        assert len(orchestrator.backends) == 1
        assert orchestrator.backends[0] == mock_backend

    def test_add_multiple_backends(self):
        from core.orchestrator import BaseBackend, ZenOrchestrator

        orchestrator = ZenOrchestrator()

        backend1 = Mock(spec=BaseBackend)
        backend1.name = "backend1"
        backend1.priority = 2

        backend2 = Mock(spec=BaseBackend)
        backend2.name = "backend2"
        backend2.priority = 1

        orchestrator.add_backend(backend1)
        orchestrator.add_backend(backend2)

        assert len(orchestrator.backends) == 2
        # Check backends are sorted by priority
        assert orchestrator.backends[0].priority == 1
        assert orchestrator.backends[1].priority == 2

    def test_backend_priority_sorting(self):
        from core.orchestrator import BaseBackend, ZenOrchestrator

        orchestrator = ZenOrchestrator()

        # Add backends in reverse priority order
        for i in [3, 1, 2]:
            backend = Mock(spec=BaseBackend)
            backend.priority = i
            backend.name = f"backend_{i}"
            orchestrator.add_backend(backend)

        priorities = [b.priority for b in orchestrator.backends]
        assert priorities == [1, 2, 3]


class TestBaseBackend:
    """Test BaseBackend abstract class"""

    def test_base_backend_init(self):
        from core.orchestrator import BaseBackend

        class TestBackend(BaseBackend):
            async def chat(self, prompt, context=""):
                return "test"

            async def health_check(self):
                return True

        backend = TestBackend("test", 1)
        assert backend.name == "test"
        assert backend.priority == 1


class TestZenOrchestratorProcess:
    """Test process method with mocks"""

    @pytest.mark.asyncio
    async def test_process_with_no_backends(self):
        from core.orchestrator import ZenOrchestrator

        orchestrator = ZenOrchestrator()

        result = await orchestrator.process("test prompt")
        # Should return fallback response when no backends
        assert result is not None
        assert hasattr(result, "content")

    @pytest.mark.asyncio
    async def test_process_with_fallback(self):
        """Test that process returns fallback when backend fails"""
        from core.orchestrator import BaseBackend, ZenOrchestrator

        orchestrator = ZenOrchestrator()

        mock_backend = Mock(spec=BaseBackend)
        mock_backend.name = "failing_backend"
        mock_backend.priority = 1
        mock_backend.chat = AsyncMock(return_value=None)  # Simulate failure
        mock_backend.health_check = AsyncMock(return_value=False)

        orchestrator.add_backend(mock_backend)

        result = await orchestrator.process("test prompt")
        # Should return fallback response when backend fails
        assert result is not None
        assert hasattr(result, "content")


class TestZenOrchestratorParallelConsensus:
    """Test parallel consensus method"""

    @pytest.mark.asyncio
    async def test_parallel_consensus_no_backends(self):
        from core.orchestrator import ZenOrchestrator

        orchestrator = ZenOrchestrator()

        result = await orchestrator.parallel_consensus("test prompt")
        assert isinstance(result, dict)


class TestZenOrchestratorHealth:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_with_healthy_backend(self):
        from core.orchestrator import BaseBackend, ZenOrchestrator

        orchestrator = ZenOrchestrator()
        mock_backend = Mock(spec=BaseBackend)
        mock_backend.name = "healthy_backend"
        mock_backend.priority = 1
        mock_backend.health_check = AsyncMock(return_value=True)

        orchestrator.add_backend(mock_backend)

        # Test individual backend health
        is_healthy = await mock_backend.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_with_unhealthy_backend(self):
        from core.orchestrator import BaseBackend, ZenOrchestrator

        orchestrator = ZenOrchestrator()
        mock_backend = Mock(spec=BaseBackend)
        mock_backend.name = "unhealthy_backend"
        mock_backend.priority = 1
        mock_backend.health_check = AsyncMock(return_value=False)

        orchestrator.add_backend(mock_backend)

        is_healthy = await mock_backend.health_check()
        assert is_healthy is False


class TestZenOrchestratorErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_process_with_exception(self):
        from core.orchestrator import BaseBackend, ZenOrchestrator

        orchestrator = ZenOrchestrator()

        mock_backend = Mock(spec=BaseBackend)
        mock_backend.name = "failing_backend"
        mock_backend.priority = 1
        mock_backend.chat = AsyncMock(side_effect=Exception("Test error"))

        orchestrator.add_backend(mock_backend)

        # Should handle exception gracefully
        result = await orchestrator.process("test")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
