"""Регистрация, вход, выход и профиль."""

from __future__ import annotations

import uuid

import jwt
from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import CurrentUser, DbSession, clear_auth_cookies, set_auth_cookies
from app.core.config import settings
from app.core.errors import AuthError
from app.core.rate_limit import auth_rate_limit
from app.core.security import decode_token
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    DeleteAccountRequest,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserResponse,
    WorkspaceShort,
)
from app.schemas.common import MessageResponse
from app.services import auth_service
from app.services.audit_service import write_audit

router = APIRouter()


async def _auth_payload(db: DbSession, user, message: str) -> AuthResponse:
    workspaces = await auth_service.list_workspaces(db, user.id)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        workspaces=[WorkspaceShort.model_validate(ws) for ws in workspaces],
        default_project_id=await auth_service.default_project_id(db, user.id),
        message=message,
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация",
    dependencies=[Depends(auth_rate_limit)],
)
async def register(
    data: RegisterRequest, request: Request, response: Response, db: DbSession
) -> AuthResponse:
    user, _workspace, project = await auth_service.register_user(
        db,
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        project_name=data.project_name,
    )
    await write_audit(
        db,
        action="user.register",
        user_id=user.id,
        project_id=project.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
    )
    await db.commit()
    await db.refresh(user)

    set_auth_cookies(response, user.id)
    return await _auth_payload(db, user, "Аккаунт создан, добро пожаловать")


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Вход",
    dependencies=[Depends(auth_rate_limit)],
)
async def login(
    data: LoginRequest, request: Request, response: Response, db: DbSession
) -> AuthResponse:
    user = await auth_service.authenticate(db, data.email, data.password)
    await write_audit(
        db, action="user.login", user_id=user.id, entity_type="user",
        entity_id=user.id, request=request,
    )
    await db.commit()
    await db.refresh(user)

    set_auth_cookies(response, user.id)
    return await _auth_payload(db, user, "Вход выполнен")


@router.post("/refresh", response_model=MessageResponse, summary="Обновление сессии")
async def refresh(request: Request, response: Response, db: DbSession) -> MessageResponse:
    token = request.cookies.get(settings.refresh_cookie_name)
    if not token:
        raise AuthError("Сессия не найдена. Войдите заново.")
    try:
        payload = decode_token(token, expected_type="refresh")
        user_id = uuid.UUID(str(payload.get("sub")))
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise AuthError("Сессия истекла. Войдите заново.") from exc

    user = await auth_service.get_user(db, user_id)
    set_auth_cookies(response, user.id)
    return MessageResponse(message="Сессия продлена")


@router.post("/logout", response_model=MessageResponse, summary="Выход")
async def logout(response: Response) -> MessageResponse:
    clear_auth_cookies(response)
    return MessageResponse(message="Вы вышли из сервиса")


@router.get("/me", response_model=AuthResponse, summary="Текущий пользователь")
async def me(user: CurrentUser, db: DbSession) -> AuthResponse:
    return await _auth_payload(db, user, "Данные пользователя получены")


@router.patch("/me", response_model=UserResponse, summary="Изменение профиля")
async def update_me(
    data: UpdateProfileRequest, user: CurrentUser, db: DbSession
) -> UserResponse:
    if data.full_name is not None:
        user.full_name = data.full_name.strip() or None
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/change-password", response_model=MessageResponse, summary="Смена пароля")
async def change_password(
    data: ChangePasswordRequest, user: CurrentUser, request: Request, db: DbSession
) -> MessageResponse:
    await auth_service.change_password(db, user, data.current_password, data.new_password)
    await write_audit(
        db, action="user.change_password", user_id=user.id, entity_type="user",
        entity_id=user.id, request=request,
    )
    await db.commit()
    return MessageResponse(message="Пароль изменён")


@router.delete("/me", response_model=MessageResponse, summary="Удаление аккаунта")
async def delete_me(
    data: DeleteAccountRequest, user: CurrentUser, response: Response, db: DbSession
) -> MessageResponse:
    if not data.confirm:
        raise AuthError(
            "Удаление не подтверждено. Отметьте согласие на удаление всех данных.",
            code="not_confirmed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    await auth_service.delete_account(db, user, data.password)
    await db.commit()
    clear_auth_cookies(response)
    return MessageResponse(message="Аккаунт и все связанные данные удалены")
