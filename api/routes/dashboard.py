"""
Dashboard API Routes

REST API and WebSocket endpoints for live dashboard.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field

# Import dashboard
try:
    from dashboard import DashboardManager, DashboardEvent, EventType
except ImportError:
    import sys
    sys.path.insert(0, "../..")
    from dashboard import DashboardManager, DashboardEvent, EventType


router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

# Global dashboard instance
_dashboard: Optional[DashboardManager] = None


def get_dashboard() -> DashboardManager:
    """Get or create dashboard instance"""
    global _dashboard

    if _dashboard is None:
        from dashboard import DashboardConfig
        config = DashboardConfig()
        _dashboard = DashboardManager(config)

    return _dashboard


# Request/Response Models
class DashboardStatusResponse(BaseModel):
    running: bool
    started_at: Optional[str]
    websocket_connections: int
    buffered_events: int


class SystemStatusResponse(BaseModel):
    status: str
    dashboard: str
    websocket: str
    metrics: str


class EventBroadcastRequest(BaseModel):
    type: str
    data: dict = Field(default_factory=dict)
    priority: int = Field(default=3, ge=1, le=5)


# REST Endpoints

@router.get("/status", response_model=DashboardStatusResponse)
async def get_status(
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """Get dashboard status and statistics"""
    stats = dashboard.get_statistics()

    return DashboardStatusResponse(
        running=stats["running"],
        started_at=stats.get("started_at"),
        websocket_connections=stats.get("websocket", {}).get("active_connections", 0),
        buffered_events=stats.get("buffered_events", 0)
    )


@router.get("/system", response_model=SystemStatusResponse)
async def get_system_status(
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """Get overall system status"""
    data = await dashboard.get_dashboard_data()
    return SystemStatusResponse(**data["system_status"])


@router.get("/data")
async def get_dashboard_data(
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """Get complete dashboard data for initial load"""
    return await dashboard.get_dashboard_data()


@router.get("/metrics")
async def get_metrics(
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """Get current system metrics"""
    return dashboard.get_current_metrics()


@router.get("/events/recent")
async def get_recent_events(
    limit: int = Query(default=50, ge=1, le=200),
    event_type: Optional[str] = None,
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """
    Get recent dashboard events

    - **limit**: Number of events to return (1-200)
    - **event_type**: Filter by event type
    """
    events = dashboard._event_buffer[-limit:]

    if event_type:
        try:
            et = EventType(event_type)
            events = [e for e in events if e.type == et]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    return {
        "events": [e.to_dict() for e in events],
        "total": len(events)
    }


@router.post("/broadcast")
async def broadcast_event(
    request: EventBroadcastRequest,
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """
    Broadcast a custom event to all connected clients

    Requires admin privileges in production.
    """
    try:
        event_type = EventType(request.type)
    except ValueError:
        event_type = EventType.CUSTOM

    event = DashboardEvent(
        type=event_type,
        data=request.data,
        priority=request.priority,
        source="api"
    )

    count = await dashboard.broadcast(event)

    return {
        "broadcasted": True,
        "clients_notified": count,
        "event_id": event.id
    }


@router.post("/notify")
async def send_notification(
    title: str,
    message: str,
    level: str = "info",
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """
    Send notification to all connected clients

    - **title**: Notification title
    - **message**: Notification message
    - **level**: info, warning, error, success
    """
    count = await dashboard.broadcast_notification(title, message, level)

    return {
        "sent": True,
        "clients_notified": count
    }


# WebSocket Endpoint

@router.websocket("/ws")
async def dashboard_websocket(
    websocket: WebSocket,
    token: Optional[str] = None,
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """
    WebSocket endpoint for real-time dashboard updates

    Connection flow:
    1. Client connects
    2. Server sends recent events as replay
    3. Client subscribes to specific event types
    4. Server pushes matching events in real-time

    Client messages:
    - {"action": "subscribe", "event_types": ["task.progress", "system.metrics"]}
    - {"action": "ping"}
    - {"action": "set_priority", "min_priority": 3}
    """
    await websocket.accept()

    # Authenticate (simplified - would validate token in production)
    user_id = None
    if token:
        # Validate token and extract user_id
        pass

    # Connect to dashboard
    try:
        connection_id = await dashboard.handle_websocket_connect(websocket, user_id)

        try:
            while True:
                # Receive message from client
                message = await websocket.receive_json()

                # Handle message
                await dashboard.handle_websocket_message(connection_id, message)

        except WebSocketDisconnect:
            pass
        finally:
            await dashboard.handle_websocket_disconnect(connection_id)

    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


# Task Progress Endpoint

@router.get("/tasks/{task_id}/progress")
async def get_task_progress(
    task_id: str,
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """Get task progress from event buffer"""
    # Search in buffered events
    for event in reversed(dashboard._event_buffer):
        if (event.type == EventType.TASK_PROGRESS and
            event.data.get("task_id") == task_id):
            return event.data

    raise HTTPException(status_code=404, detail=f"No progress found for task {task_id}")


# Statistics Endpoints

@router.get("/stats/websocket")
async def get_websocket_stats(
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """Get WebSocket connection statistics"""
    if not dashboard.websocket:
        raise HTTPException(status_code=503, detail="WebSocket not enabled")

    return dashboard.websocket.get_statistics()


@router.get("/stats/metrics")
async def get_metrics_stats(
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """Get metrics collector statistics"""
    if not dashboard.metrics:
        raise HTTPException(status_code=503, detail="Metrics not enabled")

    return dashboard.metrics.get_summary()


# Event Types Endpoint

@router.get("/event-types")
async def get_event_types():
    """Get available event types"""
    return {
        "event_types": [
            {
                "value": et.value,
                "category": et.value.split(".")[0] if "." in et.value else "general",
                "description": et.name.replace("_", " ").title()
            }
            for et in EventType
        ]
    }


# Health Check

@router.get("/health")
async def health_check(
    dashboard: DashboardManager = Depends(get_dashboard)
):
    """Dashboard health check"""
    checks = {
        "dashboard": dashboard._running,
        "websocket": dashboard.websocket._running if dashboard.websocket else False,
        "metrics": dashboard.metrics._running if dashboard.metrics else False,
    }

    all_healthy = all(checks.values())

    return {
        "healthy": all_healthy,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
