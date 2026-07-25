"""Схемы интеграций. Секреты наружу не отдаются — только маска."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import IntegrationKind


class IntegrationCreate(BaseModel):
    kind: IntegrationKind
    title: str = Field(default="Основное", max_length=255)
    api_key: str | None = Field(
        default=None, max_length=500, description="Секретный ключ. Сохраняется в зашифрованном виде"
    )
    config: dict[str, Any] = Field(default_factory=dict)


class IntegrationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    api_key: str | None = Field(default=None, max_length=500)
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class IntegrationResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    kind: IntegrationKind
    kind_label: str
    title: str
    key_mask: str
    has_credentials: bool
    config: dict[str, Any]
    is_active: bool
    last_check_at: datetime | None
    last_check_result: str | None
    created_at: datetime


class IntegrationTestResult(BaseModel):
    ok: bool
    message: str
    checked_at: datetime
