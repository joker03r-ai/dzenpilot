"""Тесты проектов, главной страницы и интеграций."""

from __future__ import annotations

from httpx import AsyncClient


async def _register(client: AsyncClient, payload: dict[str, str]) -> str:
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["default_project_id"]


async def test_list_projects_after_register(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await _register(client, register_payload)

    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == register_payload["project_name"]
    assert body["items"][0]["timezone"] == "Europe/Moscow"


async def test_create_and_update_project(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await _register(client, register_payload)

    created = await client.post(
        "/api/v1/projects",
        json={"name": "Канал про здоровье", "niche": "Здоровье", "timezone": "Asia/Irkutsk"},
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    updated = await client.patch(
        f"/api/v1/projects/{project_id}", json={"tone_of_voice": "Дружелюбный"}
    )
    assert updated.status_code == 200
    assert updated.json()["tone_of_voice"] == "Дружелюбный"
    assert updated.json()["timezone"] == "Asia/Irkutsk"


async def test_dashboard_returns_setup_steps(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    project_id = await _register(client, register_payload)

    response = await client.get(f"/api/v1/projects/{project_id}/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["greeting"] == "Ваш центр управления контентом Дзена"
    assert body["counters"]["competitors"] == 0
    assert len(body["steps"]) == 5
    assert body["setup_progress"] == 0


async def test_foreign_project_is_forbidden(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    project_id = await _register(client, register_payload)
    await client.post("/api/v1/auth/logout")
    client.cookies.clear()

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "password": "anotherpass123",
            "project_name": "Чужой канал",
        },
    )

    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


async def test_integration_key_is_never_returned(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    project_id = await _register(client, register_payload)
    secret = "sk-ant-secret-value-1234567890"

    created = await client.post(
        f"/api/v1/projects/{project_id}/integrations",
        json={"kind": "anthropic", "title": "Основное", "api_key": secret},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["has_credentials"] is True
    assert secret not in created.text
    assert body["key_mask"].startswith("sk-ant-")

    listed = await client.get(f"/api/v1/projects/{project_id}/integrations")
    assert listed.status_code == 200
    assert secret not in listed.text
