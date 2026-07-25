"""Схемы регистрации, входа и профиля."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import ORMModel

PASSWORD_HELP = "Пароль должен быть не короче 8 символов"


class RegisterRequest(BaseModel):
    email: EmailStr = Field(description="Электронная почта")
    password: str = Field(min_length=8, max_length=128, description=PASSWORD_HELP)
    full_name: str | None = Field(default=None, max_length=255, description="Имя")
    project_name: str = Field(
        default="Мой канал", max_length=255, description="Название первого проекта"
    )

    @field_validator("email")
    @classmethod
    def _lower(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _lower(cls, value: str) -> str:
        return value.strip().lower()


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128, description=PASSWORD_HELP)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirm: bool = Field(description="Подтверждение удаления всех данных")


class WorkspaceShort(ORMModel):
    id: uuid.UUID
    name: str


class UserResponse(ORMModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserResponse
    workspaces: list[WorkspaceShort]
    default_project_id: uuid.UUID | None = None
    message: str = "Вход выполнен"
