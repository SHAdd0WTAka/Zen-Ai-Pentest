"""
Performance Metrics Collection

Tracks and reports performance metrics.
"""

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class MetricSample:
    """Single metric sample"""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class PerformanceMetrics:
    """
    Collects and reports performance metrics

    Tracks:
    - Response times
    - Throughput
    - Error rates
    - Resource usage
    """

    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples
        self._metrics: Dict[str, deque] = {}
        self._counters: Dict[str, int] = {}

    def record(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a metric sample"""
        if name not in self._metrics:
            self._metrics[name] = deque(maxlen=self.max_samples)

        sample = MetricSample(
            timestamp=datetime.utcnow(), value=value, labels=labels or {}
        )

        self._metrics[name].append(sample)

    def increment(self, name: str, value: int = 1):
        """Increment a counter"""
        self._counters[name] = self._counters.get(name, 0) + value

    def get_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a metric"""
        samples = self._metrics.get(name)
        if not samples:
            return {"count": 0}

        values = [s.value for s in samples]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all metrics"""
        return {name: self.get_stats(name) for name in self._metrics.keys()}

    def get_counters(self) -> Dict[str, int]:
        """Get all counters"""
        return self._counters.copy()

    def reset(self):
        """Reset all metrics"""
        self._metrics.clear()
        self._counters.clear()


class TimingContext:
    """Context manager for timing operations"""

    def __init__(
        self,
        metrics: PerformanceMetrics,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.metrics = metrics
        self.name = name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        self.metrics.record(self.name, elapsed, self.labels)

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, *args):
        elapsed = time.time() - self.start_time
        self.metrics.record(self.name, elapsed, self.labels)


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate: int, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()

    def acquire(self) -> bool:
        """Try to acquire a token"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def get_wait_time(self) -> float:
        """Get time to wait for next token"""
        if self.tokens >= 1:
            return 0
        return (1 - self.tokens) / self.rate
