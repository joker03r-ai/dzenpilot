"""Очередь фоновых задач Celery."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "dzenpilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,
)

# Расписание периодических задач.
celery_app.conf.beat_schedule = {
    "publish-due-articles": {
        "task": "app.workers.tasks.process_due_publications",
        "schedule": crontab(minute="*"),
    },
    "refresh-analytics": {
        "task": "app.workers.tasks.refresh_analytics",
        "schedule": crontab(hour="4", minute="0"),
    },
    "retry-failed-jobs": {
        "task": "app.workers.tasks.retry_failed_jobs",
        "schedule": crontab(minute="*/15"),
    },
}
