"""Publisher: предпроверка, подтверждение, публикация, журнал и экспорт."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession, ProjectAuthor, ProjectViewer
from app.core.errors import ValidationAppError
from app.models.enums import RU_LABELS
from app.schemas.publication import (
    ConfirmRequest,
    ExportResponse,
    PreflightResponse,
    PublicationLogItem,
    PublishRequest,
    PublishResponse,
)
from app.services import article_service, calendar_service, export_service, publisher
from app.services.audit_service import write_audit

router = APIRouter()


@router.post(
    "/{project_id}/publications/{schedule_id}/preflight",
    response_model=PreflightResponse,
    summary="Проверка перед публикацией",
)
async def preflight(
    schedule_id: uuid.UUID, project: ProjectViewer, db: DbSession
) -> PreflightResponse:
    schedule = await calendar_service.get_schedule(db, project.id, schedule_id)
    return await publisher.preflight(db, schedule)


@router.post(
    "/{project_id}/publications/{schedule_id}/confirm",
    response_model=PreflightResponse,
    summary="Подтвердить публикацию",
)
async def confirm(
    schedule_id: uuid.UUID,
    data: ConfirmRequest,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> PreflightResponse:
    if not data.confirmed:
        raise ValidationAppError(
            "Подтверждение не получено. Публикация выполняется только по вашему решению."
        )

    schedule = await calendar_service.get_schedule(db, project.id, schedule_id)
    schedule.confirmed_by_user = True
    await write_audit(
        db,
        action="publication.confirm",
        user_id=user.id,
        project_id=project.id,
        entity_type="scheduled_publication",
        entity_id=schedule.id,
        request=request,
    )
    await db.commit()
    await db.refresh(schedule)
    return await publisher.preflight(db, schedule)


@router.post(
    "/{project_id}/publications/{schedule_id}/publish",
    response_model=PublishResponse,
    summary="Опубликовать выбранным способом",
)
async def publish(
    schedule_id: uuid.UUID,
    data: PublishRequest,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> PublishResponse:
    schedule = await calendar_service.get_schedule(db, project.id, schedule_id)
    result = await publisher.publish(db, schedule, data)
    await write_audit(
        db,
        action="publication.publish",
        user_id=user.id,
        project_id=project.id,
        entity_type="scheduled_publication",
        entity_id=schedule.id,
        request=request,
        payload={"method": data.method.value, "result": result.result.value},
    )
    await db.commit()
    return result


@router.post(
    "/{project_id}/publications/{schedule_id}/retry",
    response_model=PublishResponse,
    summary="Повторить попытку",
)
async def retry(
    schedule_id: uuid.UUID,
    data: PublishRequest,
    project: ProjectAuthor,
    db: DbSession,
) -> PublishResponse:
    schedule = await calendar_service.get_schedule(db, project.id, schedule_id)
    result = await publisher.publish(db, schedule, data)
    await db.commit()
    return result


@router.get(
    "/{project_id}/publications/logs",
    response_model=list[PublicationLogItem],
    summary="Журнал публикаций",
)
async def logs(
    project: ProjectViewer, db: DbSession, limit: int = Query(default=50, ge=1, le=200)
) -> list[PublicationLogItem]:
    rows = await publisher.list_logs(db, project.id, limit)
    return [
        PublicationLogItem(
            id=log.id,
            article_id=log.article_id,
            article_title=title,
            scheduled_publication_id=log.scheduled_publication_id,
            method=log.method,
            method_label=RU_LABELS["publication_method"].get(log.method, log.method),
            result=log.result,
            result_label={
                "success": "Успешно",
                "error": "Ошибка",
                "skipped": "Пропущено",
            }.get(log.result, log.result),
            published_url=log.published_url,
            error_message=log.error_message,
            attempt_number=log.attempt_number,
            response_payload=log.response_payload,
            started_at=log.started_at,
            finished_at=log.finished_at,
            created_at=log.created_at,
        )
        for log, title in rows
    ]


@router.get(
    "/{project_id}/articles/{article_id}/export",
    response_model=ExportResponse,
    summary="Экспорт статьи",
)
async def export_article(
    article_id: uuid.UUID,
    project: ProjectViewer,
    db: DbSession,
    export_format: str = Query(default="markdown", alias="format", pattern="^(markdown|html|plain)$"),
) -> ExportResponse:
    article = await article_service.get_article(db, project.id, article_id)
    slug = article.slug or "article"

    if export_format == "html":
        return ExportResponse(
            format="html",
            filename=f"{slug}.html",
            content=export_service.build_html(article),
            message="HTML-файл готов. Откройте его в браузере, чтобы посмотреть вёрстку.",
        )
    if export_format == "plain":
        return ExportResponse(
            format="plain",
            filename=f"{slug}.txt",
            content=export_service.build_plain(article),
            message="Текст готов к копированию в редактор Дзена.",
        )

    return ExportResponse(
        format="markdown",
        filename=f"{slug}.md",
        content=export_service.build_markdown(article),
        message="Файл Markdown готов к скачиванию.",
    )
