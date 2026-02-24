"""
Circuit Breaker with Fallback
When small LLM fails or hallucinates: immediate fallback to deterministic regex
Better slow and safe than fast and leaky.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from .filters.injection import PromptInjectionDetector
from .filters.secrets import SecretScrubber
from .schemas import RiskLevel, SanitizerResponse

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, use fallback
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitMetrics:
    """Metrics for circuit breaker"""

    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[float] = None
    consecutive_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker for small LLM operations.
    Falls back to regex-based processing when LLM fails.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

        # Fallback components
        self.fallback_scrubber = SecretScrubber()
        self.fallback_injection = PromptInjectionDetector()

    async def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute operation with circuit breaker protection

        Args:
            operation: Async function to execute
            *args, **kwargs: Arguments for operation

        Returns:
            Operation result or fallback result
        """
        async with self._lock:
            # Check if we should attempt reset
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info("Circuit entering HALF_OPEN state")
                else:
                    logger.warning("Circuit OPEN - using fallback")
                    return await self._fallback_response(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.half_open_max_calls:
                    logger.warning("HALF_OPEN limit reached - using fallback")
                    return await self._fallback_response(*args, **kwargs)
                self.half_open_calls += 1

        # Execute operation
        try:
            result = await operation(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            logger.error(f"Operation failed: {e}")
            return await self._fallback_response(*args, **kwargs)

    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to try recovery"""
        if self.metrics.last_failure_time is None:
            return True

        elapsed = time.time() - self.metrics.last_failure_time
        return elapsed >= self.recovery_timeout

    async def _on_success(self):
        """Handle successful operation"""
        async with self._lock:
            self.metrics.successes += 1
            self.metrics.consecutive_successes += 1

            if self.state == CircuitState.HALF_OPEN:
                # Recovery successful
                self.state = CircuitState.CLOSED
                self.metrics.failures = 0
                self.half_open_calls = 0
                logger.info("Circuit CLOSED - recovery successful")

    async def _on_failure(self):
        """Handle failed operation"""
        async with self._lock:
            self.metrics.failures += 1
            self.metrics.last_failure_time = time.time()
            self.metrics.consecutive_successes = 0

            if self.state == CircuitState.HALF_OPEN:
                # Recovery failed
                self.state = CircuitState.OPEN
                logger.warning("Circuit OPEN - recovery failed")
            elif self.metrics.failures >= self.failure_threshold:
                # Threshold reached
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit OPEN - {self.metrics.failures} failures"
                )

    async def _fallback_response(
        self, raw_data: str, source_tool: str = "unknown", **kwargs
    ) -> SanitizerResponse:
        """
        Generate fallback response using only regex

        This is deterministic and safe, but less intelligent than LLM.
        """
        logger.info("Using fallback sanitization (regex only)")

        start_time = time.time()

        # Step 1: Scrub secrets
        cleaned, redactions = self.fallback_scrubber.scrub(raw_data)

        # Step 2: Check for injection
        is_injection, injection_matches = self.fallback_injection.scan(cleaned)
        if is_injection:
            cleaned = self.fallback_injection.sanitize(cleaned)

        # Step 3: Simple heuristic compression
        cleaned = self._simple_compress(cleaned, source_tool)

        # Step 4: Risk analysis
        risk_indicators = self.fallback_scrubber.analyze_risk(cleaned)
        if is_injection:
            risk_indicators.append("prompt_injection_detected")

        # Determine risk level
        if len(redactions) > 5 or is_injection:
            risk_level = RiskLevel.DANGER
        elif len(redactions) > 0:
            risk_level = RiskLevel.SUSPECT
        else:
            risk_level = RiskLevel.CLEAN

        processing_time = (time.time() - start_time) * 1000

        return SanitizerResponse(
            cleaned_data=cleaned,
            redactions=redactions,
            risk_indicators=risk_indicators,
            compression_ratio=(
                len(cleaned) / len(raw_data) if raw_data else 1.0
            ),
            safe_to_send=risk_level != RiskLevel.DANGER,
            fallback_used=True,
            risk_level=risk_level,
            tokens_saved=(len(raw_data) - len(cleaned)) // 4,
            processing_time_ms=processing_time,
        )

    def _simple_compress(self, text: str, source_tool: str) -> str:
        """Simple fallback compression when LLM unavailable"""
        lines = text.split("\n")

        # Keep lines with important keywords
        important = [
            "open",
            "vuln",
            "error",
            "200",
            "401",
            "403",
            "500",
            "version",
            "server",
            "port",
            "service",
            "critical",
            "high",
        ]

        filtered = []
        for line in lines:
            line_lower = line.lower()
            if any(k in line_lower for k in important):
                filtered.append(line)

        # Hard cap
        if len(filtered) > 50:
            filtered = filtered[:50]
            filtered.append(f"... [{len(lines) - 50} lines omitted]")

        return "\n".join(filtered)

    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            "state": self.state.value,
            "metrics": {
                "failures": self.metrics.failures,
                "successes": self.metrics.successes,
                "consecutive_successes": self.metrics.consecutive_successes,
                "last_failure": self.metrics.last_failure_time,
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "half_open_max_calls": self.half_open_max_calls,
            },
        }

    async def force_reset(self):
        """Force circuit to closed state"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.metrics = CircuitMetrics()
            self.half_open_calls = 0
            logger.info("Circuit manually reset to CLOSED")
