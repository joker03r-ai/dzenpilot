"""Схемы конкурентов, их публикаций и отчётов ИИ."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.enums import CompetitorStatus, DataSource
from app.schemas.common import ORMModel


class CompetitorCreate(BaseModel):
    """Конкурента можно добавить по ссылке, по названию или и тем и другим."""

    name: str = Field(min_length=1, max_length=255, description="Название канала")
    url: str | None = Field(default=None, max_length=500, description="Ссылка на канал")
    description: str | None = Field(default=None, max_length=2000)
    niche: str | None = Field(default=None, max_length=255, description="Тематика")
    group_name: str | None = Field(default=None, max_length=120, description="Группа")
    notes: str | None = Field(default=None, max_length=4000, description="Заметки")

    @field_validator("url")
    @classmethod
    def _normalize_url(cls, value: str | None) -> str | None:
        if not value:
            return None
        url = value.strip()
        if not url:
            return None
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return url.rstrip("/")


class CompetitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    niche: str | None = Field(default=None, max_length=255)
    group_name: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=4000)
    subscribers_count: int | None = Field(default=None, ge=0)


class CompetitorResponse(ORMModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    url: str | None
    description: str | None
    niche: str | None
    group_name: str | None
    notes: str | None

    subscribers_count: int | None
    publications_count: int | None
    avg_publish_interval_days: Decimal | None
    avg_views: int | None
    max_views: int | None
    min_views: int | None
    avg_engagement_rate: Decimal | None
    avg_article_length: int | None

    formats_used: list[Any]
    frequent_topics: list[Any]
    popular_title_words: list[Any]
    media_usage: dict[str, Any]

    data_source: DataSource
    status: CompetitorStatus
    last_analyzed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    stored_publications: int = 0
    has_analysis: bool = False


class PublicationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    url: str | None = Field(default=None, max_length=700)
    published_at: datetime | None = None
    views: int | None = Field(default=None, ge=0, description="Оставьте пустым, если неизвестно")
    reactions: int | None = Field(default=None, ge=0)
    comments_count: int | None = Field(default=None, ge=0)
    topic_guess: str | None = Field(default=None, max_length=255)
    format: str | None = Field(default=None, max_length=120)
    audience_guess: str | None = Field(default=None, max_length=255)
    raw_excerpt: str | None = Field(default=None, max_length=20000)


class PublicationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    url: str | None = Field(default=None, max_length=700)
    published_at: datetime | None = None
    views: int | None = Field(default=None, ge=0)
    reactions: int | None = Field(default=None, ge=0)
    comments_count: int | None = Field(default=None, ge=0)
    topic_guess: str | None = Field(default=None, max_length=255)
    format: str | None = Field(default=None, max_length=120)


class PublicationResponse(ORMModel):
    id: uuid.UUID
    competitor_id: uuid.UUID
    title: str
    url: str | None
    published_at: datetime | None
    views: int | None
    reactions: int | None
    comments_count: int | None
    topic_guess: str | None
    format: str | None
    title_length: int | None
    body_length: int | None
    title_emotionality: int | None
    has_numbers: bool | None
    has_question: bool | None
    has_cta: bool | None
    audience_guess: str | None
    data_source: DataSource
    created_at: datetime


class CsvImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str]
    message: str


class AnalysisResponse(ORMModel):
    id: uuid.UUID
    competitor_id: uuid.UUID
    summary: str | None
    why_it_works: str | None
    publish_rhythm: str | None
    working_topics: list[Any]
    working_titles: list[Any]
    failed_posts: list[Any]
    formats: list[Any]
    strengths: list[Any]
    weaknesses: list[Any]
    content_gaps: list[Any]
    differentiation: list[Any]
    adaptable_ideas: list[Any]
    ai_provider: str | None
    ai_model: str | None
    tokens_input: int | None
    tokens_output: int | None
    cost_usd: Decimal | None
    created_at: datetime


class CompareRequest(BaseModel):
    competitor_ids: list[uuid.UUID] = Field(
        min_length=2, max_length=10, description="От 2 до 10 конкурентов"
    )
    period_days: int = Field(default=90, ge=7, le=365, description="Период анализа")


class CompareRow(BaseModel):
    competitor_id: uuid.UUID
    name: str
    publish_interval_days: float | None
    publications_in_period: int
    avg_views: int | None
    max_views: int | None
    avg_engagement_rate: float | None
    avg_article_length: int | None
    best_topics: list[str]
    title_style: str
    dynamics_percent: float | None
    rating: int
    rating_reason: str


class ComparePoint(BaseModel):
    name: str
    avg_views: int | None
    publications: int
    engagement: float | None


class CompareResponse(BaseModel):
    period_days: int
    rows: list[CompareRow]
    chart: list[ComparePoint]
    note: str
