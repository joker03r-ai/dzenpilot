"""Схемы аналитики."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Period = Literal["7d", "30d", "90d", "custom"]

PERIOD_DAYS: dict[str, int] = {"7d": 7, "30d": 30, "90d": 90}


class MetricValue(BaseModel):
    """Показатель вместе с изменением к прошлому периоду.

    value = None означает «Данные недоступны», а не ноль.
    """

    value: int | float | None
    change_percent: float | None = None
    available: bool = True
    note: str | None = None


class OverviewResponse(BaseModel):
    period_start: date
    period_end: date
    published_articles: MetricValue
    total_views: MetricValue
    avg_views: MetricValue
    subscribers: MetricValue
    avg_engagement: MetricValue
    publish_frequency: MetricValue
    data_source_note: str


class TimeseriesPoint(BaseModel):
    day: date
    views: int | None
    subscribers: int | None
    published: int


class TimeseriesResponse(BaseModel):
    points: list[TimeseriesPoint]
    has_data: bool
    note: str


class WeekdayStat(BaseModel):
    weekday: int
    label: str
    published: int
    avg_views: int | None


class HourStat(BaseModel):
    hour: int
    label: str
    published: int
    avg_views: int | None


class TopArticle(BaseModel):
    article_id: uuid.UUID
    title: str
    views: int | None
    published_at: date | None
    reading_time_min: int | None


class TopTopic(BaseModel):
    title: str
    articles: int
    avg_views: int | None


class TopTitleWord(BaseModel):
    word: str
    count: int
    avg_views: int | None


class TopResponse(BaseModel):
    articles: list[TopArticle]
    topics: list[TopTopic]
    title_words: list[TopTitleWord]
    note: str


class CompetitorComparison(BaseModel):
    name: str
    avg_views: int | None
    publications: int
    is_you: bool = False


class ComparisonResponse(BaseModel):
    rows: list[CompetitorComparison]
    note: str


class ManualStatInput(BaseModel):
    """Ручной ввод статистики, когда автоматических данных нет."""

    article_id: uuid.UUID | None = Field(
        default=None, description="Пусто — сводка по всему проекту"
    )
    captured_for: date
    views: int | None = Field(default=None, ge=0)
    reads: int | None = Field(default=None, ge=0)
    subscribers: int | None = Field(default=None, ge=0)
    reactions: int | None = Field(default=None, ge=0)
    comments_count: int | None = Field(default=None, ge=0)


class CsvImportSummary(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str]
    message: str
