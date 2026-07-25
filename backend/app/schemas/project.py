"""Схемы проектов и участников."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import ProjectStatus, UserRole
from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Название канала или проекта")
    description: str | None = Field(default=None, max_length=2000)
    niche: str | None = Field(default=None, max_length=255, description="Тематика")
    target_audience: str | None = Field(default=None, max_length=2000)
    tone_of_voice: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default="Россия", max_length=120)
    timezone: str = Field(default="Europe/Moscow", max_length=64)
    dzen_channel_url: str | None = Field(default=None, max_length=500)
    workspace_id: uuid.UUID | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    niche: str | None = Field(default=None, max_length=255)
    target_audience: str | None = Field(default=None, max_length=2000)
    tone_of_voice: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)
    dzen_channel_url: str | None = Field(default=None, max_length=500)
    status: ProjectStatus | None = None
    settings: dict[str, Any] | None = None


class ProjectResponse(ORMModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    niche: str | None
    target_audience: str | None
    tone_of_voice: str | None
    region: str | None
    timezone: str
    dzen_channel_url: str | None
    status: ProjectStatus
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MemberInvite(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.AUTHOR


class MemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    accepted_at: datetime | None
