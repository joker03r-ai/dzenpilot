from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import CompetitorStatus, DataSource
from app.models.pg_enums import competitor_status_enum, data_source_enum

if TYPE_CHECKING:
    from app.models.project import Project


class Competitor(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Конкурент — канал Дзена, за которым следит пользователь.

    Числовые показатели допускают NULL. NULL означает «Данные недоступны» —
    сервис не придумывает значения, которых нет в источнике.
    """

    __tablename__ = "competitors"
    __table_args__ = (
        UniqueConstraint("project_id", "url", name="uq_competitors_project_url"),
        Index("ix_competitors_project_status", "project_id", "status"),
        Index("ix_competitors_project_group", "project_id", "group_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    niche: Mapped[str | None] = mapped_column(String(255))
    group_name: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)

    subscribers_count: Mapped[int | None] = mapped_column(Integer)
    publications_count: Mapped[int | None] = mapped_column(Integer)
    avg_publish_interval_days: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    avg_views: Mapped[int | None] = mapped_column(Integer)
    max_views: Mapped[int | None] = mapped_column(Integer)
    min_views: Mapped[int | None] = mapped_column(Integer)
    avg_engagement_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    avg_article_length: Mapped[int | None] = mapped_column(Integer)

    formats_used: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    frequent_topics: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    popular_title_words: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    media_usage: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    data_source: Mapped[DataSource] = mapped_column(
        data_source_enum, default=DataSource.MANUAL, nullable=False
    )
    status: Mapped[CompetitorStatus] = mapped_column(
        competitor_status_enum,
        default=CompetitorStatus.NEW,
        nullable=False,
    )
    last_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    project: Mapped["Project"] = relationship(back_populates="competitors")
    publications: Mapped[list["CompetitorPublication"]] = relationship(
        back_populates="competitor", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["CompetitorAnalysis"]] = relationship(
        back_populates="competitor", cascade="all, delete-orphan"
    )


class CompetitorPublication(Base, UUIDMixin, TimestampMixin):
    """Отдельная публикация конкурента с разбором заголовка."""

    __tablename__ = "competitor_publications"
    __table_args__ = (
        UniqueConstraint("competitor_id", "url", name="uq_competitor_publications_url"),
        Index("ix_competitor_publications_date", "competitor_id", "published_at"),
    )

    competitor_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competitors.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(700))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    views: Mapped[int | None] = mapped_column(Integer)
    reactions: Mapped[int | None] = mapped_column(Integer)
    comments_count: Mapped[int | None] = mapped_column(Integer)

    topic_guess: Mapped[str | None] = mapped_column(String(255))
    format: Mapped[str | None] = mapped_column(String(120))
    title_length: Mapped[int | None] = mapped_column(Integer)
    body_length: Mapped[int | None] = mapped_column(Integer)
    title_emotionality: Mapped[int | None] = mapped_column(Integer)
    has_numbers: Mapped[bool | None] = mapped_column(Boolean)
    has_question: Mapped[bool | None] = mapped_column(Boolean)
    has_cta: Mapped[bool | None] = mapped_column(Boolean)
    audience_guess: Mapped[str | None] = mapped_column(String(255))
    raw_excerpt: Mapped[str | None] = mapped_column(Text)

    data_source: Mapped[DataSource] = mapped_column(
        data_source_enum, default=DataSource.MANUAL, nullable=False
    )

    competitor: Mapped["Competitor"] = relationship(back_populates="publications")


class CompetitorAnalysis(Base, UUIDMixin, TimestampMixin):
    """Отчёт ИИ по конкуренту. Хранится вся история отчётов."""

    __tablename__ = "competitor_analyses"
    __table_args__ = (Index("ix_competitor_analyses_recent", "competitor_id", "created_at"),)

    competitor_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competitors.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    summary: Mapped[str | None] = mapped_column(Text)
    why_it_works: Mapped[str | None] = mapped_column(Text)
    publish_rhythm: Mapped[str | None] = mapped_column(Text)

    working_topics: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    working_titles: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    failed_posts: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    formats: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    strengths: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    weaknesses: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    content_gaps: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    differentiation: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    adaptable_ideas: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    ai_provider: Mapped[str | None] = mapped_column(String(60))
    ai_model: Mapped[str | None] = mapped_column(String(120))
    prompt_used: Mapped[str | None] = mapped_column(Text)
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))

    competitor: Mapped["Competitor"] = relationship(back_populates="analyses")
