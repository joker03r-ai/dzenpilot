from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import CompetitionLevel, TopicOrigin, TopicStatus
from app.models.pg_enums import competition_level_enum, topic_origin_enum, topic_status_enum

if TYPE_CHECKING:
    from app.models.project import Project


class Topic(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Тема будущей статьи с обоснованием перспективности."""

    __tablename__ = "topics"
    __table_args__ = (
        Index("ix_topics_project_status", "project_id", "status"),
        Index("ix_topics_project_created", "project_id", "created_at"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    niche: Mapped[str | None] = mapped_column(String(255))
    audience: Mapped[str | None] = mapped_column(String(500))
    region: Mapped[str | None] = mapped_column(String(120))
    format: Mapped[str | None] = mapped_column(String(120))
    competition_level: Mapped[CompetitionLevel | None] = mapped_column(competition_level_enum)
    seasonality: Mapped[str | None] = mapped_column(String(255))
    recommended_length: Mapped[int | None] = mapped_column(Integer)

    title_variants: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    reader_questions: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    series_ideas: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    monetization: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    risks: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    sources: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    status: Mapped[TopicStatus] = mapped_column(
        topic_status_enum, default=TopicStatus.SUGGESTED, nullable=False
    )
    origin: Mapped[TopicOrigin] = mapped_column(
        topic_origin_enum, default=TopicOrigin.MANUAL, nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    project: Mapped["Project"] = relationship(back_populates="topics")
    scores: Mapped[list["TopicScore"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan", order_by="TopicScore.created_at"
    )

    @property
    def latest_score(self) -> "TopicScore | None":
        return self.scores[-1] if self.scores else None


class TopicScore(Base, UUIDMixin, TimestampMixin):
    """Оценка темы от 0 до 100 с расшифровкой всех составляющих."""

    __tablename__ = "topic_scores"
    __table_args__ = (Index("ix_topic_scores_recent", "topic_id", "created_at"),)

    topic_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)

    interest_score: Mapped[int | None] = mapped_column(Integer)
    growth_score: Mapped[int | None] = mapped_column(Integer)
    competition_score: Mapped[int | None] = mapped_column(Integer)
    seasonality_score: Mapped[int | None] = mapped_column(Integer)
    competitor_success_score: Mapped[int | None] = mapped_column(Integer)
    series_potential_score: Mapped[int | None] = mapped_column(Integer)
    commercial_score: Mapped[int | None] = mapped_column(Integer)
    difficulty_score: Mapped[int | None] = mapped_column(Integer)
    decay_risk_score: Mapped[int | None] = mapped_column(Integer)
    audience_fit_score: Mapped[int | None] = mapped_column(Integer)

    explanation: Mapped[str | None] = mapped_column(Text)
    formula_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)

    topic: Mapped["Topic"] = relationship(back_populates="scores")
