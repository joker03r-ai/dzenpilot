"""Регистрация, вход и работа с профилем."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.errors import AuthError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.ai import AIProviderSettings
from app.models.enums import AIProviderName, ProjectStatus, UserRole
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.strip().lower()))
    return result.scalars().first()


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthError("Пользователь не найден или заблокирован")
    return user


async def register_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str | None,
    project_name: str,
) -> tuple[User, Workspace, Project]:
    """Создаёт пользователя, его рабочее пространство и первый проект."""
    if await get_user_by_email(db, email) is not None:
        raise ConflictError("Пользователь с такой почтой уже зарегистрирован")

    user = User(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        full_name=(full_name or "").strip() or None,
    )
    db.add(user)
    await db.flush()

    workspace = Workspace(name=full_name or "Моё пространство", owner_id=user.id)
    db.add(workspace)
    await db.flush()

    db.add(
        WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=UserRole.OWNER,
            accepted_at=datetime.now(UTC),
        )
    )

    project = Project(
        workspace_id=workspace.id,
        name=project_name.strip() or "Мой канал",
        timezone="Europe/Moscow",
        region="Россия",
        status=ProjectStatus.ACTIVE,
        settings={},
    )
    db.add(project)
    await db.flush()

    # Настройки модели по умолчанию, чтобы генерация работала сразу после регистрации.
    db.add(
        AIProviderSettings(
            project_id=project.id,
            provider=AIProviderName(settings.ai_default_provider),
            model=settings.ai_default_model,
            is_default=True,
        )
    )
    await db.flush()
    return user, workspace, project


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    # Проверяем пароль даже при отсутствии пользователя, чтобы время ответа не выдавало,
    # зарегистрирована ли такая почта.
    dummy_hash = "$2b$12$" + "0" * 53
    if user is None:
        verify_password(password, dummy_hash)
        raise AuthError("Неверная почта или пароль")
    if not verify_password(password, user.password_hash):
        raise AuthError("Неверная почта или пароль")
    if not user.is_active:
        raise AuthError("Учётная запись отключена")

    user.last_login_at = datetime.now(UTC)
    return user


async def list_workspaces(db: AsyncSession, user_id: uuid.UUID) -> list[Workspace]:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
        .options(selectinload(Workspace.projects))
        .order_by(Workspace.created_at)
    )
    return list(result.scalars().unique().all())


async def default_project_id(db: AsyncSession, user_id: uuid.UUID) -> uuid.UUID | None:
    result = await db.execute(
        select(Project.id)
        .join(Workspace, Workspace.id == Project.workspace_id)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == user_id,
            Project.deleted_at.is_(None),
            Project.status != ProjectStatus.ARCHIVED,
        )
        .order_by(Project.created_at)
        .limit(1)
    )
    return result.scalars().first()


async def change_password(
    db: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Текущий пароль указан неверно")
    user.password_hash = hash_password(new_password)


async def delete_account(db: AsyncSession, user: User, password: str) -> None:
    """Полное удаление пользователя и всех связанных данных."""
    if not verify_password(password, user.password_hash):
        raise AuthError("Пароль указан неверно")
    db_user = await db.get(User, user.id)
    if db_user is None:
        raise NotFoundError("Пользователь не найден")
    await db.delete(db_user)
