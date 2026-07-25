"""Схемы модуля Publisher."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import PublicationMethod, PublicationResult


class PreflightCheck(BaseModel):
    code: str
    label: str
    passed: bool
    detail: str


class PreflightResponse(BaseModel):
    checks: list[PreflightCheck]
    ready: bool
    available_methods: list[dict[str, str]]
    message: str


class ConfirmRequest(BaseModel):
    confirmed: bool = Field(description="Явное подтверждение публикации пользователем")


class PublishRequest(BaseModel):
    method: PublicationMethod = Field(
        default=PublicationMethod.MANUAL_EXPORT,
        description="Способ публикации",
    )
    force: bool = Field(
        default=False,
        description="Повторить, даже если публикация уже была выполнена успешно",
    )


class PublishResponse(BaseModel):
    log_id: uuid.UUID
    method: PublicationMethod
    method_label: str
    result: PublicationResult
    published_url: str | None
    error_message: str | None
    can_retry: bool
    payload: dict[str, Any]
    message: str
    next_step: str


class PublicationLogItem(BaseModel):
    id: uuid.UUID
    article_id: uuid.UUID
    article_title: str
    scheduled_publication_id: uuid.UUID | None
    method: PublicationMethod
    method_label: str
    result: PublicationResult
    result_label: str
    published_url: str | None
    error_message: str | None
    attempt_number: int
    response_payload: dict[str, Any]
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class ExportResponse(BaseModel):
    format: str
    filename: str
    content: str
    message: str
