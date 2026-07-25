"""Схемы главной страницы."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class DashboardCounters(BaseModel):
    competitors: int
    topics: int
    articles: int
    scheduled: int
    published: int


class SetupStep(BaseModel):
    code: str
    title: str
    description: str
    done: bool
    progress: int
    action_label: str
    action_href: str


class ActivityItem(BaseModel):
    kind: str
    title: str
    subtitle: str | None = None
    href: str | None = None
    level: str = "info"
    happened_at: datetime | None = None
    entity_id: uuid.UUID | None = None


class DashboardResponse(BaseModel):
    project_id: uuid.UUID
    project_name: str
    greeting: str = "Ваш центр управления контентом Дзена"
    user_name: str | None = None
    counters: DashboardCounters
    setup_progress: int
    steps: list[SetupStep]
    activity: list[ActivityItem]
