"""Аналитика проекта."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse

from app.api.deps import CurrentUser, DbSession, ProjectAuthor, ProjectViewer
from app.core.errors import ValidationAppError
from app.schemas.analytics import (
    ComparisonResponse,
    CsvImportSummary,
    HourStat,
    ManualStatInput,
    OverviewResponse,
    Period,
    TimeseriesResponse,
    TopResponse,
    WeekdayStat,
)
from app.schemas.common import MessageResponse
from app.services import analytics_service
from app.services.audit_service import write_audit

router = APIRouter()

MAX_CSV_SIZE = 5 * 1024 * 1024


def _period(
    period: Period, start: date | None, end: date | None
) -> tuple[date, date]:
    return analytics_service.resolve_period(period, start, end)


@router.get(
    "/{project_id}/analytics/overview",
    response_model=OverviewResponse,
    summary="Сводка за период",
)
async def overview(
    project: ProjectViewer,
    db: DbSession,
    period: Period = Query(default="30d"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> OverviewResponse:
    period_start, period_end = _period(period, start, end)
    return await analytics_service.build_overview(db, project.id, period_start, period_end)


@router.get(
    "/{project_id}/analytics/timeseries",
    response_model=TimeseriesResponse,
    summary="Динамика просмотров и подписчиков",
)
async def timeseries(
    project: ProjectViewer,
    db: DbSession,
    period: Period = Query(default="30d"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> TimeseriesResponse:
    period_start, period_end = _period(period, start, end)
    return await analytics_service.build_timeseries(db, project.id, period_start, period_end)


@router.get(
    "/{project_id}/analytics/by-weekday",
    response_model=list[WeekdayStat],
    summary="Результат по дням недели",
)
async def by_weekday(
    project: ProjectViewer,
    db: DbSession,
    period: Period = Query(default="90d"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> list[WeekdayStat]:
    period_start, period_end = _period(period, start, end)
    return await analytics_service.build_weekday_stats(db, project.id, period_start, period_end)


@router.get(
    "/{project_id}/analytics/by-hour",
    response_model=list[HourStat],
    summary="Результат по времени публикации",
)
async def by_hour(
    project: ProjectViewer,
    db: DbSession,
    period: Period = Query(default="90d"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> list[HourStat]:
    period_start, period_end = _period(period, start, end)
    return await analytics_service.build_hour_stats(db, project.id, period_start, period_end)


@router.get(
    "/{project_id}/analytics/top",
    response_model=TopResponse,
    summary="Лучшие статьи, темы и заголовки",
)
async def top(
    project: ProjectViewer,
    db: DbSession,
    period: Period = Query(default="90d"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> TopResponse:
    period_start, period_end = _period(period, start, end)
    return await analytics_service.build_top(db, project.id, period_start, period_end)


@router.get(
    "/{project_id}/analytics/comparison",
    response_model=ComparisonResponse,
    summary="Сравнение с конкурентами",
)
async def comparison(
    project: ProjectViewer,
    db: DbSession,
    period: Period = Query(default="90d"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> ComparisonResponse:
    period_start, period_end = _period(period, start, end)
    return await analytics_service.build_comparison(db, project.id, period_start, period_end)


@router.post(
    "/{project_id}/analytics/manual",
    response_model=MessageResponse,
    summary="Ручной ввод статистики",
)
async def add_manual(
    data: ManualStatInput, project: ProjectAuthor, db: DbSession
) -> MessageResponse:
    await analytics_service.save_manual(db, project.id, data)
    await db.commit()
    return MessageResponse(message="Данные сохранены")


@router.post(
    "/{project_id}/analytics/import-csv",
    response_model=CsvImportSummary,
    summary="Импорт статистики из CSV",
)
async def import_csv(
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
    file: UploadFile = File(..., description="CSV с колонкой «Дата»"),
) -> CsvImportSummary:
    content = await file.read()
    if len(content) > MAX_CSV_SIZE:
        raise ValidationAppError("Файл больше 5 МБ. Разделите его на части.")
    if not content:
        raise ValidationAppError("Файл пустой")

    result = await analytics_service.import_csv(db, project.id, content)
    await write_audit(
        db,
        action="analytics.import_csv",
        user_id=user.id,
        project_id=project.id,
        entity_type="project",
        entity_id=project.id,
        request=request,
        payload={"created": result.created, "updated": result.updated},
    )
    await db.commit()
    return result


@router.get(
    "/{project_id}/analytics/export",
    response_class=PlainTextResponse,
    summary="Выгрузка статистики в CSV",
)
async def export_csv(
    project: ProjectViewer,
    db: DbSession,
    period: Period = Query(default="90d"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
) -> PlainTextResponse:
    period_start, period_end = _period(period, start, end)
    content = await analytics_service.export_csv(db, project.id, period_start, period_end)

    return PlainTextResponse(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="analytics-{period_start}-{period_end}.csv"'
        },
    )
