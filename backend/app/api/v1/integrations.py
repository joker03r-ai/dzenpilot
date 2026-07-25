"""Подключения внешних сервисов проекта."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request, status

from app.api.deps import CurrentUser, DbSession, ProjectEditor, ProjectViewer
from app.models.enums import RU_LABELS, IntegrationKind
from app.schemas.common import MessageResponse
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationResponse,
    IntegrationTestResult,
    IntegrationUpdate,
)
from app.services import integration_service
from app.services.audit_service import write_audit

router = APIRouter()


@router.get(
    "/{project_id}/integrations",
    response_model=list[IntegrationResponse],
    summary="Список подключений",
)
async def list_integrations(project: ProjectViewer, db: DbSession) -> list[IntegrationResponse]:
    items = await integration_service.list_integrations(db, project.id)
    return [integration_service.to_response(item) for item in items]


@router.get(
    "/{project_id}/integrations/catalog",
    response_model=list[dict[str, str]],
    summary="Какие сервисы можно подключить",
)
async def catalog(_: ProjectViewer) -> list[dict[str, str]]:
    return [
        {"kind": kind.value, "title": RU_LABELS["integration_kind"][kind]}
        for kind in IntegrationKind
    ]


@router.post(
    "/{project_id}/integrations",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Подключить сервис",
)
async def create_integration(
    data: IntegrationCreate,
    project: ProjectEditor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> IntegrationResponse:
    integration = await integration_service.create_integration(db, project.id, data)
    await write_audit(
        db,
        action="integration.create",
        user_id=user.id,
        project_id=project.id,
        entity_type="integration",
        entity_id=integration.id,
        request=request,
        payload={"kind": data.kind.value},  # сам ключ в журнал не попадает
    )
    await db.commit()
    await db.refresh(integration)
    return integration_service.to_response(integration)


@router.patch(
    "/{project_id}/integrations/{integration_id}",
    response_model=IntegrationResponse,
    summary="Изменить подключение",
)
async def update_integration(
    integration_id: uuid.UUID,
    data: IntegrationUpdate,
    project: ProjectEditor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> IntegrationResponse:
    integration = await integration_service.get_integration(db, project.id, integration_id)
    await integration_service.update_integration(db, integration, data)
    await write_audit(
        db,
        action="integration.update",
        user_id=user.id,
        project_id=project.id,
        entity_type="integration",
        entity_id=integration.id,
        request=request,
    )
    await db.commit()
    await db.refresh(integration)
    return integration_service.to_response(integration)


@router.delete(
    "/{project_id}/integrations/{integration_id}",
    response_model=MessageResponse,
    summary="Отключить сервис",
)
async def delete_integration(
    integration_id: uuid.UUID,
    project: ProjectEditor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> MessageResponse:
    integration = await integration_service.get_integration(db, project.id, integration_id)
    await integration_service.delete_integration(db, integration)
    await write_audit(
        db,
        action="integration.delete",
        user_id=user.id,
        project_id=project.id,
        entity_type="integration",
        entity_id=integration_id,
        request=request,
    )
    await db.commit()
    return MessageResponse(message="Подключение удалено")


@router.post(
    "/{project_id}/integrations/{integration_id}/test",
    response_model=IntegrationTestResult,
    summary="Проверить подключение",
)
async def test_integration(
    integration_id: uuid.UUID, project: ProjectEditor, db: DbSession
) -> IntegrationTestResult:
    integration = await integration_service.get_integration(db, project.id, integration_id)
    result = await integration_service.test_integration(db, integration)
    await db.commit()
    return result
