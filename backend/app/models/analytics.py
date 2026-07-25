from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import DataSource
from app.models.pg_enums import data_source_enum


class AnalyticsSnapshot(Base, UUIDMixin, TimestampMixin):
    """Срез статистики за день. article_id = NULL — сводка по всему проекту."""

    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "article_id",
            "captured_for",
            "source",
            name="uq_analytics_snapshots_day",
        ),
        Index("ix_analytics_snapshots_project_day", "project_id", "captured_for"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    captured_for: Mapped[date] = mapped_column(Date, nullable=False)

    views: Mapped[int | None] = mapped_column(Integer)
    reads: Mapped[int | None] = mapped_column(Integer)
    subscribers: Mapped[int | None] = mapped_column(Integer)
    reactions: Mapped[int | None] = mapped_column(Integer)
    comments_count: Mapped[int | None] = mapped_column(Integer)
    ctr: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))

    source: Mapped[DataSource] = mapped_column(
        data_source_enum, default=DataSource.MANUAL, nullable=False
    )
