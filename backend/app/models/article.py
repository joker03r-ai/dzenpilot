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
from app.models.enums import ArticleStatus
from app.models.pg_enums import article_status_enum

if TYPE_CHECKING:
    from app.models.project import Project


class Article(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Статья: от черновика до опубликованного материала."""

    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_project_status", "project_id", "status"),
        Index("ix_articles_project_planned", "project_id", "planned_publish_at"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(500))
    lead: Mapped[str | None] = mapped_column(Text)
    body_markdown: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    outline: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    keywords: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    cta: Mapped[str | None] = mapped_column(Text)
    goal: Mapped[str | None] = mapped_column(String(500))
    audience: Mapped[str | None] = mapped_column(String(500))
    tone: Mapped[str | None] = mapped_column(String(120))
    target_length: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[ArticleStatus] = mapped_column(
        article_status_enum, default=ArticleStatus.DRAFT, nullable=False
    )
    checklist: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    generation_input: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    planned_publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_url: Mapped[str | None] = mapped_column(String(700))
    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("integrations.id", ondelete="SET NULL")
    )

    ai_provider: Mapped[str | None] = mapped_column(String(60))
    ai_model: Mapped[str | None] = mapped_column(String(120))
    prompt_used: Mapped[str | None] = mapped_column(Text)
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))

    word_count: Mapped[int | None] = mapped_column(Integer)
    reading_time_min: Mapped[int | None] = mapped_column(Integer)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    project: Mapped["Project"] = relationship(back_populates="articles")
    versions: Mapped[list["ArticleVersion"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="ArticleVersion.version_number",
    )
    images: Mapped[list["ArticleImage"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="ArticleImage.position",
    )


class ArticleVersion(Base, UUIDMixin, TimestampMixin):
    """Снимок статьи. Нужен для автосохранения и отката к прошлой версии."""

    __tablename__ = "article_versions"
    __table_args__ = (
        UniqueConstraint("article_id", "version_number", name="uq_article_versions_number"),
    )

    article_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    lead: Mapped[str | None] = mapped_column(Text)
    body_markdown: Mapped[str | None] = mapped_column(Text)
    outline: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    article: Mapped["Article"] = relationship(back_populates="versions")


class ArticleImage(Base, UUIDMixin, TimestampMixin):
    """Изображение статьи. Обложка помечается флагом is_cover."""

    __tablename__ = "article_images"
    __table_args__ = (Index("ix_article_images_order", "article_id", "position"),)

    article_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str | None] = mapped_column(String(700))
    storage_key: Mapped[str | None] = mapped_column(String(500))
    alt_text: Mapped[str | None] = mapped_column(String(500))
    prompt_used: Mapped[str | None] = mapped_column(Text)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)

    article: Mapped["Article"] = relationship(back_populates="images")
