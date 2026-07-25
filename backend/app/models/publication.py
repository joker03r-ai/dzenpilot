from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import PublicationMethod, PublicationResult
from app.models.pg_enums import publication_method_enum, publication_result_enum


class PublicationLog(Base, UUIDMixin, TimestampMixin):
    """Журнал публикаций: что, когда, каким способом и с каким результатом."""

    __tablename__ = "publication_logs"
    __table_args__ = (Index("ix_publication_logs_article_time", "article_id", "started_at"),)

    scheduled_publication_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("scheduled_publications.id", ondelete="SET NULL"),
        index=True,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    method: Mapped[PublicationMethod] = mapped_column(publication_method_enum, nullable=False)
    result: Mapped[PublicationResult] = mapped_column(publication_result_enum, nullable=False)
    published_url: Mapped[str | None] = mapped_column(String(700))
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
