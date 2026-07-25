"""Фоновые задачи.

На этом этапе реализованы служебные задачи и каркас плановых публикаций.
Задачи анализа конкурентов, подбора тем и генерации статей подключаются
на следующих этапах — точки расширения уже подготовлены.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.calendar import ScheduledPublication
from app.models.enums import JobStatus, ScheduleStatus
from app.models.job import JobRun
from app.workers.celery_app import celery_app

logger = logging.getLogger("dzenpilot.tasks")


def run_async(coroutine) -> Any:
    """Запускает корутину внутри синхронной задачи Celery."""
    return asyncio.run(coroutine)


@celery_app.task(name="app.workers.tasks.ping")
def ping() -> str:
    """Проверка, что worker жив."""
    return "pong"


@celery_app.task(name="app.workers.tasks.process_due_publications")
def process_due_publications() -> dict[str, int]:
    """Ищет публикации, чьё время наступило.

    Публикация никогда не отправляется без подтверждения пользователя:
    без confirmed_by_user запись только переводится в статус «Готова к публикации».
    """
    return run_async(_process_due_publications())


async def _process_due_publications() -> dict[str, int]:
    now = datetime.now(UTC)
    marked_ready = 0
    waiting_confirmation = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledPublication).where(
                ScheduledPublication.status == ScheduleStatus.PLANNED,
                ScheduledPublication.scheduled_at <= now,
            )
        )
        for schedule in result.scalars().all():
            if schedule.confirmed_by_user:
                schedule.status = ScheduleStatus.READY
                marked_ready += 1
            else:
                waiting_confirmation += 1
        await db.commit()

    logger.info(
        "Плановые публикации: готовы %s, ждут подтверждения %s",
        marked_ready,
        waiting_confirmation,
    )
    return {"ready": marked_ready, "waiting_confirmation": waiting_confirmation}


@celery_app.task(name="app.workers.tasks.refresh_analytics")
def refresh_analytics() -> dict[str, str]:
    """Обновление аналитики. Полная реализация — этап 8."""
    return {"status": "Задача выполнена, автоматических источников пока не подключено"}


@celery_app.task(name="app.workers.tasks.retry_failed_jobs")
def retry_failed_jobs() -> dict[str, int]:
    """Помечает задачи, застрявшие в статусе «Выполняется» дольше часа."""
    return run_async(_retry_failed_jobs())


async def _retry_failed_jobs() -> dict[str, int]:
    stuck = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(JobRun).where(JobRun.status == JobStatus.RUNNING))
        now = datetime.now(UTC)
        for job in result.scalars().all():
            if job.started_at and (now - job.started_at).total_seconds() > 3600:
                job.status = JobStatus.ERROR
                job.error_message = "Задача не завершилась за час и была остановлена"
                job.finished_at = now
                stuck += 1
        await db.commit()
    return {"stopped": stuck}
