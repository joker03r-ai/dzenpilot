"""Статус фоновых задач."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import ForbiddenError, NotFoundError
from app.models.enums import RU_LABELS
from app.models.job import JobRun
from app.schemas.job import JobResponse
from app.services import project_service

router = APIRouter()


def _to_response(job: JobRun) -> JobResponse:
    return JobResponse(
        id=job.id,
        task_name=job.task_name,
        status=job.status,
        status_label=RU_LABELS["job_status"].get(job.status, job.status),
        progress=job.progress,
        started_at=job.started_at,
        finished_at=job.finished_at,
        result=job.result,
        error_message=job.error_message,
        retries=job.retries,
        created_at=job.created_at,
    )


@router.get("/{job_id}", response_model=JobResponse, summary="Статус задачи")
async def get_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser) -> JobResponse:
    job = await db.get(JobRun, job_id)
    if job is None:
        raise NotFoundError("Задача не найдена")
    if job.project_id is not None:
        await project_service.get_project_for_user(db, job.project_id, user.id)
    elif job.user_id != user.id:
        raise ForbiddenError("Нет доступа к этой задаче")
    return _to_response(job)


@router.get("", response_model=list[JobResponse], summary="Последние задачи проекта")
async def list_jobs(
    project_id: uuid.UUID, db: DbSession, user: CurrentUser, limit: int = 20
) -> list[JobResponse]:
    await project_service.get_project_for_user(db, project_id, user.id)
    result = await db.execute(
        select(JobRun)
        .where(JobRun.project_id == project_id)
        .order_by(JobRun.created_at.desc())
        .limit(min(limit, 100))
    )
    return [_to_response(job) for job in result.scalars().all()]
