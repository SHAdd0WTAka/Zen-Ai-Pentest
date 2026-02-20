"""
Task Scheduler for Zen-AI-Pentest

Advanced scheduling system with:
- Cron-style expressions
- Recurring tasks
- Job queuing and execution
- Schedule management API

Usage:
    from scheduler import TaskScheduler

    scheduler = TaskScheduler()
    await scheduler.start()

    # Schedule a daily scan
    job_id = await scheduler.schedule(
        task_type="vulnerability_scan",
        task_data={"target": "example.com"},
        cron="0 2 * * *"  # Daily at 2 AM
    )
"""

from .core import ScheduleConfig, TaskScheduler
from .cron import CronParser
from .job import JobStatus, ScheduledJob, ScheduleType
from .recurring import RecurringSchedule

__all__ = [
    "TaskScheduler",
    "ScheduleConfig",
    "ScheduledJob",
    "JobStatus",
    "ScheduleType",
    "CronParser",
    "RecurringSchedule",
]

__version__ = "1.0.0"
