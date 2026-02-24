"""
Metrics Collector

Collects and aggregates system metrics for dashboard display.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""

    timestamp: datetime
    value: float
    labels: Dict[str, str]


class MetricsCollector:
    """
    Collects system metrics for dashboard

    Collects:
    - System resource usage (CPU, memory)
    - Task statistics
    - Queue depths
    - Error rates
    - Performance metrics

    Example:
        collector = MetricsCollector()
        await collector.start()

        # Get current metrics
        metrics = collector.get_current_metrics()
    """

    def __init__(self, collection_interval: int = 10):
        self.collection_interval = collection_interval

        # Storage
        self._metrics: Dict[str, List[MetricPoint]] = {}
        self._current: Dict[str, Any] = {}
        self._max_history = 1000

        # Runtime
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None

        # Callbacks
        self._on_metrics: Optional[Callable] = None

    async def start(self) -> None:
        """Start metrics collection"""
        if self._running:
            return

        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collector started")

    async def stop(self) -> None:
        """Stop metrics collection"""
        if not self._running:
            return

        self._running = False

        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        logger.info("Metrics collector stopped")

    def on_metrics(self, callback: Callable) -> None:
        """Set callback for new metrics"""
        self._on_metrics = callback

    async def _collection_loop(self) -> None:
        """Main collection loop"""
        while self._running:
            try:
                metrics = await self._collect_metrics()
                self._current = metrics

                # Store history
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        if key not in self._metrics:
                            self._metrics[key] = []

                        self._metrics[key].append(
                            MetricPoint(
                                timestamp=datetime.utcnow(),
                                value=float(value),
                                labels={},
                            )
                        )

                        # Trim history
                        if len(self._metrics[key]) > self._max_history:
                            self._metrics[key] = self._metrics[key][
                                -self._max_history :
                            ]

                # Notify callback
                if self._on_metrics:
                    await self._on_metrics(metrics)

                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current metrics"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": await self._collect_system_metrics(),
            "tasks": await self._collect_task_metrics(),
            "scheduler": await self._collect_scheduler_metrics(),
        }

        return metrics

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system resource metrics"""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
            }
        except ImportError:
            return {"error": "psutil not available"}
        except Exception as e:
            return {"error": str(e)}

    async def _collect_task_metrics(self) -> Dict[str, Any]:
        """Collect task-related metrics"""
        # This would integrate with task manager
        # For now, return placeholder
        return {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
        }

    async def _collect_scheduler_metrics(self) -> Dict[str, Any]:
        """Collect scheduler metrics"""
        # This would integrate with scheduler
        return {
            "total_jobs": 0,
            "enabled_jobs": 0,
            "due_jobs": 0,
        }

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return self._current.copy()

    def get_metric_history(
        self, metric_name: str, duration_seconds: int = 3600
    ) -> List[MetricPoint]:
        """Get historical data for a metric"""
        points = self._metrics.get(metric_name, [])

        if not points:
            return []

        cutoff = datetime.utcnow() - timedelta(seconds=duration_seconds)
        return [p for p in points if p.timestamp >= cutoff]

    def get_metric_names(self) -> List[str]:
        """Get list of available metrics"""
        return list(self._metrics.keys())

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "collection_interval": self.collection_interval,
            "metrics_count": len(self._metrics),
            "data_points": sum(
                len(points) for points in self._metrics.values()
            ),
            "last_update": self._current.get("timestamp"),
        }


class MetricsAggregator:
    """
    Aggregates metrics over time periods

    Provides:
    - Averages
    - Min/Max values
    - Rates of change
    - Trends
    """

    @staticmethod
    def calculate_average(points: List[MetricPoint]) -> Optional[float]:
        """Calculate average of metric points"""
        if not points:
            return None
        return sum(p.value for p in points) / len(points)

    @staticmethod
    def calculate_min_max(points: List[MetricPoint]) -> tuple:
        """Calculate min and max values"""
        if not points:
            return None, None
        values = [p.value for p in points]
        return min(values), max(values)

    @staticmethod
    def calculate_rate(
        points: List[MetricPoint], duration_seconds: int = 60
    ) -> Optional[float]:
        """Calculate rate of change"""
        if len(points) < 2:
            return None

        first = points[0]
        last = points[-1]

        time_diff = (last.timestamp - first.timestamp).total_seconds()
        value_diff = last.value - first.value

        if time_diff == 0:
            return 0

        return (value_diff / time_diff) * duration_seconds

    @staticmethod
    def detect_trend(points: List[MetricPoint]) -> str:
        """Detect trend direction"""
        if len(points) < 3:
            return "insufficient_data"

        # Simple linear regression
        n = len(points)
        x = list(range(n))
        y = [p.value for p in points]

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
