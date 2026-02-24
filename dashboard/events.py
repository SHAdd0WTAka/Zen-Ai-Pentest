"""
Dashboard Event System

Event types and streaming for real-time dashboard updates.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EventType(Enum):
    """Dashboard event types"""

    # Task Events
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # System Events
    SYSTEM_STATUS = "system.status"
    SYSTEM_HEALTH = "system.health"
    SYSTEM_METRICS = "system.metrics"
    SYSTEM_ALERT = "system.alert"

    # Security Events
    SECURITY_ALERT = "security.alert"
    SECURITY_VIOLATION = "security.violation"
    SCAN_FINDING = "scan.finding"

    # Schedule Events
    SCHEDULE_TRIGGERED = "schedule.triggered"
    SCHEDULE_COMPLETED = "schedule.completed"

    # User Events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_ACTION = "user.action"

    # Analysis Events
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_PROGRESS = "analysis.progress"
    ANALYSIS_COMPLETED = "analysis.completed"

    # Generic
    NOTIFICATION = "notification"
    CUSTOM = "custom"


@dataclass
class DashboardEvent:
    """
    Dashboard event message

    Attributes:
        type: Event type
        data: Event payload
        timestamp: Event timestamp
        id: Unique event ID
        source: Event source component
        priority: Event priority (1-5, 5 being highest)
        user_id: Associated user ID
        session_id: Associated session ID
    """

    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str = "system"
    priority: int = 3
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "priority": self.priority,
            "user_id": self.user_id,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardEvent":
        """Create from dictionary"""
        event_type = EventType(data.get("type", "custom"))
        return cls(
            type=event_type,
            data=data.get("data", {}),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.utcnow()
            ),
            id=data.get("id", str(uuid.uuid4())[:8]),
            source=data.get("source", "system"),
            priority=data.get("priority", 3),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
        )

    @classmethod
    def task_progress(
        cls, task_id: str, progress: float, message: str = "", **kwargs
    ) -> "DashboardEvent":
        """Create task progress event"""
        return cls(
            type=EventType.TASK_PROGRESS,
            data={
                "task_id": task_id,
                "progress": progress,
                "message": message,
                **kwargs,
            },
            source="task_manager",
        )

    @classmethod
    def system_metrics(cls, metrics: Dict[str, Any]) -> "DashboardEvent":
        """Create system metrics event"""
        return cls(
            type=EventType.SYSTEM_METRICS,
            data=metrics,
            source="metrics_collector",
            priority=2,
        )

    @classmethod
    def security_alert(
        cls, alert_type: str, severity: str, details: Dict[str, Any]
    ) -> "DashboardEvent":
        """Create security alert event"""
        priority_map = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1,
        }
        return cls(
            type=EventType.SECURITY_ALERT,
            data={
                "alert_type": alert_type,
                "severity": severity,
                "details": details,
            },
            source="security_monitor",
            priority=priority_map.get(severity.lower(), 3),
        )


class EventStream:
    """
    Event stream for filtering and buffering

    Allows clients to subscribe to specific event types
    and receive buffered events on connection.
    """

    def __init__(
        self,
        event_types: Optional[list] = None,
        min_priority: int = 1,
        buffer_size: int = 100,
    ):
        self.event_types = set(event_types) if event_types else None
        self.min_priority = min_priority
        self.buffer_size = buffer_size
        self._buffer: list = []

    def matches(self, event: DashboardEvent) -> bool:
        """Check if event matches stream criteria"""
        if event.priority < self.min_priority:
            return False

        if self.event_types and event.type not in self.event_types:
            return False

        return True

    def add(self, event: DashboardEvent) -> None:
        """Add event to buffer"""
        if not self.matches(event):
            return

        self._buffer.append(event)

        # Trim buffer
        if len(self._buffer) > self.buffer_size:
            self._buffer = self._buffer[-self.buffer_size :]

    def get_recent(self, count: int = 10) -> list:
        """Get recent events from buffer"""
        return self._buffer[-count:]

    def clear(self) -> None:
        """Clear buffer"""
        self._buffer.clear()
