"""Запись значимых действий в журнал."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    request: Request | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Добавляет запись в audit_logs. Коммит делает вызывающий код."""
    ip = None
    user_agent = None
    if request is not None:
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else None
        )
        user_agent = request.headers.get("User-Agent", "")[:500]

    db.add(
        AuditLog(
            user_id=user_id,
            project_id=project_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip,
            user_agent=user_agent,
            payload=payload or {},
        )
    )
