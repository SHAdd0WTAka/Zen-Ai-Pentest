"""
Scheduled Job Definitions

Data models and enums for scheduled jobs.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ScheduleType(Enum):
    """Types of schedules"""

    CRON = "cron"  # Cron expression
    INTERVAL = "interval"  # Fixed interval (e.g., every 5 minutes)
    ONCE = "once"  # One-time execution
    DATETIME = "datetime"  # Specific date and time


class JobStatus(Enum):
    """Job lifecycle states"""

    SCHEDULED = "scheduled"  # Waiting for next execution
    RUNNING = "running"  # Currently executing
    PAUSED = "paused"  # Temporarily paused
    COMPLETED = "completed"  # One-time job completed
    FAILED = "failed"  # Last execution failed
    DISABLED = "disabled"  # Permanently disabled


@dataclass
class JobExecution:
    """Record of a single job execution"""

    id: str
    job_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class ScheduledJob:
    """
    A scheduled job definition

    Attributes:
        id: Unique job ID
        name: Human-readable name
        description: Job description
        task_type: Type of task to execute
        task_data: Task configuration
        schedule_type: Type of schedule
        schedule_expr: Schedule expression (cron, interval, datetime)
        status: Current job status
        timezone: Timezone for scheduling
        max_retries: Maximum retry attempts
        timeout: Task timeout in seconds
        enabled: Whether job is enabled
        created_at: Creation timestamp
        updated_at: Last update timestamp
        last_run: Last execution time
        next_run: Next scheduled execution
        run_count: Total execution count
        fail_count: Failed execution count
        metadata: Additional metadata
    """

    id: str
    name: str
    description: str
    task_type: str
    task_data: Dict[str, Any]
    schedule_type: ScheduleType
    schedule_expr: str
    status: JobStatus = JobStatus.SCHEDULED
    timezone: str = "UTC"
    max_retries: int = 3
    timeout: int = 3600
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    fail_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.schedule_type, str):
            self.schedule_type = ScheduleType(self.schedule_type)
        if isinstance(self.status, str):
            self.status = JobStatus(self.status)

    @classmethod
    def create(
        cls,
        name: str,
        task_type: str,
        task_data: Dict[str, Any],
        schedule_type: ScheduleType,
        schedule_expr: str,
        description: str = "",
        **kwargs,
    ) -> "ScheduledJob":
        """Create a new scheduled job"""
        return cls(
            id=f"job-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            task_type=task_type,
            task_data=task_data,
            schedule_type=schedule_type,
            schedule_expr=schedule_expr,
            **kwargs,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "task_data": self.task_data,
            "schedule_type": self.schedule_type.value,
            "schedule_expr": self.schedule_expr,
            "status": self.status.value,
            "timezone": self.timezone,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "fail_count": self.fail_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledJob":
        """Create from dictionary"""
        # Parse datetime fields
        datetime_fields = ["created_at", "updated_at", "last_run", "next_run"]
        for field_name in datetime_fields:
            if data.get(field_name):
                data[field_name] = datetime.fromisoformat(data[field_name])

        return cls(**data)

    def record_execution(
        self,
        success: bool,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        """Record job execution result"""
        self.last_run = datetime.utcnow()
        self.run_count += 1

        if success:
            self.status = (
                JobStatus.SCHEDULED
                if self.schedule_type != ScheduleType.ONCE
                else JobStatus.COMPLETED
            )
        else:
            self.fail_count += 1
            self.status = JobStatus.FAILED

        self.updated_at = datetime.utcnow()

    def pause(self):
        """Pause the job"""
        self.enabled = False
        self.status = JobStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self):
        """Resume the job"""
        self.enabled = True
        self.status = JobStatus.SCHEDULED
        self.updated_at = datetime.utcnow()

    def disable(self):
        """Permanently disable the job"""
        self.enabled = False
        self.status = JobStatus.DISABLED
        self.updated_at = datetime.utcnow()


class JobBuilder:
    """Builder pattern for creating scheduled jobs"""

    def __init__(self):
        self._name = ""
        self._description = ""
        self._task_type = ""
        self._task_data = {}
        self._schedule_type = ScheduleType.CRON
        self._schedule_expr = ""
        self._timezone = "UTC"
        self._max_retries = 3
        self._timeout = 3600
        self._metadata = {}

    def name(self, name: str) -> "JobBuilder":
        self._name = name
        return self

    def description(self, description: str) -> "JobBuilder":
        self._description = description
        return self

    def task(self, task_type: str, **task_data) -> "JobBuilder":
        self._task_type = task_type
        self._task_data = task_data
        return self

    def cron(self, expression: str) -> "JobBuilder":
        self._schedule_type = ScheduleType.CRON
        self._schedule_expr = expression
        return self

    def interval(self, minutes: int) -> "JobBuilder":
        self._schedule_type = ScheduleType.INTERVAL
        self._schedule_expr = str(minutes)
        return self

    def once(self, at: datetime) -> "JobBuilder":
        self._schedule_type = ScheduleType.ONCE
        self._schedule_expr = at.isoformat()
        return self

    def timezone(self, tz: str) -> "JobBuilder":
        self._timezone = tz
        return self

    def retries(self, count: int) -> "JobBuilder":
        self._max_retries = count
        return self

    def timeout(self, seconds: int) -> "JobBuilder":
        self._timeout = seconds
        return self

    def with_metadata(self, **metadata) -> "JobBuilder":
        self._metadata = metadata
        return self

    def build(self) -> ScheduledJob:
        """Build the scheduled job"""
        if not self._name:
            raise ValueError("Job name is required")
        if not self._task_type:
            raise ValueError("Task type is required")
        if not self._schedule_expr:
            raise ValueError("Schedule expression is required")

        return ScheduledJob.create(
            name=self._name,
            description=self._description,
            task_type=self._task_type,
            task_data=self._task_data,
            schedule_type=self._schedule_type,
            schedule_expr=self._schedule_expr,
            timezone=self._timezone,
            max_retries=self._max_retries,
            timeout=self._timeout,
            metadata=self._metadata,
        )
