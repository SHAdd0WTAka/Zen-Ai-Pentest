"""Smoke tests for core/orchestrator.py"""

import pytest

from core.orchestrator import (
    BaseBackend,
    CircuitBreaker,
    CircuitBreakerOpen,
    LLMResponse,
    QualityLevel,
    ZenOrchestrator,
    close_orchestrator,
    get_orchestrator,
)


class TestQualityLevel:
    def test_values(self):
        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.HIGH.value == "high"


class TestLLMResponse:
    def test_defaults(self):
        resp = LLMResponse(content="hello")
        assert resp.content == "hello"
        assert resp.source == ""
        assert resp.latency == 0.0
        assert resp.cached is False

    def test_full(self):
        resp = LLMResponse(content="test", source="gpt4", latency=1.5, quality=QualityLevel.HIGH, cached=True)
        assert resp.source == "gpt4"
        assert resp.quality == QualityLevel.HIGH
        assert resp.cached is True


class TestCircuitBreaker:
    def test_init(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0, half_open_max_calls=2)
        assert cb._state == "closed"
        assert cb._failures == 0

    def test_state_property(self):
        cb = CircuitBreaker()
        assert cb.state == "closed"


class TestCircuitBreakerOpen:
    def test_exception(self):
        exc = CircuitBreakerOpen()
        assert isinstance(exc, Exception)


class TestBaseBackend:
    def test_abstract(self):
        assert "chat" in BaseBackend.__abstractmethods__


class TestZenOrchestrator:
    def test_init_defaults(self):
        orch = ZenOrchestrator(enable_caching=False)
        assert orch.backends == []
        assert orch.request_count == 0
        assert orch.enable_caching is False

    def test_get_stats(self):
        orch = ZenOrchestrator(enable_caching=False)
        stats = orch.get_stats()
        assert "backends_registered" in stats
        assert stats["requests_processed"] == 0


class TestGlobalFunctions:
    def test_get_orchestrator(self):
        orch = get_orchestrator()
        assert isinstance(orch, ZenOrchestrator)
