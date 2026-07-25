"""Уведомления пользователя."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import NotFoundError
from app.models.notification import Notification
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationResponse

router = APIRouter()


@router.get("", response_model=list[NotificationResponse], summary="Список уведомлений")
async def list_notifications(
    db: DbSession, user: CurrentUser, only_unread: bool = False, limit: int = 30
) -> list[NotificationResponse]:
    statement = select(Notification).where(Notification.user_id == user.id)
    if only_unread:
        statement = statement.where(Notification.is_read.is_(False))
    result = await db.execute(
        statement.order_by(Notification.created_at.desc()).limit(min(limit, 100))
    )
    return [NotificationResponse.model_validate(item) for item in result.scalars().all()]


@router.post("/{notification_id}/read", response_model=MessageResponse, summary="Прочитано")
async def mark_read(
    notification_id: uuid.UUID, db: DbSession, user: CurrentUser
) -> MessageResponse:
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise NotFoundError("Уведомление не найдено")
    notification.is_read = True
    await db.commit()
    return MessageResponse(message="Уведомление отмечено прочитанным")


@router.post("/read-all", response_model=MessageResponse, summary="Прочитать все")
async def mark_all_read(db: DbSession, user: CurrentUser) -> MessageResponse:
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user.id, Notification.is_read.is_(False)
        )
    )
    for notification in result.scalars().all():
        notification.is_read = True
    await db.commit()
    return MessageResponse(message="Все уведомления отмечены прочитанными")
