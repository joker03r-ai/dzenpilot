from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ScheduleStatus
from app.models.pg_enums import schedule_status_enum


class ContentPlan(Base, UUIDMixin, TimestampMixin):
    """Контент-план на период. Объединяет запланированные публикации."""

    __tablename__ = "content_plans"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    publications: Mapped[list["ScheduledPublication"]] = relationship(
        back_populates="content_plan"
    )


class ScheduledPublication(Base, UUIDMixin, TimestampMixin):
    """Запись календаря: когда и куда публикуется статья.

    scheduled_at всегда хранится в UTC, а timezone — это пояс, выбранный
    пользователем для отображения (по умолчанию Europe/Moscow, UTC+3).
    """

    __tablename__ = "scheduled_publications"
    __table_args__ = (
        Index("ix_scheduled_publications_project_time", "project_id", "scheduled_at"),
        Index("ix_scheduled_publications_status_time", "status", "scheduled_at"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    content_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("content_plans.id", ondelete="SET NULL")
    )
    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("integrations.id", ondelete="SET NULL")
    )

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow", nullable=False)
    repeat_rule: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(Text)

    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ScheduleStatus] = mapped_column(
        schedule_status_enum, default=ScheduleStatus.PLANNED, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    content_plan: Mapped["ContentPlan | None"] = relationship(back_populates="publications")
