from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AIProviderName
from app.models.pg_enums import ai_provider_name_enum


class AIProviderSettings(Base, UUIDMixin, TimestampMixin):
    """Какая модель используется в проекте. Смена модели не требует правки кода."""

    __tablename__ = "ai_provider_settings"
    __table_args__ = (
        UniqueConstraint("project_id", "provider", "model", name="uq_ai_settings_project_model"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[AIProviderName] = mapped_column(ai_provider_name_enum, nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    temperature: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal("0.70"), nullable=False
    )
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class PromptTemplate(Base, UUIDMixin, TimestampMixin):
    """Шаблон промта. project_id = NULL означает системный шаблон."""

    __tablename__ = "prompt_templates"
    __table_args__ = (
        UniqueConstraint("project_id", "code", "version", name="uq_prompt_templates_code"),
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class AIUsage(Base, UUIDMixin, TimestampMixin):
    """Расход токенов по каждой операции — для контроля стоимости."""

    __tablename__ = "ai_usage"
    __table_args__ = (Index("ix_ai_usage_project_created", "project_id", "created_at"),)

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    operation: Mapped[str] = mapped_column(String(120), nullable=False)
    tokens_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    entity_type: Mapped[str | None] = mapped_column(String(60))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
