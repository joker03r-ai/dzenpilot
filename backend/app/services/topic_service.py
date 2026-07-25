"""Подбор и хранение тем.

Источники сигналов только законные: публикации конкурентов, которые пользователь
сам добавил или импортировал, введённые им данные о нише и аудитории,
а также смысловые выводы модели. Сервис не обходит защиту площадок
и не собирает закрытые данные.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIRequest
from app.ai.factory import get_project_provider
from app.ai.prompts import system_prompt
from app.core.errors import ExternalServiceError, NotFoundError
from app.models.ai import AIUsage
from app.models.competitor import Competitor, CompetitorPublication
from app.models.enums import CompetitionLevel, TopicOrigin, TopicStatus
from app.models.project import Project
from app.models.topic import Topic, TopicScore
from app.schemas.common import PaginationParams
from app.schemas.topic import (
    GOAL_LABELS,
    ScoreBreakdown,
    TopicCreate,
    TopicResponse,
    TopicScoreResponse,
    TopicSearchRequest,
    TopicUpdate,
)
from app.services import topic_scoring
from app.services.topic_scoring import ScoreComponents

RESPONSE_SCHEMA = """{
  "topics": [
    {
      "title": "название темы",
      "description": "почему тема перспективна, 2-3 предложения",
      "audience": "кому адресована",
      "format": "предполагаемый формат",
      "competition_level": "low | medium | high",
      "seasonality": "когда тема востребована",
      "recommended_length": 7000,
      "title_variants": ["вариант заголовка"],
      "reader_questions": ["вопрос читателя"],
      "series_ideas": ["идея для продолжения серии"],
      "monetization": ["способ монетизации"],
      "risks": ["риск"],
      "scores": {
        "interest": 0,
        "growth": 0,
        "competition": 0,
        "seasonality": 0,
        "series_potential": 0,
        "commercial": 0,
        "difficulty": 0,
        "decay_risk": 0,
        "audience_fit": 0
      }
    }
  ]
}"""


# --------------------------------------------------------------------------
# Сбор законных сигналов
# --------------------------------------------------------------------------

async def collect_signals(
    db: AsyncSession, project_id: uuid.UUID, period_days: int
) -> dict[str, object]:
    """Готовит выжимку по публикациям конкурентов за период."""
    since = datetime.now(UTC) - timedelta(days=period_days)

    result = await db.execute(
        select(CompetitorPublication, Competitor.name)
        .join(Competitor, Competitor.id == CompetitorPublication.competitor_id)
        .where(
            Competitor.project_id == project_id,
            Competitor.deleted_at.is_(None),
            or_(
                CompetitorPublication.published_at.is_(None),
                CompetitorPublication.published_at >= since,
            ),
        )
    )
    rows = result.all()

    publications = [item for item, _ in rows]
    with_views = [item for item in publications if item.views is not None]
    top = sorted(with_views, key=lambda item: item.views or 0, reverse=True)[:25]

    topics_counter: dict[str, int] = {}
    for item in publications:
        if item.topic_guess:
            topics_counter[item.topic_guess] = topics_counter.get(item.topic_guess, 0) + 1

    return {
        "total_publications": len(publications),
        "with_views": len(with_views),
        "competitors": len({name for _, name in rows}),
        "top_titles": [
            {
                "title": item.title,
                "views": item.views,
                "topic": item.topic_guess,
                "format": item.format,
            }
            for item in top
        ],
        "frequent_topics": sorted(
            topics_counter.items(), key=lambda pair: pair[1], reverse=True
        )[:15],
    }


def build_prompt(
    request: TopicSearchRequest, project: Project, signals: dict[str, object]
) -> str:
    lines = [
        f"Ниша: {request.niche}",
        f"Целевая аудитория: {request.audience or project.target_audience or 'не указана'}",
        f"Регион: {request.region or 'не указан'}",
        f"Желаемый формат: {request.format or 'любой'}",
        f"Цель автора: {GOAL_LABELS.get(request.goal, request.goal)}",
        f"Желаемый уровень конкуренции: {request.competition_level or 'любой'}",
        f"Период анализа: {request.period_days} дней",
    ]

    if request.forbidden_topics:
        lines.append("Запрещённые темы (не предлагать): " + ", ".join(request.forbidden_topics))

    lines += [
        "",
        "Данные по конкурентам из базы пользователя:",
        f"- конкурентов: {signals['competitors']}",
        f"- публикаций за период: {signals['total_publications']}",
        f"- из них с известными просмотрами: {signals['with_views']}",
    ]

    frequent = signals.get("frequent_topics") or []
    if frequent:
        lines.append("- частые темы: " + ", ".join(f"{name} ({count})" for name, count in frequent))
    else:
        lines.append("- частые темы: данные недоступны")

    top_titles = signals.get("top_titles") or []
    if top_titles:
        lines.append("")
        lines.append("Самые просматриваемые публикации конкурентов:")
        for item in top_titles:
            views = item["views"] if item["views"] is not None else "просмотры неизвестны"
            lines.append(f"- {item['title']} | {views}")
    else:
        lines.append("")
        lines.append(
            "Публикаций конкурентов в базе нет — опирайся только на нишу и аудиторию, "
            "и учти это при оценке."
        )

    lines += [
        "",
        f"Предложи {request.count} тем для статей в Яндекс Дзене.",
        "Верни ответ строго в виде JSON по схеме:",
        RESPONSE_SCHEMA,
        "",
        "Правила оценок в поле scores:",
        "- каждое значение от 0 до 100;",
        "- competition: насколько ниша свободна, 100 значит почти нет конкурентов;",
        "- difficulty: насколько сложно подготовить статью, 100 значит очень сложно;",
        "- decay_risk: насколько быстро тема устареет, 100 значит устареет очень быстро;",
        "- остальные поля: чем больше, тем лучше.",
        "",
        "Не предлагай темы, требующие выдуманных фактов или обещаний дохода.",
        "Не повторяй заголовки конкурентов дословно.",
        "Отвечай на русском языке. Верни только JSON.",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Разбор ответа модели
# --------------------------------------------------------------------------

def parse_response(text: str) -> list[dict]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.+?)\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ExternalServiceError(
                "Модель вернула ответ в неожиданном формате. Попробуйте запустить поиск ещё раз."
            ) from None
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ExternalServiceError(
                "Не удалось разобрать ответ модели. Попробуйте запустить поиск ещё раз."
            ) from exc

    topics = payload.get("topics") if isinstance(payload, dict) else payload
    if not isinstance(topics, list) or not topics:
        raise ExternalServiceError("Модель не предложила ни одной темы. Уточните нишу и повторите.")
    return [item for item in topics if isinstance(item, dict)]


def _as_list(value: object, limit: int = 20) -> list:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()][:limit]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _as_int(value: object, default: int = 50) -> int:
    try:
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _competition_level(value: object) -> CompetitionLevel | None:
    mapping = {
        "low": CompetitionLevel.LOW,
        "medium": CompetitionLevel.MEDIUM,
        "high": CompetitionLevel.HIGH,
        "низкая": CompetitionLevel.LOW,
        "средняя": CompetitionLevel.MEDIUM,
        "высокая": CompetitionLevel.HIGH,
    }
    if isinstance(value, str):
        return mapping.get(value.strip().lower())
    return None


# --------------------------------------------------------------------------
# Подбор тем
# --------------------------------------------------------------------------

async def _match_competitor_publications(
    db: AsyncSession, project_id: uuid.UUID, title: str
) -> tuple[int, int, int | None]:
    """Ищет публикации конкурентов, похожие на тему, по значимым словам заголовка."""
    words = [
        word
        for word in re.findall(r"[а-яёa-z]{5,}", title.lower())
        if word not in {"который", "которая", "которые", "почему", "нужно"}
    ][:4]
    if not words:
        return 0, 0, None

    conditions = [CompetitorPublication.title.ilike(f"%{word}%") for word in words]
    result = await db.execute(
        select(CompetitorPublication)
        .join(Competitor, Competitor.id == CompetitorPublication.competitor_id)
        .where(
            Competitor.project_id == project_id,
            Competitor.deleted_at.is_(None),
            or_(*conditions),
        )
    )
    publications = list(result.scalars().all())
    views = [item.views for item in publications if item.views is not None]
    average = round(sum(views) / len(views)) if views else None
    return len(publications), len(views), average


async def search_topics(
    db: AsyncSession,
    project: Project,
    request: TopicSearchRequest,
    user_id: uuid.UUID,
) -> tuple[list[Topic], str]:
    """Подбирает темы и сразу считает их оценку."""
    signals = await collect_signals(db, project.id, request.period_days)
    provider = await get_project_provider(db, project.id)
    prompt = build_prompt(request, project, signals)

    response = await provider.complete(
        AIRequest(
            prompt=prompt,
            system=system_prompt("topic_search"),
            max_tokens=8000,
            temperature=0.7,
            json_mode=True,
        )
    )
    raw_topics = parse_response(response.text)

    forbidden = {item.strip().lower() for item in request.forbidden_topics if item.strip()}
    created: list[Topic] = []

    for item in raw_topics:
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        if any(word in title.lower() for word in forbidden):
            continue

        topic = Topic(
            project_id=project.id,
            title=title[:500],
            description=str(item.get("description", "") or "").strip()[:4000] or None,
            niche=request.niche[:255],
            audience=str(item.get("audience", "") or request.audience or "")[:500] or None,
            region=request.region,
            format=str(item.get("format", "") or request.format or "")[:120] or None,
            competition_level=_competition_level(item.get("competition_level")),
            seasonality=str(item.get("seasonality", "") or "")[:255] or None,
            recommended_length=_as_int(item.get("recommended_length"), 7000),
            title_variants=_as_list(item.get("title_variants"), 10),
            reader_questions=_as_list(item.get("reader_questions"), 10),
            series_ideas=_as_list(item.get("series_ideas"), 10),
            monetization=_as_list(item.get("monetization"), 10),
            risks=_as_list(item.get("risks"), 10),
            sources=[
                "Публикации конкурентов из вашего проекта",
                "Параметры ниши и аудитории, указанные вами",
                f"Смысловая оценка модели {response.model}",
            ],
            status=TopicStatus.SUGGESTED,
            origin=TopicOrigin.AI_SEARCH,
            created_by=user_id,
        )
        db.add(topic)
        await db.flush()

        # Успешность у конкурентов считаем по реальным данным, а не по мнению модели
        matched, with_views, average_views = await _match_competitor_publications(
            db, project.id, title
        )
        competitor_score, competitor_note = topic_scoring.competitor_success_signal(
            matched, with_views, average_views
        )

        raw_scores = item.get("scores") if isinstance(item.get("scores"), dict) else {}
        components = ScoreComponents(
            interest=_as_int(raw_scores.get("interest")),
            growth=_as_int(raw_scores.get("growth")),
            competition=(
                topic_scoring.competition_signal(topic.competition_level)
                if topic.competition_level
                else _as_int(raw_scores.get("competition"))
            ),
            seasonality=_as_int(raw_scores.get("seasonality")),
            competitor_success=competitor_score,
            series_potential=_as_int(raw_scores.get("series_potential")),
            commercial=_as_int(raw_scores.get("commercial")),
            difficulty=_as_int(raw_scores.get("difficulty")),
            decay_risk=_as_int(raw_scores.get("decay_risk")),
            audience_fit=_as_int(raw_scores.get("audience_fit")),
        )
        score = topic_scoring.calculate(
            components, context=competitor_note.capitalize() + "."
        )

        db.add(
            TopicScore(
                topic_id=topic.id,
                total_score=score.total,
                interest_score=score.components["interest"],
                growth_score=score.components["growth"],
                competition_score=score.components["competition"],
                seasonality_score=score.components["seasonality"],
                competitor_success_score=score.components["competitor_success"],
                series_potential_score=score.components["series_potential"],
                commercial_score=score.components["commercial"],
                difficulty_score=score.components["difficulty"],
                decay_risk_score=score.components["decay_risk"],
                audience_fit_score=score.components["audience_fit"],
                explanation=score.explanation,
                formula_version=score.formula_version,
            )
        )
        created.append(topic)

    db.add(
        AIUsage(
            project_id=project.id,
            provider=response.provider,
            model=response.model,
            operation="topic_search",
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=response.cost_usd,
            entity_type="project",
            entity_id=project.id,
        )
    )
    await db.flush()

    note = (
        "Выводы основаны на публикациях конкурентов из вашего проекта и указанных "
        "вами параметрах ниши."
        if signals["total_publications"]
        else "Публикаций конкурентов в проекте нет, поэтому оценки опираются только "
        "на нишу и аудиторию. Добавьте конкурентов — точность заметно вырастет."
    )
    return created, note


# --------------------------------------------------------------------------
# Хранение и выдача
# --------------------------------------------------------------------------

async def latest_score(db: AsyncSession, topic_id: uuid.UUID) -> TopicScore | None:
    result = await db.execute(
        select(TopicScore)
        .where(TopicScore.topic_id == topic_id)
        .order_by(TopicScore.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


async def to_response(db: AsyncSession, topic: Topic) -> TopicResponse:
    payload = TopicResponse.model_validate(topic)
    score = await latest_score(db, topic.id)
    if score is not None:
        payload.score = TopicScoreResponse(
            total_score=score.total_score,
            verdict=topic_scoring.describe(score.total_score),
            explanation=score.explanation or "",
            breakdown=ScoreBreakdown(
                interest=score.interest_score or 0,
                growth=score.growth_score or 0,
                competition=score.competition_score or 0,
                seasonality=score.seasonality_score or 0,
                competitor_success=score.competitor_success_score or 0,
                series_potential=score.series_potential_score or 0,
                commercial=score.commercial_score or 0,
                difficulty=score.difficulty_score or 0,
                decay_risk=score.decay_risk_score or 0,
                audience_fit=score.audience_fit_score or 0,
            ),
            formula_version=score.formula_version,
            created_at=score.created_at,
        )
    return payload


async def list_topics(
    db: AsyncSession,
    project_id: uuid.UUID,
    params: PaginationParams,
    status: TopicStatus | None = None,
    min_score: int | None = None,
) -> tuple[list[Topic], int]:
    base = select(Topic).where(Topic.project_id == project_id, Topic.deleted_at.is_(None))

    if status:
        base = base.where(Topic.status == status)
    else:
        base = base.where(Topic.status != TopicStatus.HIDDEN)
    if params.search:
        base = base.where(Topic.title.ilike(f"%{params.search}%"))

    if min_score is not None:
        newest = (
            select(TopicScore.topic_id, func.max(TopicScore.created_at).label("last"))
            .group_by(TopicScore.topic_id)
            .subquery()
        )
        base = base.join(newest, newest.c.topic_id == Topic.id).join(
            TopicScore,
            (TopicScore.topic_id == Topic.id) & (TopicScore.created_at == newest.c.last),
        ).where(TopicScore.total_score >= min_score)

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0
    result = await db.execute(
        base.order_by(Topic.created_at.desc()).offset(params.offset).limit(params.size)
    )
    return list(result.scalars().all()), int(total)


async def get_topic(db: AsyncSession, project_id: uuid.UUID, topic_id: uuid.UUID) -> Topic:
    topic = await db.get(Topic, topic_id)
    if topic is None or topic.project_id != project_id or topic.deleted_at:
        raise NotFoundError("Тема не найдена")
    return topic


async def create_topic(
    db: AsyncSession, project_id: uuid.UUID, data: TopicCreate, user_id: uuid.UUID
) -> Topic:
    topic = Topic(
        project_id=project_id,
        **data.model_dump(),
        status=TopicStatus.SAVED,
        origin=TopicOrigin.MANUAL,
        created_by=user_id,
    )
    db.add(topic)
    await db.flush()
    return topic


async def update_topic(db: AsyncSession, topic: Topic, data: TopicUpdate) -> Topic:
    for field_name, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, field_name, value)
    await db.flush()
    return topic


async def delete_topic(db: AsyncSession, topic: Topic) -> None:
    topic.deleted_at = datetime.now(UTC)
    await db.flush()
