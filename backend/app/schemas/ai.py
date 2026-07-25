"""Схемы настроек ИИ."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import AIProviderName


class ModelInfo(BaseModel):
    id: str
    title: str
    recommended: bool = False


class ProviderInfo(BaseModel):
    provider: AIProviderName
    title: str
    available: bool
    description: str
    models: list[ModelInfo]


class AISettingsUpdate(BaseModel):
    provider: AIProviderName
    model: str = Field(min_length=1, max_length=120)
    temperature: Decimal = Field(default=Decimal("0.7"), ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=256, le=64000)


class AISettingsResponse(BaseModel):
    id: uuid.UUID | None
    project_id: uuid.UUID
    provider: AIProviderName
    model: str
    temperature: Decimal
    max_tokens: int
    key_configured: bool


class AITestRequest(BaseModel):
    prompt: str = Field(
        default="Ответь одним предложением: сервис работает?",
        min_length=1,
        max_length=2000,
    )


class AITestResponse(BaseModel):
    ok: bool
    provider: str
    model: str
    text: str
    tokens_input: int
    tokens_output: int
