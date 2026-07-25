"""Проекты и права доступа к ним."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.ai import AIProviderSettings
from app.models.enums import AIProviderName, ProjectStatus, UserRole
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.common import PaginationParams
from app.schemas.project import ProjectCreate, ProjectUpdate

# Кто что может делать. Наблюдатель только смотрит, автор работает со статьями,
# редактор управляет содержимым проекта, владелец — всем.
ROLE_WEIGHT: dict[UserRole, int] = {
    UserRole.VIEWER: 1,
    UserRole.AUTHOR: 2,
    UserRole.EDITOR: 3,
    UserRole.OWNER: 4,
}


async def get_membership(
    db: AsyncSession, user_id: uuid.UUID, workspace_id: uuid.UUID
) -> WorkspaceMember | None:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id,
        )
    )
    return result.scalars().first()


async def get_project_for_user(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    min_role: UserRole = UserRole.VIEWER,
) -> Project:
    """Возвращает проект и проверяет, что у пользователя достаточно прав."""
    project = await db.get(Project, project_id)
    if project is None or project.deleted_at is not None:
        raise NotFoundError("Проект не найден")

    membership = await get_membership(db, user_id, project.workspace_id)
    if membership is None:
        raise ForbiddenError("У вас нет доступа к этому проекту")
    if ROLE_WEIGHT[membership.role] < ROLE_WEIGHT[min_role]:
        raise ForbiddenError("Недостаточно прав для этого действия")
    return project


async def list_projects(
    db: AsyncSession, user_id: uuid.UUID, params: PaginationParams
) -> tuple[list[Project], int]:
    base = (
        select(Project)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Project.workspace_id)
        .where(WorkspaceMember.user_id == user_id, Project.deleted_at.is_(None))
    )
    if params.search:
        base = base.where(Project.name.ilike(f"%{params.search}%"))

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0

    order = Project.created_at.desc()
    if params.sort:
        field_name = params.sort.lstrip("-")
        column = getattr(Project, field_name, None)
        if column is not None:
            order = column.desc() if params.sort.startswith("-") else column.asc()

    result = await db.execute(base.order_by(order).offset(params.offset).limit(params.size))
    return list(result.scalars().all()), int(total)


async def _resolve_workspace(
    db: AsyncSession, user: User, workspace_id: uuid.UUID | None
) -> Workspace:
    if workspace_id is not None:
        membership = await get_membership(db, user.id, workspace_id)
        if membership is None or ROLE_WEIGHT[membership.role] < ROLE_WEIGHT[UserRole.EDITOR]:
            raise ForbiddenError("Нет прав создавать проекты в этом пространстве")
        workspace = await db.get(Workspace, workspace_id)
        if workspace is None:
            raise NotFoundError("Рабочее пространство не найдено")
        return workspace

    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.created_at)
        .limit(1)
    )
    workspace = result.scalars().first()
    if workspace is None:
        workspace = Workspace(name="Моё пространство", owner_id=user.id)
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
        await db.flush()
    return workspace


async def create_project(db: AsyncSession, user: User, data: ProjectCreate) -> Project:
    workspace = await _resolve_workspace(db, user, data.workspace_id)

    exists = await db.scalar(
        select(func.count())
        .select_from(Project)
        .where(
            Project.workspace_id == workspace.id,
            Project.name == data.name.strip(),
            Project.deleted_at.is_(None),
        )
    )
    if exists:
        raise ConflictError("Проект с таким названием уже есть")

    project = Project(
        workspace_id=workspace.id,
        name=data.name.strip(),
        description=data.description,
        niche=data.niche,
        target_audience=data.target_audience,
        tone_of_voice=data.tone_of_voice,
        region=data.region,
        timezone=data.timezone,
        dzen_channel_url=data.dzen_channel_url,
        settings={},
    )
    db.add(project)
    await db.flush()

    db.add(
        AIProviderSettings(
            project_id=project.id,
            provider=AIProviderName.ANTHROPIC,
            model="claude-sonnet-5",
            is_default=True,
        )
    )
    await db.flush()
    return project


async def update_project(db: AsyncSession, project: Project, data: ProjectUpdate) -> Project:
    for field_name, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field_name, value)
    await db.flush()
    return project


async def archive_project(db: AsyncSession, project: Project) -> None:
    project.status = ProjectStatus.ARCHIVED
    project.deleted_at = datetime.now(UTC)
    await db.flush()


async def list_members(db: AsyncSession, workspace_id: uuid.UUID) -> list[tuple[WorkspaceMember, User]]:
    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.created_at)
    )
    return [(member, user) for member, user in result.all()]


async def invite_member(
    db: AsyncSession, workspace_id: uuid.UUID, email: str, role: UserRole
) -> tuple[WorkspaceMember, User]:
    result = await db.execute(select(User).where(User.email == email.strip().lower()))
    user = result.scalars().first()
    if user is None:
        raise NotFoundError(
            "Пользователь с такой почтой ещё не зарегистрирован. "
            "Попросите его создать аккаунт, затем пригласите снова."
        )
    if await get_membership(db, user.id, workspace_id) is not None:
        raise ConflictError("Этот пользователь уже участник пространства")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=role,
        invited_at=datetime.now(UTC),
        accepted_at=datetime.now(UTC),
    )
    db.add(member)
    await db.flush()
    return member, user
