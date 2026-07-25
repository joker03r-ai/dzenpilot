"""Поиск и хранение перспективных тем."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentUser, DbSession, Pagination, ProjectAuthor, ProjectViewer
from app.core.rate_limit import ai_rate_limit
from app.models.enums import TopicStatus
from app.schemas.common import MessageResponse, Page
from app.schemas.topic import (
    TopicCreate,
    TopicResponse,
    TopicSearchRequest,
    TopicSearchResponse,
    TopicUpdate,
)
from app.services import topic_service
from app.services.audit_service import write_audit

router = APIRouter()


@router.get("/{project_id}/topics", response_model=Page[TopicResponse], summary="Список тем")
async def list_topics(
    project: ProjectViewer,
    db: DbSession,
    params: Pagination,
    topic_status: TopicStatus | None = Query(default=None, alias="status"),
    min_score: int | None = Query(default=None, ge=0, le=100, description="Минимальная оценка"),
) -> Page[TopicResponse]:
    items, total = await topic_service.list_topics(
        db, project.id, params, status=topic_status, min_score=min_score
    )
    responses = [await topic_service.to_response(db, item) for item in items]
    # Сортировка по оценке: самые перспективные темы сверху
    responses.sort(key=lambda item: item.score.total_score if item.score else -1, reverse=True)
    return Page.build(responses, total, params)


@router.post(
    "/{project_id}/topics/search",
    response_model=TopicSearchResponse,
    summary="Подобрать темы",
    dependencies=[Depends(ai_rate_limit)],
)
async def search_topics(
    data: TopicSearchRequest,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> TopicSearchResponse:
    topics, note = await topic_service.search_topics(db, project, data, user.id)
    await write_audit(
        db,
        action="topic.search",
        user_id=user.id,
        project_id=project.id,
        entity_type="project",
        entity_id=project.id,
        request=request,
        payload={"niche": data.niche, "found": len(topics)},
    )
    await db.commit()

    responses = [await topic_service.to_response(db, topic) for topic in topics]
    responses.sort(key=lambda item: item.score.total_score if item.score else -1, reverse=True)

    return TopicSearchResponse(
        created=len(responses),
        topics=responses,
        message=(
            f"Подобрано тем: {len(responses)}. Сверху — с самой высокой оценкой."
            if responses
            else "Не удалось подобрать темы. Уточните нишу и попробуйте ещё раз."
        ),
        sources_note=note,
    )


@router.post(
    "/{project_id}/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить тему вручную",
)
async def create_topic(
    data: TopicCreate, project: ProjectAuthor, user: CurrentUser, db: DbSession
) -> TopicResponse:
    topic = await topic_service.create_topic(db, project.id, data, user.id)
    await db.commit()
    await db.refresh(topic)
    return await topic_service.to_response(db, topic)


@router.get(
    "/{project_id}/topics/{topic_id}", response_model=TopicResponse, summary="Карточка темы"
)
async def get_topic(
    topic_id: uuid.UUID, project: ProjectViewer, db: DbSession
) -> TopicResponse:
    topic = await topic_service.get_topic(db, project.id, topic_id)
    return await topic_service.to_response(db, topic)


@router.patch(
    "/{project_id}/topics/{topic_id}", response_model=TopicResponse, summary="Изменить тему"
)
async def update_topic(
    topic_id: uuid.UUID,
    data: TopicUpdate,
    project: ProjectAuthor,
    db: DbSession,
) -> TopicResponse:
    topic = await topic_service.get_topic(db, project.id, topic_id)
    await topic_service.update_topic(db, topic, data)
    await db.commit()
    await db.refresh(topic)
    return await topic_service.to_response(db, topic)


@router.delete(
    "/{project_id}/topics/{topic_id}", response_model=MessageResponse, summary="Удалить тему"
)
async def delete_topic(
    topic_id: uuid.UUID, project: ProjectAuthor, db: DbSession
) -> MessageResponse:
    topic = await topic_service.get_topic(db, project.id, topic_id)
    await topic_service.delete_topic(db, topic)
    await db.commit()
    return MessageResponse(message="Тема удалена")
