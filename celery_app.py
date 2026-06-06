"""
Celery Application für Zen-AI-Pentest Scan Scheduler

Konfiguriert Celery mit Beat-Scheduler für wiederkehrende Tasks,
Prioritäts-Warteschlangen und Retry-Logik.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Celery App erstellen
celery_app = Celery(
    "zen_pentest",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["tasks.scan_tasks"],
)

# Konfiguration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone=os.getenv("TZ", "UTC"),
    enable_utc=True,
    # Task-Einstellungen
    task_track_started=True,
    task_time_limit=7200,  # 2 Stunden Hard-Limit
    task_soft_time_limit=3600,  # 1 Stunde Soft-Limit
    task_acks_late=True,  # ACK erst nach Abschluss
    worker_prefetch_multiplier=1,  # Fair-Task-Verteilung
    # Retry-Einstellungen
    task_default_retry_delay=60,  # 1 Minute
    task_max_retries=3,
    # Result-Backend
    result_expires=86400 * 7,  # 7 Tage
    result_extended=True,
    # Worker-Einstellungen
    worker_max_tasks_per_child=50,  # Restart nach 50 Tasks
    worker_max_memory_per_child=1024000,  # 1 GB
    # Prioritäts-Warteschlangen
    task_default_priority=5,
    task_queue_max_priority=10,
)

# Queue-Konfiguration mit Prioritäten
celery_app.conf.task_queues = {
    "celery": {"exchange": "celery", "routing_key": "celery", "queue_arguments": {"x-max-priority": 10}},
    "scans.critical": {"exchange": "scans", "routing_key": "scans.critical", "queue_arguments": {"x-max-priority": 10}},
    "scans.high": {"exchange": "scans", "routing_key": "scans.high", "queue_arguments": {"x-max-priority": 10}},
    "scans.normal": {"exchange": "scans", "routing_key": "scans.normal", "queue_arguments": {"x-max-priority": 10}},
    "scans.low": {"exchange": "scans", "routing_key": "scans.low", "queue_arguments": {"x-max-priority": 10}},
    "notifications": {
        "exchange": "notifications",
        "routing_key": "notifications",
    },
    "reports": {
        "exchange": "reports",
        "routing_key": "reports",
    },
}

# Routing-Regeln
celery_app.conf.task_routes = {
    "tasks.scan_tasks.execute_scheduled_scan": {"queue": "scans.normal"},
    "tasks.scan_tasks.execute_priority_scan": {"queue": "scans.critical"},
    "tasks.scan_tasks.run_scan_with_priority": {"queue": "scans.normal"},
    "tasks.scan_tasks.send_notification": {"queue": "notifications"},
    "tasks.scan_tasks.generate_scan_report": {"queue": "reports"},
}


# Beat-Schedule: Zeitgesteuerte Tasks
celery_app.conf.beat_schedule = {
    # Prüft alle 30 Sekunden auf fällige Scans
    "check-due-scans": {
        "task": "tasks.scan_tasks.check_and_queue_due_scans",
        "schedule": 30.0,  # 30 Sekunden
        "options": {"queue": "celery"},
    },
    # Bereinigt alte Einträge täglich um 3 Uhr
    "cleanup-old-history": {
        "task": "tasks.scan_tasks.cleanup_old_history",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "celery"},
    },
    # Aktualisiert nächste Ausführungen für Cron-Scans
    "update-cron-schedules": {
        "task": "tasks.scan_tasks.update_cron_schedules",
        "schedule": crontab(hour="*", minute=0),  # Jede Stunde
        "options": {"queue": "celery"},
    },
    # Sendet tägliche Zusammenfassung um 8 Uhr
    "daily-summary": {
        "task": "tasks.scan_tasks.send_daily_summary",
        "schedule": crontab(hour=8, minute=0),
        "options": {"queue": "notifications"},
    },
}


def get_queue_for_priority(priority: int) -> str:
    """
    Mappt Prioritäts-Level zu Queue-Namen

    Args:
        priority: Priorität (1-10, niedriger = wichtiger)

    Returns:
        Queue-Name
    """
    if priority <= 2:
        return "scans.critical"
    elif priority <= 4:
        return "scans.high"
    elif priority <= 7:
        return "scans.normal"
    else:
        return "scans.low"


def send_task_with_priority(task_name: str, args=None, kwargs=None, priority: int = 5, countdown: int = 0):
    """
    Sendet einen Task mit Priorität an die entsprechende Queue

    Args:
        task_name: Name des Tasks
        args: Positionale Argumente
        kwargs: Keyword-Argumente
        priority: Priorität (1-10)
        countdown: Verzögerung in Sekunden
    """
    queue = get_queue_for_priority(priority)

    return celery_app.send_task(task_name, args=args, kwargs=kwargs, queue=queue, priority=priority, countdown=countdown)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug-Task zur Überprüfung der Celery-Konfiguration"""
    return {"task_id": self.request.id, "status": "success", "message": "Celery is working correctly!"}


if __name__ == "__main__":
    celery_app.start()
