"""Общие зависимости: текущий пользователь, доступ к проекту, работа с cookie."""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AuthError
from app.core.security import create_token, decode_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginationParams
from app.services import auth_service, project_service

DbSession = Annotated[AsyncSession, Depends(get_db)]


def set_auth_cookies(response: Response, user_id: uuid.UUID) -> None:
    """Кладёт токены в httpOnly-cookie: JavaScript их прочитать не может."""
    access = create_token(str(user_id), "access")
    refresh = create_token(str(user_id), "refresh")
    common = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
    }
    if settings.cookie_domain:
        common["domain"] = settings.cookie_domain

    response.set_cookie(
        settings.access_cookie_name,
        access,
        max_age=settings.access_token_expire_minutes * 60,
        **common,
    )
    response.set_cookie(
        settings.refresh_cookie_name,
        refresh,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        **common,
    )


def clear_auth_cookies(response: Response) -> None:
    for name in (settings.access_cookie_name, settings.refresh_cookie_name):
        response.delete_cookie(
            name, path="/", domain=settings.cookie_domain or None
        )


async def get_current_user(request: Request, db: DbSession) -> User:
    token = request.cookies.get(settings.access_cookie_name)
    if not token:
        raise AuthError("Требуется вход в сервис")
    try:
        payload = decode_token(token, expected_type="access")
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Сессия истекла. Войдите заново.", code="token_expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Недействительный токен доступа") from exc

    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except (ValueError, TypeError) as exc:
        raise AuthError("Недействительный токен доступа") from exc

    user = await auth_service.get_user(db, user_id)
    request.state.user_id = str(user.id)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def project_access(min_role: UserRole = UserRole.VIEWER):
    """Зависимость доступа к проекту с проверкой роли."""

    async def dependency(project_id: uuid.UUID, db: DbSession, user: CurrentUser) -> Project:
        return await project_service.get_project_for_user(db, project_id, user.id, min_role)

    return dependency


ProjectViewer = Annotated[Project, Depends(project_access(UserRole.VIEWER))]
ProjectAuthor = Annotated[Project, Depends(project_access(UserRole.AUTHOR))]
ProjectEditor = Annotated[Project, Depends(project_access(UserRole.EDITOR))]
ProjectOwner = Annotated[Project, Depends(project_access(UserRole.OWNER))]

Pagination = Annotated[PaginationParams, Depends()]
