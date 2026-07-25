"""Конкуренты: список, карточка, публикации, импорт, ИИ-анализ, сравнение."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status

from app.api.deps import CurrentUser, DbSession, Pagination, ProjectAuthor, ProjectViewer
from app.core.errors import NotFoundError, ValidationAppError
from app.core.idempotency import get_cached_response, store_response
from app.core.rate_limit import ai_rate_limit
from app.models.competitor import CompetitorPublication
from app.models.enums import CompetitorStatus
from app.schemas.common import MessageResponse, Page, PaginationParams
from app.schemas.competitor import (
    AnalysisResponse,
    CompareRequest,
    CompareResponse,
    CompetitorCreate,
    CompetitorResponse,
    CompetitorUpdate,
    CsvImportResult,
    PublicationCreate,
    PublicationResponse,
    PublicationUpdate,
)
from app.services import competitor_analysis_service as analysis_service
from app.services import competitor_service
from app.services.audit_service import write_audit

router = APIRouter()

MAX_CSV_SIZE = 5 * 1024 * 1024  # 5 МБ


async def _to_response(db, competitor) -> CompetitorResponse:
    """Дополняет карточку числом публикаций и признаком наличия отчёта."""
    payload = CompetitorResponse.model_validate(competitor)
    payload.stored_publications = await competitor_service.count_publications(db, competitor.id)
    payload.has_analysis = await competitor_service.has_analysis(db, competitor.id)
    return payload


# --------------------------------------------------------------------------
# Конкуренты
# --------------------------------------------------------------------------

@router.get(
    "/{project_id}/competitors",
    response_model=Page[CompetitorResponse],
    summary="Список конкурентов",
)
async def list_competitors(
    project: ProjectViewer,
    db: DbSession,
    params: Pagination,
    group: str | None = Query(default=None, description="Фильтр по группе"),
    competitor_status: CompetitorStatus | None = Query(default=None, alias="status"),
) -> Page[CompetitorResponse]:
    items, total = await competitor_service.list_competitors(
        db, project.id, params, group=group, status=competitor_status
    )
    return Page.build([await _to_response(db, item) for item in items], total, params)


@router.get(
    "/{project_id}/competitors/groups",
    response_model=list[str],
    summary="Группы конкурентов",
)
async def list_groups(project: ProjectViewer, db: DbSession) -> list[str]:
    items, _ = await competitor_service.list_competitors(
        db, project.id, PaginationParams(page=1, size=100)
    )
    return sorted({item.group_name for item in items if item.group_name})


@router.post(
    "/{project_id}/competitors",
    response_model=CompetitorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить конкурента",
)
async def create_competitor(
    data: CompetitorCreate,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> CompetitorResponse:
    cached = await get_cached_response(request)
    if cached is not None:
        return CompetitorResponse.model_validate(cached)

    competitor = await competitor_service.create_competitor(db, project.id, data, user.id)
    await write_audit(
        db,
        action="competitor.create",
        user_id=user.id,
        project_id=project.id,
        entity_type="competitor",
        entity_id=competitor.id,
        request=request,
        payload={"name": competitor.name},
    )
    await db.commit()
    await db.refresh(competitor)

    payload = await _to_response(db, competitor)
    await store_response(request, payload.model_dump(mode="json"))
    return payload


@router.get(
    "/{project_id}/competitors/{competitor_id}",
    response_model=CompetitorResponse,
    summary="Карточка конкурента",
)
async def get_competitor(
    competitor_id: uuid.UUID, project: ProjectViewer, db: DbSession
) -> CompetitorResponse:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    return await _to_response(db, competitor)


@router.patch(
    "/{project_id}/competitors/{competitor_id}",
    response_model=CompetitorResponse,
    summary="Изменить конкурента",
)
async def update_competitor(
    competitor_id: uuid.UUID,
    data: CompetitorUpdate,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> CompetitorResponse:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    await competitor_service.update_competitor(db, competitor, data)
    await write_audit(
        db,
        action="competitor.update",
        user_id=user.id,
        project_id=project.id,
        entity_type="competitor",
        entity_id=competitor.id,
        request=request,
    )
    await db.commit()
    await db.refresh(competitor)
    return await _to_response(db, competitor)


@router.delete(
    "/{project_id}/competitors/{competitor_id}",
    response_model=MessageResponse,
    summary="Удалить конкурента",
)
async def delete_competitor(
    competitor_id: uuid.UUID,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> MessageResponse:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    await competitor_service.delete_competitor(db, competitor)
    await write_audit(
        db,
        action="competitor.delete",
        user_id=user.id,
        project_id=project.id,
        entity_type="competitor",
        entity_id=competitor_id,
        request=request,
    )
    await db.commit()
    return MessageResponse(message="Конкурент удалён")


# --------------------------------------------------------------------------
# Публикации конкурента
# --------------------------------------------------------------------------

@router.get(
    "/{project_id}/competitors/{competitor_id}/publications",
    response_model=Page[PublicationResponse],
    summary="Публикации конкурента",
)
async def list_publications(
    competitor_id: uuid.UUID, project: ProjectViewer, db: DbSession, params: Pagination
) -> Page[PublicationResponse]:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    items, total = await competitor_service.list_publications(db, competitor.id, params)
    return Page.build(
        [PublicationResponse.model_validate(item) for item in items], total, params
    )


@router.post(
    "/{project_id}/competitors/{competitor_id}/publications",
    response_model=PublicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить публикацию вручную",
)
async def add_publication(
    competitor_id: uuid.UUID,
    data: PublicationCreate,
    project: ProjectAuthor,
    db: DbSession,
) -> PublicationResponse:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    publication = await competitor_service.add_publication(db, competitor, data)
    await competitor_service.recalculate_metrics(db, competitor)
    await db.commit()
    await db.refresh(publication)
    return PublicationResponse.model_validate(publication)


@router.patch(
    "/{project_id}/competitors/{competitor_id}/publications/{publication_id}",
    response_model=PublicationResponse,
    summary="Изменить публикацию",
)
async def update_publication(
    competitor_id: uuid.UUID,
    publication_id: uuid.UUID,
    data: PublicationUpdate,
    project: ProjectAuthor,
    db: DbSession,
) -> PublicationResponse:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    publication = await db.get(CompetitorPublication, publication_id)
    if publication is None or publication.competitor_id != competitor.id:
        raise NotFoundError("Публикация не найдена")

    await competitor_service.update_publication(db, publication, data)
    await competitor_service.recalculate_metrics(db, competitor)
    await db.commit()
    await db.refresh(publication)
    return PublicationResponse.model_validate(publication)


@router.delete(
    "/{project_id}/competitors/{competitor_id}/publications/{publication_id}",
    response_model=MessageResponse,
    summary="Удалить публикацию",
)
async def delete_publication(
    competitor_id: uuid.UUID,
    publication_id: uuid.UUID,
    project: ProjectAuthor,
    db: DbSession,
) -> MessageResponse:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    publication = await db.get(CompetitorPublication, publication_id)
    if publication is None or publication.competitor_id != competitor.id:
        raise NotFoundError("Публикация не найдена")

    await competitor_service.delete_publication(db, publication)
    await competitor_service.recalculate_metrics(db, competitor)
    await db.commit()
    return MessageResponse(message="Публикация удалена")


@router.post(
    "/{project_id}/competitors/{competitor_id}/publications/import-csv",
    response_model=CsvImportResult,
    summary="Импорт публикаций из CSV",
)
async def import_csv(
    competitor_id: uuid.UUID,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
    file: UploadFile = File(..., description="CSV с колонкой «Заголовок»"),
) -> CsvImportResult:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)

    content = await file.read()
    if len(content) > MAX_CSV_SIZE:
        raise ValidationAppError("Файл больше 5 МБ. Разделите его на части.")
    if not content:
        raise ValidationAppError("Файл пустой")

    result = await competitor_service.import_publications_csv(db, competitor, content)
    await write_audit(
        db,
        action="competitor.import_csv",
        user_id=user.id,
        project_id=project.id,
        entity_type="competitor",
        entity_id=competitor.id,
        request=request,
        payload={"created": result.created, "skipped": result.skipped},
    )
    await db.commit()
    return result


# --------------------------------------------------------------------------
# ИИ-анализ и сравнение
# --------------------------------------------------------------------------

@router.post(
    "/{project_id}/competitors/{competitor_id}/analyze",
    response_model=AnalysisResponse,
    summary="Получить отчёт ИИ",
    dependencies=[Depends(ai_rate_limit)],
)
async def analyze(
    competitor_id: uuid.UUID,
    project: ProjectAuthor,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> AnalysisResponse:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    analysis = await analysis_service.analyze_competitor(db, competitor, project.id)
    await write_audit(
        db,
        action="competitor.analyze",
        user_id=user.id,
        project_id=project.id,
        entity_type="competitor",
        entity_id=competitor.id,
        request=request,
        payload={"model": analysis.ai_model},
    )
    await db.commit()
    await db.refresh(analysis)
    return AnalysisResponse.model_validate(analysis)


@router.get(
    "/{project_id}/competitors/{competitor_id}/analyses",
    response_model=list[AnalysisResponse],
    summary="История отчётов",
)
async def list_analyses(
    competitor_id: uuid.UUID, project: ProjectViewer, db: DbSession
) -> list[AnalysisResponse]:
    competitor = await competitor_service.get_competitor(db, project.id, competitor_id)
    items = await analysis_service.list_analyses(db, competitor.id)
    return [AnalysisResponse.model_validate(item) for item in items]


@router.post(
    "/{project_id}/competitors/compare",
    response_model=CompareResponse,
    summary="Сравнить от 2 до 10 конкурентов",
)
async def compare(
    data: CompareRequest, project: ProjectViewer, db: DbSession
) -> CompareResponse:
    return await competitor_service.compare_competitors(db, project.id, data)
