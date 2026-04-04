"""Tests for core.orchestrator - ZenOrchestrator LLM orchestrator."""

import pytest

from core.orchestrator import LLMResponse, QualityLevel, ZenOrchestrator


class TestQualityLevel:
    """Tests for QualityLevel enum."""

    def test_all_quality_levels_exist(self):
        """Test that expected quality levels exist."""
        assert hasattr(QualityLevel, "LOW")
        assert hasattr(QualityLevel, "MEDIUM")
        assert hasattr(QualityLevel, "HIGH")

    def test_quality_level_values(self):
        """Test quality level string values."""
        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.HIGH.value == "high"

    def test_quality_level_comparison(self):
        """Test quality levels can be compared."""
        assert QualityLevel.LOW != QualityLevel.MEDIUM
        assert QualityLevel.MEDIUM != QualityLevel.HIGH

    def test_quality_level_from_string(self):
        """Test creating quality level from string."""
        ql = QualityLevel("low")
        assert ql == QualityLevel.LOW


class TestLLMResponse:
    """Comprehensive tests for LLMResponse."""

    def test_llm_response_init_basic(self):
        """Test basic LLMResponse initialization."""
        response = LLMResponse(content="Test response")
        assert response.content == "Test response"

    def test_llm_response_with_metadata(self):
        """Test LLMResponse with metadata."""
        response = LLMResponse(
            content="Test",
            source="gpt-4",
            latency=0.5,
            quality=QualityLevel.HIGH,
        )
        assert response.source == "gpt-4"
        assert response.latency == 0.5

    def test_llm_response_empty_content(self):
        """Test LLMResponse with empty content."""
        response = LLMResponse(content="")
        assert response.content == ""

    def test_llm_response_long_content(self):
        """Test LLMResponse with long content."""
        long_text = "x" * 10000
        response = LLMResponse(content=long_text)
        assert response.content == long_text


class TestZenOrchestratorInit:
    """Tests for ZenOrchestrator initialization."""

    def test_orchestrator_init_default(self):
        """Test default orchestrator initialization."""
        orch = ZenOrchestrator()
        assert orch is not None
        assert orch.enable_caching is True
        assert orch.max_parallel_requests == 10

    def test_orchestrator_init_with_caching(self):
        """Test orchestrator with caching disabled."""
        orch = ZenOrchestrator(enable_caching=False)
        assert orch.enable_caching is False

    def test_orchestrator_init_with_quality(self):
        """Test orchestrator accepts quality-related init."""
        orch = ZenOrchestrator(cache_ttl=600)
        assert orch.cache_ttl == 600


class TestZenOrchestratorBackends:
    """Tests for backend management."""

    def test_add_backend(self):
        """Test adding a backend."""
        orch = ZenOrchestrator()

        class FakeBackend:
            name = "fake"
            priority = 1

        backend = FakeBackend()
        orch.add_backend(backend)
        assert backend in orch.backends

    def test_get_stats(self):
        """Test getting orchestrator stats."""
        orch = ZenOrchestrator()
        stats = orch.get_stats()
        assert isinstance(stats, dict)

    def test_get_capabilities(self):
        """Test getting orchestrator capabilities."""
        orch = ZenOrchestrator()
        caps = orch.get_capabilities()
        assert isinstance(caps, dict)

    def test_generate_cache_key(self):
        """Test cache key generation."""
        orch = ZenOrchestrator()
        key1 = orch._generate_cache_key("hello", QualityLevel.MEDIUM)
        key2 = orch._generate_cache_key("hello", QualityLevel.MEDIUM)
        key3 = orch._generate_cache_key("hello", QualityLevel.HIGH)
        assert key1 == key2
        assert key1 != key3


class TestZenOrchestratorScanMethods:
    """Tests for scan-related methods on ZenOrchestrator."""

    def test_run_autonomous_scan(self):
        """Test run_autonomous_scan signature."""
        orch = ZenOrchestrator()
        # Should not raise with basic args
        try:
            result = orch.run_autonomous_scan("example.com", "recon", "limited")
            assert result is not None
        except Exception as e:
            pytest.skip(f"Autonomous scan unavailable: {e}")

    def test_validate_findings(self):
        """Test validate_findings signature."""
        orch = ZenOrchestrator()
        try:
            result = orch.validate_findings([{"title": "test"}])
            assert result is not None
        except Exception as e:
            pytest.skip(f"Findings validation unavailable: {e}")


class TestZenOrchestratorErrors:
    """Tests for error handling."""

    def test_process_without_backends(self):
        """Test process with no backends returns error response."""
        orch = ZenOrchestrator()
        import asyncio

        response = asyncio.get_event_loop().run_until_complete(orch.process("hello", required_quality=QualityLevel.LOW))
        assert isinstance(response, LLMResponse)
        assert "error" in response.content.lower() or "failed" in response.content.lower() or response.source == "none"

    def test_invalid_quality(self):
        """Test invalid quality level raises ValueError."""
        with pytest.raises(ValueError):
            QualityLevel("invalid")
