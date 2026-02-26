"""
Circuit Breaker Pattern for gRPC Agent Communication v2.

Prevents cascade failures when agents or services become unavailable.
Implements the standard circuit breaker states: CLOSED, OPEN, HALF_OPEN.
"""

import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker.
    
    Attributes:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before trying half-open
        success_threshold: Number of successes in half-open to close
        half_open_max_calls: Max calls allowed in half-open state
    """
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 3
    half_open_max_calls: int = 10
    
    def __post_init__(self):
        """Validate configuration."""
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")
        if self.success_threshold < 1:
            raise ValueError("success_threshold must be at least 1")


class CircuitBreaker:
    """Circuit breaker implementation for resilient agent communication.
    
    Automatically opens when failures exceed threshold, preventing
    cascade failures across the agent network.
    
    Example:
        cb = CircuitBreaker("agent-connection", CircuitBreakerConfig())
        
        try:
            result = cb.call(lambda: connect_to_agent(agent_id))
        except CircuitBreakerOpen:
            # Circuit is open, service unavailable
            pass
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None
    ):
        """Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name (for logging/metrics)
            config: Circuit breaker configuration
            on_state_change: Callback when state changes (old_state, new_state)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = 0.0
        self._lock = threading.RLock()
        
        self._metrics = {
            "calls_attempted": 0,
            "calls_succeeded": 0,
            "calls_failed": 0,
            "calls_rejected": 0,
            "state_changes": 0,
        }
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing)."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing)."""
        return self.state == CircuitState.HALF_OPEN
    
    def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Call a function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Any exception from the function
        """
        with self._lock:
            self._metrics["calls_attempted"] += 1
            
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
                else:
                    self._metrics["calls_rejected"] += 1
                    raise CircuitBreakerOpen(
                        f"Circuit '{self.name}' is OPEN"
                    )
            
            # Check half-open call limit
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._metrics["calls_rejected"] += 1
                    raise CircuitBreakerOpen(
                        f"Circuit '{self.name}' HALF_OPEN call limit reached"
                    )
                self._half_open_calls += 1
        
        # Execute call outside lock
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, async_func: Callable[..., Any], *args, **kwargs) -> Any:
        """Call an async function with circuit breaker protection.
        
        Args:
            async_func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        import asyncio
        
        with self._lock:
            self._metrics["calls_attempted"] += 1
            
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
                else:
                    self._metrics["calls_rejected"] += 1
                    raise CircuitBreakerOpen(
                        f"Circuit '{self.name}' is OPEN"
                    )
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._metrics["calls_rejected"] += 1
                    raise CircuitBreakerOpen(
                        f"Circuit '{self.name}' HALF_OPEN call limit reached"
                    )
                self._half_open_calls += 1
        
        try:
            result = await async_func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            self._metrics["calls_succeeded"] += 1
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self._metrics["calls_failed"] += 1
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open -> back to open
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try half-open."""
        return (
            time.time() - self._last_failure_time
        ) >= self.config.recovery_timeout
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to new state.
        
        Args:
            new_state: State to transition to
        """
        old_state = self._state
        self._state = new_state
        self._metrics["state_changes"] += 1
        
        # Reset counters
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.OPEN:
            self._success_count = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
        
        logger.info(
            f"Circuit '{self.name}' transitioned: "
            f"{old_state.value} -> {new_state.value}"
        )
        
        if self.on_state_change:
            try:
                self.on_state_change(old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback failed: {e}")
    
    def force_open(self):
        """Force circuit to open state (for manual intervention)."""
        with self._lock:
            if self._state != CircuitState.OPEN:
                self._transition_to(CircuitState.OPEN)
    
    def force_closed(self):
        """Force circuit to closed state (for recovery)."""
        with self._lock:
            if self._state != CircuitState.CLOSED:
                self._transition_to(CircuitState.CLOSED)
    
    def get_metrics(self) -> dict:
        """Get circuit breaker metrics.
        
        Returns:
            Dictionary with metrics
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "half_open_calls": self._half_open_calls,
                "last_failure_time": self._last_failure_time,
                **self._metrics,
            }


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers.
    
    Useful for managing circuits for different agents or services.
    """
    
    def __init__(self):
        """Initialize registry."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one.
        
        Args:
            name: Circuit breaker name
            config: Configuration (used if creating new)
            
        Returns:
            Circuit breaker instance
        """
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name.
        
        Args:
            name: Circuit breaker name
            
        Returns:
            Circuit breaker or None if not found
        """
        with self._lock:
            return self._breakers.get(name)
    
    def remove(self, name: str) -> bool:
        """Remove circuit breaker from registry.
        
        Args:
            name: Circuit breaker name
            
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                return True
            return False
    
    def get_all_metrics(self) -> dict[str, dict]:
        """Get metrics for all circuit breakers.
        
        Returns:
            Dictionary mapping names to metrics
        """
        with self._lock:
            return {
                name: breaker.get_metrics()
                for name, breaker in self._breakers.items()
            }
    
    def get_open_circuits(self) -> list[str]:
        """Get list of open circuit breaker names.
        
        Returns:
            List of names of open circuits
        """
        with self._lock:
            return [
                name for name, breaker in self._breakers.items()
                if breaker.is_open
            ]
