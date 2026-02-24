#!/usr/bin/env python3
"""
Celery Configuration for Zen-AI-Pentest
"""

import os

# Broker settings
broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Serialization
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Timezone
timezone = "UTC"
enable_utc = True

# Task settings
task_track_started = True
task_time_limit = 3600  # 1 hour
task_soft_time_limit = 3000  # 50 minutes
worker_prefetch_multiplier = 1
task_acks_late = True

# Result settings
result_expires = 86400  # 24 hours
result_extended = True

# Worker settings
worker_max_tasks_per_child = 100
worker_max_memory_per_child = 512000  # 512 MB

# Beat schedule (periodic tasks)
beat_schedule = {
    "cleanup-old-scans-daily": {
        "task": "tasks.cleanup_old_scans",
        "schedule": 86400.0,  # Daily
        "args": (30,),
    },
}

# Queue settings
task_default_queue = "default"
task_queues = {
    "default": {"exchange": "default", "routing_key": "default"},
    "scans": {"exchange": "scans", "routing_key": "scans"},
    "reports": {"exchange": "reports", "routing_key": "reports"},
}

task_routes = {
    "tasks.run_security_scan": {"queue": "scans"},
    "tasks.generate_report": {"queue": "reports"},
}
