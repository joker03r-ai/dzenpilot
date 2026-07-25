from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import ProjectStatus
from app.models.pg_enums import project_status_enum

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.competitor import Competitor
    from app.models.topic import Topic
    from app.models.workspace import Workspace


class Project(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Проект — это отдельный канал Дзена со своими данными и настройками."""

    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_workspace_status", "workspace_id", "status"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    niche: Mapped[str | None] = mapped_column(String(255))
    target_audience: Mapped[str | None] = mapped_column(Text)
    tone_of_voice: Mapped[str | None] = mapped_column(String(255))
    region: Mapped[str | None] = mapped_column(String(120), default="Россия")
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow", nullable=False)
    dzen_channel_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ProjectStatus] = mapped_column(
        project_status_enum, default=ProjectStatus.ACTIVE, nullable=False
    )
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="projects")
    competitors: Mapped[list["Competitor"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    topics: Mapped[list["Topic"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    articles: Mapped[list["Article"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Project {self.name}>"
