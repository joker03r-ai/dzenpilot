"""Мастер создания статьи, библиотека и версии."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, Pagination, ProjectAuthor, ProjectViewer
from app.core.rate_limit import ai_rate_limit
from app.models.article import ArticleImage
from app.models.enums import ArticleStatus
from app.schemas.article import (
    IMPROVE_LABELS,
    ADVISORY_ACTIONS,
    ArticleCreate,
    ArticleListItem,
    ArticleResponse,
    ArticleUpdate,
    ArticleVersionResponse,
    ChecklistResponse,
    GenerateRequest,
    ImproveRequest,
    ImproveResponse,
    OutlineResponse,
)
from app.schemas.common import MessageResponse, Page
from app.services import article_generation, article_service
from app.services.audit_service import write_audit

router = APIRouter()


@router.get(
    "/{project_id}/articles",
    response_model=Page[ArticleListItem],
    summary="Библиотека статей",
)
async def list_articles(
    project: ProjectViewer,
    db: DbSession,
    params: Pagination,
    article_status: ArticleStatus | None = Query(default=None, alias="status"),
) -> Page[ArticleListItem]:
    items, total = await article_service.list_articles(
        db, project.id, params, status=article_status
    )
    return Page.build([article_service.to_list_item(item) for item in items], total, params)


@router.post(
    "/{project_id}/articles",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Шаг 1: создать черновик",
)
async def create_article(
    data: ArticleCreate,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> ArticleResponse:
    article = await article_service.create_article(db, project.id, data, user.id)
    await write_audit(
        db,
        action="article.create",
        user_id=user.id,
        project_id=project.id,
        entity_type="article",
        entity_id=article.id,
        request=request,
    )
    await db.commit()
    await db.refresh(article)
    return await article_service.to_response(db, article)


@router.get(
    "/{project_id}/articles/{article_id}",
    response_model=ArticleResponse,
    summary="Статья целиком",
)
async def get_article(
    article_id: uuid.UUID, project: ProjectViewer, db: DbSession
) -> ArticleResponse:
    article = await article_service.get_article(db, project.id, article_id)
    return await article_service.to_response(db, article)


@router.patch(
    "/{project_id}/articles/{article_id}",
    response_model=ArticleResponse,
    summary="Сохранение и автосохранение",
)
async def update_article(
    article_id: uuid.UUID,
    data: ArticleUpdate,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
) -> ArticleResponse:
    article = await article_service.get_article(db, project.id, article_id)
    await article_service.update_article(db, article, data, user.id)
    await db.commit()
    await db.refresh(article)
    return await article_service.to_response(db, article)


@router.delete(
    "/{project_id}/articles/{article_id}",
    response_model=MessageResponse,
    summary="Перенести в архив",
)
async def delete_article(
    article_id: uuid.UUID, project: ProjectAuthor, db: DbSession
) -> MessageResponse:
    article = await article_service.get_article(db, project.id, article_id)
    await article_service.delete_article(db, article)
    await db.commit()
    return MessageResponse(message="Статья перенесена в архив")


@router.post(
    "/{project_id}/articles/{article_id}/outline",
    response_model=OutlineResponse,
    summary="Шаг 2: структура статьи",
    dependencies=[Depends(ai_rate_limit)],
)
async def build_outline(
    article_id: uuid.UUID, project: ProjectAuthor, db: DbSession
) -> OutlineResponse:
    article = await article_service.get_article(db, project.id, article_id)
    result = await article_generation.generate_outline(db, article, project)
    await db.commit()
    return result


@router.post(
    "/{project_id}/articles/{article_id}/generate",
    response_model=ArticleResponse,
    summary="Шаг 3: сгенерировать текст",
    dependencies=[Depends(ai_rate_limit)],
)
async def generate_body(
    article_id: uuid.UUID,
    data: GenerateRequest,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> ArticleResponse:
    article = await article_service.get_article(db, project.id, article_id)
    await article_generation.generate_body(db, article, project, data, user.id)
    await write_audit(
        db,
        action="article.generate",
        user_id=user.id,
        project_id=project.id,
        entity_type="article",
        entity_id=article.id,
        request=request,
    )
    await db.commit()
    await db.refresh(article)
    return await article_service.to_response(db, article)


@router.post(
    "/{project_id}/articles/{article_id}/improve",
    response_model=ImproveResponse,
    summary="Шаг 4: доработка текста",
    dependencies=[Depends(ai_rate_limit)],
)
async def improve_article(
    article_id: uuid.UUID,
    data: ImproveRequest,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
) -> ImproveResponse:
    article = await article_service.get_article(db, project.id, article_id)
    result, applied = await article_generation.improve(db, article, project, data, user.id)
    await db.commit()

    return ImproveResponse(
        action=data.action,
        action_label=IMPROVE_LABELS[data.action],
        changes_text=data.action not in ADVISORY_ACTIONS,
        result=result,
        applied=applied,
        message=(
            "Текст статьи обновлён. Предыдущая версия сохранена в истории."
            if applied
            else "Заключение готово. Текст статьи не изменялся."
        ),
    )


@router.get(
    "/{project_id}/articles/{article_id}/checklist",
    response_model=ChecklistResponse,
    summary="Шаг 5: проверка перед публикацией",
)
async def get_checklist(
    article_id: uuid.UUID, project: ProjectViewer, db: DbSession
) -> ChecklistResponse:
    article = await article_service.get_article(db, project.id, article_id)
    has_cover = bool(
        await db.scalar(
            select(func.count())
            .select_from(ArticleImage)
            .where(ArticleImage.article_id == article.id, ArticleImage.is_cover.is_(True))
        )
    )
    return article_service.build_checklist(article, has_cover)


@router.get(
    "/{project_id}/articles/{article_id}/versions",
    response_model=list[ArticleVersionResponse],
    summary="История изменений",
)
async def list_versions(
    article_id: uuid.UUID, project: ProjectViewer, db: DbSession
) -> list[ArticleVersionResponse]:
    article = await article_service.get_article(db, project.id, article_id)
    versions = await article_service.list_versions(db, article.id)
    return [ArticleVersionResponse.model_validate(item) for item in versions]


@router.post(
    "/{project_id}/articles/{article_id}/versions/{version_id}/restore",
    response_model=ArticleResponse,
    summary="Восстановить версию",
)
async def restore_version(
    article_id: uuid.UUID,
    version_id: uuid.UUID,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
) -> ArticleResponse:
    article = await article_service.get_article(db, project.id, article_id)
    await article_service.restore_version(db, article, version_id, user.id)
    await db.commit()
    await db.refresh(article)
    return await article_service.to_response(db, article)
