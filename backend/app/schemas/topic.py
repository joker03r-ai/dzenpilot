"""Схемы поиска тем и карточки темы."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import CompetitionLevel, TopicOrigin, TopicStatus
from app.schemas.common import ORMModel

TopicGoal = Literal["views", "subscribers", "leads", "income"]

GOAL_LABELS: dict[str, str] = {
    "views": "Просмотры",
    "subscribers": "Подписчики",
    "leads": "Заявки",
    "income": "Доход",
}


class TopicSearchRequest(BaseModel):
    """Параметры подбора тем. Заполняется пользователем в форме поиска."""

    niche: str = Field(min_length=2, max_length=255, description="Ниша или тематика")
    audience: str | None = Field(default=None, max_length=1000, description="Кто читатели")
    region: str | None = Field(default="Россия", max_length=120)
    format: str | None = Field(default=None, max_length=120, description="Желаемый формат")
    period_days: int = Field(default=90, ge=7, le=365, description="Период анализа конкурентов")
    forbidden_topics: list[str] = Field(
        default_factory=list, max_length=50, description="Запрещённые темы"
    )
    competition_level: CompetitionLevel | None = Field(
        default=None, description="Желаемый уровень конкуренции"
    )
    goal: TopicGoal = Field(default="views", description="Цель: просмотры, подписчики, заявки, доход")
    count: int = Field(default=8, ge=3, le=15, description="Сколько тем предложить")


class TopicCreate(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    niche: str | None = Field(default=None, max_length=255)
    audience: str | None = Field(default=None, max_length=500)
    region: str | None = Field(default=None, max_length=120)
    format: str | None = Field(default=None, max_length=120)
    competition_level: CompetitionLevel | None = None
    seasonality: str | None = Field(default=None, max_length=255)
    recommended_length: int | None = Field(default=None, ge=500, le=50000)


class TopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    status: TopicStatus | None = None
    format: str | None = Field(default=None, max_length=120)
    recommended_length: int | None = Field(default=None, ge=500, le=50000)


class ScoreBreakdown(BaseModel):
    """Расшифровка оценки: из чего сложился балл."""

    interest: int
    growth: int
    competition: int
    seasonality: int
    competitor_success: int
    series_potential: int
    commercial: int
    difficulty: int
    decay_risk: int
    audience_fit: int


class TopicScoreResponse(BaseModel):
    total_score: int
    verdict: str
    explanation: str
    breakdown: ScoreBreakdown
    formula_version: str
    created_at: datetime


class TopicResponse(ORMModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    niche: str | None
    audience: str | None
    region: str | None
    format: str | None
    competition_level: CompetitionLevel | None
    seasonality: str | None
    recommended_length: int | None

    title_variants: list[Any]
    reader_questions: list[Any]
    series_ideas: list[Any]
    monetization: list[Any]
    risks: list[Any]
    sources: list[Any]

    status: TopicStatus
    origin: TopicOrigin
    created_at: datetime
    updated_at: datetime

    score: TopicScoreResponse | None = None


class TopicSearchResponse(BaseModel):
    created: int
    topics: list[TopicResponse]
    message: str
    sources_note: str


class TopicToArticleResponse(BaseModel):
    article_id: uuid.UUID
    message: str
