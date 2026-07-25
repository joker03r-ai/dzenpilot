"""ИИ-отчёт по конкуренту.

Модель получает только те данные, которые есть в базе. Если показателей нет,
в промт прямо пишется «данные недоступны», чтобы модель не додумывала цифры.
Ответ приходит в формате JSON и раскладывается по полям отчёта.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIRequest
from app.ai.factory import get_project_provider
from app.ai.prompts import system_prompt
from app.core.errors import ExternalServiceError, ValidationAppError
from app.models.ai import AIUsage
from app.models.competitor import Competitor, CompetitorAnalysis, CompetitorPublication
from app.models.enums import CompetitorStatus

MIN_PUBLICATIONS = 3

RESPONSE_SCHEMA = """{
  "summary": "краткий вывод в 2-3 предложениях",
  "why_it_works": "почему канал набирает просмотры",
  "publish_rhythm": "как часто выходит контент",
  "working_topics": ["тема — почему работает"],
  "working_titles": ["приём в заголовках — пример"],
  "failed_posts": ["публикация — вероятная причина слабого результата"],
  "formats": ["используемый формат"],
  "strengths": ["сильная сторона"],
  "weaknesses": ["слабая сторона"],
  "content_gaps": ["тема, которую конкурент не раскрыл"],
  "differentiation": ["как отстроиться от этого канала"],
  "adaptable_ideas": ["идея, которую можно адаптировать, не копируя текст"]
}"""


def _describe(value: object, suffix: str = "") -> str:
    if value is None:
        return "данные недоступны"
    return f"{value}{suffix}"


def build_prompt(competitor: Competitor, publications: list[CompetitorPublication]) -> str:
    lines = [
        f"Канал: {competitor.name}",
        f"Тематика: {_describe(competitor.niche)}",
        f"Описание: {_describe(competitor.description)}",
        f"Подписчики: {_describe(competitor.subscribers_count)}",
        f"Всего сохранено публикаций: {len(publications)}",
        f"Средние просмотры: {_describe(competitor.avg_views)}",
        f"Максимум просмотров: {_describe(competitor.max_views)}",
        f"Минимум просмотров: {_describe(competitor.min_views)}",
        f"Средняя вовлечённость: {_describe(competitor.avg_engagement_rate, '%')}",
        f"Средняя длина статьи: {_describe(competitor.avg_article_length, ' знаков')}",
        f"Интервал между публикациями: {_describe(competitor.avg_publish_interval_days, ' дн.')}",
        "",
        "Публикации (заголовок | дата | просмотры | реакции | комментарии | формат):",
    ]

    ordered = sorted(
        publications,
        key=lambda item: (item.views if item.views is not None else -1),
        reverse=True,
    )
    for item in ordered[:40]:
        date = item.published_at.strftime("%d.%m.%Y") if item.published_at else "дата неизвестна"
        lines.append(
            f"- {item.title} | {date} | {_describe(item.views)} | "
            f"{_describe(item.reactions)} | {_describe(item.comments_count)} | "
            f"{_describe(item.format)}"
        )

    lines += [
        "",
        "Проанализируй канал и верни ответ строго в виде JSON по схеме:",
        RESPONSE_SCHEMA,
        "",
        "Правила:",
        "- Опирайся только на приведённые данные.",
        "- Если для вывода данных не хватает, так и напиши «Данные недоступны».",
        "- В failed_posts перечисли публикации с заметно меньшими просмотрами,",
        "  если просмотры известны. Если неизвестны — верни пустой список.",
        "- Не предлагай копировать чужие тексты.",
        "- Отвечай на русском языке. Верни только JSON, без пояснений вокруг.",
    ]
    return "\n".join(lines)


def parse_response(text: str) -> dict:
    """Достаёт JSON из ответа модели.

    Модель иногда оборачивает JSON в ```json — это учитывается.
    """
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.+?)\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ExternalServiceError(
                "Модель вернула ответ в неожиданном формате. Попробуйте запустить анализ ещё раз."
            ) from None
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ExternalServiceError(
                "Не удалось разобрать ответ модели. Попробуйте запустить анализ ещё раз."
            ) from exc

    if not isinstance(parsed, dict):
        raise ExternalServiceError("Модель вернула ответ в неожиданном формате.")
    return parsed


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _as_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list) and value:
        return "; ".join(str(item) for item in value)
    return None


async def analyze_competitor(
    db: AsyncSession, competitor: Competitor, project_id: uuid.UUID
) -> CompetitorAnalysis:
    """Запрашивает отчёт у модели и сохраняет его."""
    result = await db.execute(
        select(CompetitorPublication).where(
            CompetitorPublication.competitor_id == competitor.id
        )
    )
    publications = list(result.scalars().all())

    if len(publications) < MIN_PUBLICATIONS:
        raise ValidationAppError(
            f"Для анализа нужно минимум {MIN_PUBLICATIONS} публикации конкурента. "
            f"Сейчас сохранено: {len(publications)}. Добавьте их вручную или импортируйте CSV."
        )

    provider = await get_project_provider(db, project_id)
    prompt = build_prompt(competitor, publications)

    competitor.status = CompetitorStatus.ANALYZING
    await db.flush()

    try:
        response = await provider.complete(
            AIRequest(
                prompt=prompt,
                system=system_prompt("competitor_analysis"),
                max_tokens=4096,
                temperature=0.4,
                json_mode=True,
            )
        )
    except Exception:
        competitor.status = CompetitorStatus.ERROR
        await db.flush()
        raise

    payload = parse_response(response.text)

    analysis = CompetitorAnalysis(
        competitor_id=competitor.id,
        project_id=project_id,
        summary=_as_text(payload.get("summary")),
        why_it_works=_as_text(payload.get("why_it_works")),
        publish_rhythm=_as_text(payload.get("publish_rhythm")),
        working_topics=_as_list(payload.get("working_topics")),
        working_titles=_as_list(payload.get("working_titles")),
        failed_posts=_as_list(payload.get("failed_posts")),
        formats=_as_list(payload.get("formats")),
        strengths=_as_list(payload.get("strengths")),
        weaknesses=_as_list(payload.get("weaknesses")),
        content_gaps=_as_list(payload.get("content_gaps")),
        differentiation=_as_list(payload.get("differentiation")),
        adaptable_ideas=_as_list(payload.get("adaptable_ideas")),
        ai_provider=response.provider,
        ai_model=response.model,
        prompt_used=prompt,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
        cost_usd=response.cost_usd,
    )
    db.add(analysis)

    db.add(
        AIUsage(
            project_id=project_id,
            provider=response.provider,
            model=response.model,
            operation="competitor_analysis",
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=response.cost_usd,
            entity_type="competitor",
            entity_id=competitor.id,
        )
    )

    competitor.status = CompetitorStatus.ANALYZED
    competitor.last_analyzed_at = datetime.now(UTC)
    await db.flush()
    return analysis


async def latest_analysis(
    db: AsyncSession, competitor_id: uuid.UUID
) -> CompetitorAnalysis | None:
    result = await db.execute(
        select(CompetitorAnalysis)
        .where(CompetitorAnalysis.competitor_id == competitor_id)
        .order_by(CompetitorAnalysis.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


async def list_analyses(
    db: AsyncSession, competitor_id: uuid.UUID, limit: int = 10
) -> list[CompetitorAnalysis]:
    result = await db.execute(
        select(CompetitorAnalysis)
        .where(CompetitorAnalysis.competitor_id == competitor_id)
        .order_by(CompetitorAnalysis.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
