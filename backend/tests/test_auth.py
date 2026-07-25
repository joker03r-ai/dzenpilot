"""Тесты регистрации, входа и защиты маршрутов."""

from __future__ import annotations

from httpx import AsyncClient

from app.core.config import settings


async def test_register_creates_user_and_project(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    response = await client.post("/api/v1/auth/register", json=register_payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == register_payload["email"]
    assert data["default_project_id"] is not None
    assert settings.access_cookie_name in response.cookies


async def test_register_rejects_duplicate_email(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await client.post("/api/v1/auth/register", json=register_payload)
    response = await client.post("/api/v1/auth/register", json=register_payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "123", "project_name": "Канал"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_login_and_me(client: AsyncClient, register_payload: dict[str, str]) -> None:
    await client.post("/api/v1/auth/register", json=register_payload)
    client.cookies.clear()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login.status_code == 200, login.text

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == register_payload["email"]


async def test_login_with_wrong_password(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await client.post("/api/v1/auth/register", json=register_payload)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Неверная почта или пароль"


async def test_protected_route_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/projects")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_logout_clears_session(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await client.post("/api/v1/auth/register", json=register_payload)
    await client.post("/api/v1/auth/logout")
    client.cookies.clear()

    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
