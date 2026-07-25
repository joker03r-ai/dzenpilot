"""Учёт запусков фоновых задач.

Каждая задача создаёт запись в job_runs, чтобы пользователь видел статус,
прогресс, результат и текст ошибки, а не «зависшую» кнопку.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import JobStatus
from app.models.job import JobRun


async def create_job(
    db: AsyncSession,
    *,
    task_name: str,
    project_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
) -> JobRun:
    job = JobRun(
        task_name=task_name,
        project_id=project_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        status=JobStatus.PENDING,
        progress=0,
    )
    db.add(job)
    await db.flush()
    return job


async def start_job(db: AsyncSession, job_id: uuid.UUID, celery_task_id: str | None = None) -> None:
    job = await db.get(JobRun, job_id)
    if job is None:
        return
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(UTC)
    if celery_task_id:
        job.celery_task_id = celery_task_id
    await db.flush()


async def set_progress(db: AsyncSession, job_id: uuid.UUID, progress: int) -> None:
    job = await db.get(JobRun, job_id)
    if job is None:
        return
    job.progress = max(0, min(100, progress))
    await db.flush()


async def finish_job(
    db: AsyncSession, job_id: uuid.UUID, result: dict[str, Any] | None = None
) -> None:
    job = await db.get(JobRun, job_id)
    if job is None:
        return
    job.status = JobStatus.SUCCESS
    job.progress = 100
    job.finished_at = datetime.now(UTC)
    job.result = result or {}
    await db.flush()


async def fail_job(db: AsyncSession, job_id: uuid.UUID, message: str) -> None:
    job = await db.get(JobRun, job_id)
    if job is None:
        return
    job.status = JobStatus.ERROR
    job.finished_at = datetime.now(UTC)
    job.error_message = message[:2000]
    job.retries += 1
    await db.flush()
