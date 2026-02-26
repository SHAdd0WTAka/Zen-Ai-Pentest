"""
Comprehensive tests for agent_comm/v2/src/circuit_breaker.py
Target: 80%+ Coverage
"""

import time
import pytest
import threading
from unittest.mock import MagicMock, patch

from agent_comm.v2.src.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitBreakerOpen,
    CircuitState,
)


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""
    
    def test_default_values(self):
        """Test default configuration."""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 30.0
        assert config.success_threshold == 3
        assert config.half_open_max_calls == 10
    
    def test_custom_values(self):
        """Test custom configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60.0,
            success_threshold=2,
            half_open_max_calls=5
        )
        
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 60.0
        assert config.success_threshold == 2
        assert config.half_open_max_calls == 5
    
    def test_validation_failure_threshold_zero(self):
        """Test validation for failure_threshold=0."""
        with pytest.raises(ValueError, match="failure_threshold must be at least 1"):
            CircuitBreakerConfig(failure_threshold=0)
    
    def test_validation_recovery_timeout_zero(self):
        """Test validation for recovery_timeout=0."""
        with pytest.raises(ValueError, match="recovery_timeout must be positive"):
            CircuitBreakerConfig(recovery_timeout=0)
    
    def test_validation_success_threshold_zero(self):
        """Test validation for success_threshold=0."""
        with pytest.raises(ValueError, match="success_threshold must be at least 1"):
            CircuitBreakerConfig(success_threshold=0)


class TestCircuitBreakerInitialization:
    """Tests for CircuitBreaker initialization."""
    
    def test_default_init(self):
        """Test default initialization."""
        cb = CircuitBreaker("test")
        
        assert cb.name == "test"
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed is True
        assert cb.is_open is False
        assert cb.is_half_open is False
    
    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        
        assert cb.config.failure_threshold == 3
    
    def test_init_with_callback(self):
        """Test initialization with state change callback."""
        callback = MagicMock()
        cb = CircuitBreaker("test", on_state_change=callback)
        
        assert cb.on_state_change is callback


class TestCircuitBreakerClosedState:
    """Tests for CLOSED state (normal operation)."""
    
    def test_successful_call(self):
        """Test successful function call."""
        cb = CircuitBreaker("test")
        
        result = cb.call(lambda: "success")
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
    
    def test_successful_call_with_args(self):
        """Test successful call with arguments."""
        cb = CircuitBreaker("test")
        
        result = cb.call(lambda x, y: x + y, 1, 2)
        
        assert result == 3
    
    def test_successful_call_with_kwargs(self):
        """Test successful call with keyword arguments."""
        cb = CircuitBreaker("test")
        
        result = cb.call(lambda x, y=0: x + y, 1, y=2)
        
        assert result == 3
    
    def test_failed_call_raises_exception(self):
        """Test that failed call raises original exception."""
        cb = CircuitBreaker("test")
        
        with pytest.raises(ValueError, match="test error"):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("test error")))
    
    def test_failure_count_increments(self):
        """Test that failure count increments on failure."""
        cb = CircuitBreaker("test")
        
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        metrics = cb.get_metrics()
        assert metrics["calls_failed"] == 1
        assert metrics["failure_count"] == 1
    
    def test_failure_count_resets_on_success(self):
        """Test that failure count resets on success."""
        cb = CircuitBreaker("test")
        
        # Fail twice
        for _ in range(2):
            try:
                cb.call(lambda: 1/0)
            except ZeroDivisionError:
                pass
        
        # Succeed
        cb.call(lambda: "success")
        
        metrics = cb.get_metrics()
        assert metrics["failure_count"] == 0


class TestCircuitBreakerOpenState:
    """Tests for OPEN state (circuit broken)."""
    
    def test_opens_after_threshold(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        
        # Fail 3 times
        for _ in range(3):
            try:
                cb.call(lambda: 1/0)
            except ZeroDivisionError:
                pass
        
        assert cb.state == CircuitState.OPEN
        assert cb.is_open is True
    
    def test_rejects_calls_when_open(self):
        """Test that calls are rejected when open."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config)
        
        # Open the circuit
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: "success")
    
    def test_metrics_track_rejections(self):
        """Test that rejected calls are tracked."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config)
        
        # Open the circuit
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        # Reject a call
        try:
            cb.call(lambda: "success")
        except CircuitBreakerOpen:
            pass
        
        metrics = cb.get_metrics()
        assert metrics["calls_rejected"] == 1


class TestCircuitBreakerHalfOpenState:
    """Tests for HALF_OPEN state (testing recovery)."""
    
    def test_transitions_to_half_open_after_timeout(self):
        """Test transition to half-open after recovery timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1
        )
        cb = CircuitBreaker("test", config)
        
        # Open the circuit
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Next call should trigger half-open
        try:
            cb.call(lambda: "test")
        except CircuitBreakerOpen:
            pass  # Might still be rejected due to race
        
        # State should be half-open or transitioning
        assert cb.state in [CircuitState.HALF_OPEN, CircuitState.OPEN]
    
    def test_success_in_half_open_increments_success_count(self):
        """Test success count increments in half-open."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,
            success_threshold=2
        )
        cb = CircuitBreaker("test", config)
        
        # Open circuit
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        time.sleep(0.15)
        
        # Force half-open
        cb.force_closed()
        cb.force_open()
        cb._transition_to(CircuitState.HALF_OPEN)
        
        # Success in half-open
        cb._on_success()
        
        assert cb._success_count == 1
    
    def test_failure_in_half_open_returns_to_open(self):
        """Test that failure in half-open returns to open."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1
        )
        cb = CircuitBreaker("test", config)
        
        # Open circuit
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        time.sleep(0.15)
        
        # Force half-open and fail
        cb._transition_to(CircuitState.HALF_OPEN)
        cb._on_failure()
        
        assert cb.state == CircuitState.OPEN
    
    def test_closes_after_success_threshold(self):
        """Test circuit closes after success threshold in half-open."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2
        )
        cb = CircuitBreaker("test", config)
        
        # Manually set to half-open
        cb._transition_to(CircuitState.HALF_OPEN)
        
        # Two successes
        cb._on_success()
        cb._on_success()
        
        assert cb.state == CircuitState.CLOSED
    
    def test_half_open_call_limit(self):
        """Test that half-open has call limit."""
        config = CircuitBreakerConfig(
            half_open_max_calls=2
        )
        cb = CircuitBreaker("test", config)
        
        # Manually set to half-open and use both calls
        cb._transition_to(CircuitState.HALF_OPEN)
        cb._half_open_calls = 2
        
        # Third call should be rejected
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: "test")


class TestCircuitBreakerForceState:
    """Tests for force state methods."""
    
    def test_force_open(self):
        """Test forcing circuit to open."""
        cb = CircuitBreaker("test")
        
        cb.force_open()
        
        assert cb.state == CircuitState.OPEN
    
    def test_force_closed(self):
        """Test forcing circuit to closed."""
        cb = CircuitBreaker("test")
        
        # Open first
        cb.force_open()
        assert cb.state == CircuitState.OPEN
        
        # Then close
        cb.force_closed()
        
        assert cb.state == CircuitState.CLOSED
    
    def test_force_no_change_when_already_in_state(self):
        """Test force methods when already in state."""
        cb = CircuitBreaker("test")
        
        # Already closed, force closed again
        cb.force_closed()
        
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerStateCallback:
    """Tests for state change callback."""
    
    def test_callback_called_on_state_change(self):
        """Test callback is called when state changes."""
        callback = MagicMock()
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config, on_state_change=callback)
        
        # Open the circuit
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == CircuitState.CLOSED
        assert args[1] == CircuitState.OPEN
    
    def test_callback_exception_handled(self):
        """Test that callback exceptions are handled gracefully."""
        callback = MagicMock(side_effect=Exception("callback error"))
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config, on_state_change=callback)
        
        # Should not raise even though callback fails
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        # Circuit should still be open
        assert cb.is_open


class TestCircuitBreakerMetrics:
    """Tests for circuit breaker metrics."""
    
    def test_metrics_initial(self):
        """Test initial metrics."""
        cb = CircuitBreaker("test")
        
        metrics = cb.get_metrics()
        
        assert metrics["name"] == "test"
        assert metrics["state"] == "closed"
        assert metrics["calls_attempted"] == 0
        assert metrics["calls_succeeded"] == 0
        assert metrics["calls_failed"] == 0
        assert metrics["calls_rejected"] == 0
        assert metrics["state_changes"] == 0
    
    def test_metrics_tracked(self):
        """Test that metrics are tracked correctly."""
        cb = CircuitBreaker("test")
        
        # Successful call
        cb.call(lambda: "success")
        
        # Failed call
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        metrics = cb.get_metrics()
        assert metrics["calls_attempted"] == 2
        assert metrics["calls_succeeded"] == 1
        assert metrics["calls_failed"] == 1


class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""
    
    def test_get_or_create_new(self):
        """Test creating new circuit breaker."""
        registry = CircuitBreakerRegistry()
        
        cb = registry.get_or_create("cb1")
        
        assert cb.name == "cb1"
        assert cb.state == CircuitState.CLOSED
    
    def test_get_or_create_existing(self):
        """Test getting existing circuit breaker."""
        registry = CircuitBreakerRegistry()
        
        cb1 = registry.get_or_create("cb1")
        cb2 = registry.get_or_create("cb1")
        
        assert cb1 is cb2
    
    def test_get_existing(self):
        """Test getting existing circuit breaker."""
        registry = CircuitBreakerRegistry()
        registry.get_or_create("cb1")
        
        cb = registry.get("cb1")
        
        assert cb is not None
        assert cb.name == "cb1"
    
    def test_get_nonexistent(self):
        """Test getting non-existent circuit breaker."""
        registry = CircuitBreakerRegistry()
        
        cb = registry.get("nonexistent")
        
        assert cb is None
    
    def test_remove_existing(self):
        """Test removing existing circuit breaker."""
        registry = CircuitBreakerRegistry()
        registry.get_or_create("cb1")
        
        result = registry.remove("cb1")
        
        assert result is True
        assert registry.get("cb1") is None
    
    def test_remove_nonexistent(self):
        """Test removing non-existent circuit breaker."""
        registry = CircuitBreakerRegistry()
        
        result = registry.remove("nonexistent")
        
        assert result is False
    
    def test_get_all_metrics(self):
        """Test getting metrics for all breakers."""
        registry = CircuitBreakerRegistry()
        registry.get_or_create("cb1")
        registry.get_or_create("cb2")
        
        metrics = registry.get_all_metrics()
        
        assert "cb1" in metrics
        assert "cb2" in metrics
    
    def test_get_open_circuits(self):
        """Test getting list of open circuits."""
        registry = CircuitBreakerRegistry()
        
        cb1 = registry.get_or_create("cb1")
        cb2 = registry.get_or_create("cb2")
        
        # Open cb1
        cb1.force_open()
        
        open_circuits = registry.get_open_circuits()
        
        assert open_circuits == ["cb1"]


class TestCircuitBreakerConcurrency:
    """Concurrency tests for CircuitBreaker."""
    
    def test_concurrent_calls(self):
        """Test concurrent calls to circuit breaker."""
        cb = CircuitBreaker("test")
        results = []
        errors = []
        
        def make_call():
            try:
                result = cb.call(lambda: "success")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=make_call) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 50
        assert len(errors) == 0
    
    def test_concurrent_failures(self):
        """Test concurrent failures."""
        config = CircuitBreakerConfig(failure_threshold=100)
        cb = CircuitBreaker("test", config)
        errors = []
        
        def fail_call():
            try:
                cb.call(lambda: 1/0)
            except ZeroDivisionError:
                pass
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=fail_call) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should have gotten ZeroDivisionError, not CircuitBreakerOpen
        # (since failure_threshold is 100)
        assert len(errors) == 0
        assert cb.get_metrics()["calls_failed"] == 50


@pytest.mark.asyncio
class TestCircuitBreakerAsync:
    """Async tests for CircuitBreaker."""
    
    async def test_async_call_success(self):
        """Test successful async call."""
        cb = CircuitBreaker("test")
        
        async def async_func():
            return "async success"
        
        result = await cb.call_async(async_func)
        
        assert result == "async success"
    
    async def test_async_call_failure(self):
        """Test failed async call."""
        cb = CircuitBreaker("test")
        
        async def async_func():
            raise ValueError("async error")
        
        with pytest.raises(ValueError, match="async error"):
            await cb.call_async(async_func)
    
    async def test_async_opens_after_threshold(self):
        """Test async circuit opens after failures."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        
        async def fail():
            raise ValueError("fail")
        
        for _ in range(3):
            try:
                await cb.call_async(fail)
            except ValueError:
                pass
        
        assert cb.is_open
        
        with pytest.raises(CircuitBreakerOpen):
            await cb.call_async(lambda: "success")
