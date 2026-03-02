"""Celery application configuration."""

import os

from celery import Celery

# In production, CELERY_BROKER_URL must be explicitly set
_env_broker_url = os.getenv("CELERY_BROKER_URL")
_env_result_backend = os.getenv("CELERY_RESULT_BACKEND")
_environment = os.getenv("ENVIRONMENT", "development")

if _env_broker_url:
    CELERY_BROKER_URL = _env_broker_url
elif _environment == "production":
    raise RuntimeError(
        "CELERY_BROKER_URL environment variable is required in production. "
        "Please configure a Redis service and set CELERY_BROKER_URL."
    )
else:
    # Development fallback
    CELERY_BROKER_URL = "redis://localhost:6379/1"

if _env_result_backend:
    CELERY_RESULT_BACKEND = _env_result_backend
elif _environment == "production":
    raise RuntimeError(
        "CELERY_RESULT_BACKEND environment variable is required in production. "
        "Please configure a Redis service and set CELERY_RESULT_BACKEND."
    )
else:
    # Development fallback
    CELERY_RESULT_BACKEND = "redis://localhost:6379/2"

celery_app = Celery(
    "nexus_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "worker.tasks.messages",
        "worker.tasks.moderation",
        "worker.tasks.economy",
        "worker.tasks.scheduled",
        "worker.tasks.keepalive",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "keep-services-awake": {
        "task": "worker.tasks.keepalive.ping_services",
        "schedule": 60.0,  # Every minute
    },
    "check-scheduled-messages": {
        "task": "worker.tasks.scheduled.check_scheduled_messages",
        "schedule": 60.0,  # Every minute
    },
    "update-member-activity": {
        "task": "worker.tasks.economy.process_daily_activity",
        "schedule": 300.0,  # Every 5 minutes
    },
    "cleanup-expired-warnings": {
        "task": "worker.tasks.moderation.cleanup_expired_warnings",
        "schedule": 3600.0,  # Every hour
    },
}

if __name__ == "__main__":
    celery_app.start()
