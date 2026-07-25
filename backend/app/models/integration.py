from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import IntegrationKind
from app.models.pg_enums import integration_kind_enum


class Integration(Base, UUIDMixin, TimestampMixin):
    """Подключение внешнего сервиса.

    Секреты лежат в credentials_encrypted (шифрование Fernet) и никогда
    не передаются во frontend — наружу уходит только маска ключа.
    """

    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint("project_id", "kind", "title", name="uq_integrations_project_kind_title"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[IntegrationKind] = mapped_column(integration_kind_enum, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="Основное", nullable=False)
    credentials_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_check_result: Mapped[str | None] = mapped_column(Text)
