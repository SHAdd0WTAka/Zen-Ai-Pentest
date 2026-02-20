"""
Dashboard Manager

Main dashboard coordinator that brings together:
- WebSocket connections
- Metrics collection
- Event streaming
- Integration with orchestrator components
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from .events import DashboardEvent, EventType
from .metrics import MetricsCollector
from .websocket import DashboardWebSocket

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Dashboard configuration"""

    websocket_enabled: bool = True
    metrics_enabled: bool = True
    metrics_interval: int = 10
    event_buffer_size: int = 1000
    max_connections: int = 100


class DashboardManager:
    """
    Main dashboard manager

    Coordinates all dashboard components and provides
    a unified interface for real-time updates.

    Example:
        dashboard = DashboardManager()
        await dashboard.start()

        # Broadcast task update
        await dashboard.broadcast_task_progress(
            task_id="123",
            progress=50,
            message="Scanning ports..."
        )
    """

    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()

        # Components
        self.websocket: Optional[DashboardWebSocket] = None
        self.metrics: Optional[MetricsCollector] = None

        # Event buffer for replay
        self._event_buffer: list = []
        self._max_buffer_size = self.config.event_buffer_size

        # Runtime
        self._running = False
        self._started_at: Optional[datetime] = None

        # Integration hooks
        self._orchestrator = None
        self._scheduler = None

    async def start(self) -> None:
        """Start dashboard manager"""
        if self._running:
            return

        logger.info("Starting DashboardManager...")

        # Start WebSocket
        if self.config.websocket_enabled:
            self.websocket = DashboardWebSocket(max_connections=self.config.max_connections)
            await self.websocket.start()

        # Start metrics collector
        if self.config.metrics_enabled:
            self.metrics = MetricsCollector(collection_interval=self.config.metrics_interval)
            self.metrics.on_metrics(self._on_metrics_collected)
            await self.metrics.start()

        self._running = True
        self._started_at = datetime.utcnow()

        logger.info("✅ DashboardManager started")

    async def stop(self) -> None:
        """Stop dashboard manager"""
        if not self._running:
            return

        logger.info("Stopping DashboardManager...")

        if self.websocket:
            await self.websocket.stop()

        if self.metrics:
            await self.metrics.stop()

        self._running = False
        logger.info("✅ DashboardManager stopped")

    # ==================== Event Broadcasting ====================

    async def broadcast(self, event: DashboardEvent) -> int:
        """Broadcast event to all connected clients"""
        # Buffer event
        self._buffer_event(event)

        # Send via WebSocket
        if self.websocket:
            return await self.websocket.broadcast(event)

        return 0

    async def broadcast_task_progress(self, task_id: str, progress: float, message: str = "", **kwargs) -> int:
        """Broadcast task progress update"""
        event = DashboardEvent.task_progress(task_id=task_id, progress=progress, message=message, **kwargs)
        return await self.broadcast(event)

    async def broadcast_system_metrics(self, metrics: Dict[str, Any]) -> int:
        """Broadcast system metrics"""
        event = DashboardEvent.system_metrics(metrics)
        return await self.broadcast(event)

    async def broadcast_security_alert(self, alert_type: str, severity: str, details: Dict[str, Any]) -> int:
        """Broadcast security alert"""
        event = DashboardEvent.security_alert(alert_type, severity, details)
        return await self.broadcast(event)

    async def broadcast_notification(self, title: str, message: str, level: str = "info") -> int:
        """Broadcast user notification"""
        event = DashboardEvent(
            type=EventType.NOTIFICATION,
            data={"title": title, "message": message, "level": level},
            priority=4 if level == "error" else 3,
        )
        return await self.broadcast(event)

    def _buffer_event(self, event: DashboardEvent) -> None:
        """Add event to buffer"""
        self._event_buffer.append(event)

        if len(self._event_buffer) > self._max_buffer_size:
            self._event_buffer = self._event_buffer[-self._max_buffer_size :]

    # ==================== WebSocket Integration ====================

    async def handle_websocket_connect(self, websocket, user_id: Optional[str] = None) -> str:
        """Handle new WebSocket connection"""
        if not self.websocket:
            raise RuntimeError("WebSocket not enabled")

        conn_id = await self.websocket.connect(websocket, user_id)

        # Send recent events as replay
        recent_events = self._event_buffer[-50:]  # Last 50 events
        for event in recent_events:
            await self.websocket.send_to_connection(conn_id, event.to_dict())

        return conn_id

    async def handle_websocket_disconnect(self, connection_id: str) -> None:
        """Handle WebSocket disconnection"""
        if self.websocket:
            await self.websocket.disconnect(connection_id)

    async def handle_websocket_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message"""
        if self.websocket:
            await self.websocket.handle_message(connection_id, message)

    # ==================== Metrics Integration ====================

    async def _on_metrics_collected(self, metrics: Dict[str, Any]) -> None:
        """Callback when new metrics are collected"""
        await self.broadcast_system_metrics(metrics)

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        if self.metrics:
            return self.metrics.get_current_metrics()
        return {}

    # ==================== Integration with Orchestrator ====================

    def connect_orchestrator(self, orchestrator) -> None:
        """Connect to orchestrator for event streaming"""
        self._orchestrator = orchestrator

        # Subscribe to orchestrator events
        # This would be implemented based on orchestrator event bus
        pass

    def connect_scheduler(self, scheduler) -> None:
        """Connect to scheduler for event streaming"""
        self._scheduler = scheduler
        pass

    # ==================== Statistics ====================

    def get_statistics(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        stats = {
            "running": self._running,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "buffered_events": len(self._event_buffer),
        }

        if self.websocket:
            stats["websocket"] = self.websocket.get_statistics()

        if self.metrics:
            stats["metrics"] = self.metrics.get_summary()

        return stats

    # ==================== API Endpoints Helper ====================

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data for initial load"""
        return {
            "system_status": self._get_system_status(),
            "current_metrics": self.get_current_metrics(),
            "recent_events": [e.to_dict() for e in self._event_buffer[-20:]],
            "statistics": self.get_statistics(),
        }

    def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "status": "healthy" if self._running else "stopped",
            "dashboard": "running" if self._running else "stopped",
            "websocket": "running" if self.websocket and self.websocket._running else "stopped",
            "metrics": "running" if self.metrics and self.metrics._running else "stopped",
        }
