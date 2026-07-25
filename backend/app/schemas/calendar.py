"""Схемы контент-календаря."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ScheduleStatus
from app.services.timezones import DEFAULT_TIMEZONE, is_valid_timezone

CalendarView = Literal["day", "week", "month", "list"]

# Как часто повторять публикацию
RepeatRule = Literal["none", "daily", "weekly", "biweekly", "monthly"]

REPEAT_LABELS: dict[str, str] = {
    "none": "Без повторения",
    "daily": "Каждый день",
    "weekly": "Каждую неделю",
    "biweekly": "Раз в две недели",
    "monthly": "Каждый месяц",
}


class ScheduleCreate(BaseModel):
    """Дата и время задаются в выбранном часовом поясе, а не в UTC."""

    article_id: uuid.UUID
    local_datetime: str = Field(
        description="Местные дата и время в формате 2026-08-01T10:00",
        examples=["2026-08-01T10:00"],
    )
    timezone: str = Field(default=DEFAULT_TIMEZONE, max_length=64)
    channel_id: uuid.UUID | None = None
    repeat_rule: RepeatRule = "none"
    repeat_count: int = Field(default=1, ge=1, le=52, description="Сколько публикаций создать")
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, value: str) -> str:
        if not is_valid_timezone(value):
            raise ValueError(
                f"Неизвестный часовой пояс: {value}. "
                "Выберите пояс из списка, например Europe/Moscow."
            )
        return value

    @field_validator("local_datetime")
    @classmethod
    def _check_datetime(cls, value: str) -> str:
        try:
            datetime.fromisoformat(value.replace("Z", "").split("+")[0])
        except ValueError as exc:
            raise ValueError(
                "Дата и время указаны неверно. Ожидается формат 2026-08-01T10:00."
            ) from exc
        return value


class ScheduleUpdate(BaseModel):
    """Используется в том числе при переносе публикации мышью."""

    local_datetime: str | None = None
    timezone: str | None = Field(default=None, max_length=64)
    channel_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=2000)
    status: ScheduleStatus | None = None
    confirmed_by_user: bool | None = None

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, value: str | None) -> str | None:
        if value is not None and not is_valid_timezone(value):
            raise ValueError(f"Неизвестный часовой пояс: {value}")
        return value


class ScheduleResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    article_id: uuid.UUID
    article_title: str
    article_status: str
    channel_id: uuid.UUID | None

    scheduled_at: datetime
    local_datetime: str
    local_date: date
    local_time: str
    timezone: str
    timezone_label: str

    repeat_rule: str | None
    note: str | None
    confirmed_by_user: bool
    status: ScheduleStatus
    status_label: str
    attempts: int
    created_at: datetime


class CalendarResponse(BaseModel):
    view: CalendarView
    period_start: date
    period_end: date
    timezone: str
    timezone_label: str
    items: list[ScheduleResponse]
    note: str
