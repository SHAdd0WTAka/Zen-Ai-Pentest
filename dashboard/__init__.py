"""
Live Dashboard System for Zen-AI-Pentest

Real-time dashboard with:
- WebSocket event streaming
- Live metrics and statistics
- Task progress tracking
- System health monitoring

Usage:
    from dashboard import DashboardManager
    
    dashboard = DashboardManager()
    await dashboard.start()
    
    # Stream events to connected clients
    await dashboard.broadcast({
        "type": "task_update",
        "data": {"task_id": "123", "progress": 50}
    })
"""

from .manager import DashboardManager, DashboardConfig
from .websocket import DashboardWebSocket
from .metrics import MetricsCollector
from .events import DashboardEvent, EventStream

__all__ = [
    "DashboardManager",
    "DashboardConfig",
    "DashboardWebSocket",
    "MetricsCollector",
    "DashboardEvent",
    "EventStream",
]

__version__ = "1.0.0"
