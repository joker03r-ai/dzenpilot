"""Контент-календарь."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Query, Request, status

from app.api.deps import CurrentUser, DbSession, ProjectAuthor, ProjectViewer
from app.models.article import Article
from app.schemas.calendar import (
    REPEAT_LABELS,
    CalendarResponse,
    CalendarView,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.schemas.common import MessageResponse
from app.services import calendar_service
from app.services.audit_service import write_audit
from app.services.timezones import DEFAULT_TIMEZONE, TIMEZONE_CHOICES, all_timezones

router = APIRouter()


@router.get(
    "/{project_id}/calendar", response_model=CalendarResponse, summary="События календаря"
)
async def get_calendar(
    project: ProjectViewer,
    db: DbSession,
    view: CalendarView = Query(default="month", description="день, неделя, месяц или список"),
    anchor: date | None = Query(default=None, description="Опорная дата периода"),
    timezone: str | None = Query(default=None, description="Часовой пояс отображения"),
) -> CalendarResponse:
    return await calendar_service.list_calendar(
        db,
        project.id,
        view,
        anchor or date.today(),
        timezone or project.timezone or DEFAULT_TIMEZONE,
    )


@router.get(
    "/{project_id}/calendar/timezones",
    response_model=dict[str, object],
    summary="Часовые пояса и правила повторения",
)
async def calendar_options(_: ProjectViewer) -> dict[str, object]:
    return {
        "default": DEFAULT_TIMEZONE,
        "popular": TIMEZONE_CHOICES,
        "all": all_timezones(),
        "repeat_rules": [
            {"value": value, "label": label} for value, label in REPEAT_LABELS.items()
        ],
    }


@router.post(
    "/{project_id}/calendar",
    response_model=list[ScheduleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Запланировать публикацию",
)
async def create_schedule(
    data: ScheduleCreate,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> list[ScheduleResponse]:
    created = await calendar_service.create_schedule(db, project.id, data)
    await write_audit(
        db,
        action="calendar.schedule",
        user_id=user.id,
        project_id=project.id,
        entity_type="article",
        entity_id=data.article_id,
        request=request,
        payload={"count": len(created), "timezone": data.timezone},
    )
    await db.commit()

    responses: list[ScheduleResponse] = []
    for schedule in created:
        await db.refresh(schedule)
        article = await db.get(Article, schedule.article_id)
        responses.append(calendar_service.to_response(schedule, article))
    return responses


@router.patch(
    "/{project_id}/calendar/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Перенос, смена канала и заметки",
)
async def update_schedule(
    schedule_id: uuid.UUID,
    data: ScheduleUpdate,
    project: ProjectAuthor,
    db: DbSession,
) -> ScheduleResponse:
    schedule = await calendar_service.get_schedule(db, project.id, schedule_id)
    await calendar_service.update_schedule(db, schedule, data)
    await db.commit()
    await db.refresh(schedule)
    article = await db.get(Article, schedule.article_id)
    return calendar_service.to_response(schedule, article)


@router.post(
    "/{project_id}/calendar/{schedule_id}/duplicate",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Копировать публикацию",
)
async def duplicate_schedule(
    schedule_id: uuid.UUID,
    project: ProjectAuthor,
    db: DbSession,
    days_offset: int = Query(default=7, ge=1, le=365, description="Сдвиг копии в днях"),
) -> ScheduleResponse:
    schedule = await calendar_service.get_schedule(db, project.id, schedule_id)
    copy = await calendar_service.duplicate_schedule(db, schedule, days_offset)
    await db.commit()
    await db.refresh(copy)
    article = await db.get(Article, copy.article_id)
    return calendar_service.to_response(copy, article)


@router.delete(
    "/{project_id}/calendar/{schedule_id}",
    response_model=MessageResponse,
    summary="Отменить публикацию",
)
async def cancel_schedule(
    schedule_id: uuid.UUID,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> MessageResponse:
    schedule = await calendar_service.get_schedule(db, project.id, schedule_id)
    await calendar_service.cancel_schedule(db, schedule)
    await write_audit(
        db,
        action="calendar.cancel",
        user_id=user.id,
        project_id=project.id,
        entity_type="scheduled_publication",
        entity_id=schedule_id,
        request=request,
    )
    await db.commit()
    return MessageResponse(message="Публикация отменена")
