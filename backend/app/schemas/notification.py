"""Схемы уведомлений."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.models.enums import NotificationLevel
from app.schemas.common import ORMModel


class NotificationResponse(ORMModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    kind: str
    title: str
    body: str | None
    level: NotificationLevel
    is_read: bool
    payload: dict[str, Any]
    created_at: datetime
