"""Проекты, участники и данные главной страницы."""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    Pagination,
    ProjectEditor,
    ProjectOwner,
    ProjectViewer,
)
from app.core.idempotency import get_cached_response, store_response
from app.models.enums import RU_LABELS, UserRole
from app.schemas.common import MessageResponse, Page
from app.schemas.dashboard import DashboardResponse
from app.schemas.project import (
    MemberInvite,
    MemberResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services import dashboard_service, project_service
from app.services.audit_service import write_audit
from app.services.timezones import TIMEZONE_CHOICES

router = APIRouter()


@router.get("", response_model=Page[ProjectResponse], summary="Список проектов")
async def list_projects(
    user: CurrentUser, db: DbSession, params: Pagination
) -> Page[ProjectResponse]:
    projects, total = await project_service.list_projects(db, user.id, params)
    return Page.build(
        [ProjectResponse.model_validate(item) for item in projects], total, params
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание проекта",
)
async def create_project(
    data: ProjectCreate, user: CurrentUser, db: DbSession, request: Request
) -> ProjectResponse:
    cached = await get_cached_response(request)
    if cached is not None:
        return ProjectResponse.model_validate(cached)

    project = await project_service.create_project(db, user, data)
    await write_audit(
        db,
        action="project.create",
        user_id=user.id,
        project_id=project.id,
        entity_type="project",
        entity_id=project.id,
        request=request,
    )
    await db.commit()
    await db.refresh(project)

    payload = ProjectResponse.model_validate(project)
    await store_response(request, payload.model_dump(mode="json"))
    return payload


@router.get("/{project_id}", response_model=ProjectResponse, summary="Карточка проекта")
async def get_project(project: ProjectViewer) -> ProjectResponse:
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse, summary="Изменение проекта")
async def update_project(
    data: ProjectUpdate,
    project: ProjectEditor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> ProjectResponse:
    await project_service.update_project(db, project, data)
    await write_audit(
        db,
        action="project.update",
        user_id=user.id,
        project_id=project.id,
        entity_type="project",
        entity_id=project.id,
        request=request,
        payload=data.model_dump(exclude_unset=True, mode="json"),
    )
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", response_model=MessageResponse, summary="Архивация проекта")
async def archive_project(
    project: ProjectOwner, user: CurrentUser, db: DbSession, request: Request
) -> MessageResponse:
    await project_service.archive_project(db, project)
    await write_audit(
        db,
        action="project.archive",
        user_id=user.id,
        project_id=project.id,
        entity_type="project",
        entity_id=project.id,
        request=request,
    )
    await db.commit()
    return MessageResponse(message="Проект перенесён в архив")


@router.get(
    "/{project_id}/dashboard",
    response_model=DashboardResponse,
    summary="Данные главной страницы",
)
async def project_dashboard(
    project: ProjectViewer, user: CurrentUser, db: DbSession
) -> DashboardResponse:
    return await dashboard_service.build_dashboard(db, project, user)


@router.get(
    "/{project_id}/members", response_model=list[MemberResponse], summary="Участники проекта"
)
async def list_members(project: ProjectViewer, db: DbSession) -> list[MemberResponse]:
    rows = await project_service.list_members(db, project.workspace_id)
    return [
        MemberResponse(
            id=member.id,
            user_id=member.user_id,
            email=member_user.email,
            full_name=member_user.full_name,
            role=member.role,
            accepted_at=member.accepted_at,
        )
        for member, member_user in rows
    ]


@router.post(
    "/{project_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Приглашение участника",
)
async def invite_member(
    data: MemberInvite,
    project: ProjectOwner,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> MemberResponse:
    member, invited = await project_service.invite_member(
        db, project.workspace_id, data.email, data.role
    )
    await write_audit(
        db,
        action="workspace.invite_member",
        user_id=user.id,
        project_id=project.id,
        entity_type="workspace_member",
        entity_id=member.id,
        request=request,
        payload={"email": data.email, "role": data.role.value},
    )
    await db.commit()
    return MemberResponse(
        id=member.id,
        user_id=invited.id,
        email=invited.email,
        full_name=invited.full_name,
        role=member.role,
        accepted_at=member.accepted_at,
    )


@router.get(
    "/{project_id}/roles",
    response_model=dict[str, str],
    summary="Названия ролей для интерфейса",
)
async def roles(_: ProjectViewer) -> dict[str, str]:
    return {role.value: RU_LABELS["user_role"][role] for role in UserRole}


@router.get(
    "/{project_id}/timezones",
    response_model=list[dict[str, str]],
    summary="Часовые пояса для календаря",
)
async def timezones(_: ProjectViewer) -> list[dict[str, str]]:
    return TIMEZONE_CHOICES
