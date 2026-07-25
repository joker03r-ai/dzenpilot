"""Генерация структуры, текста и доработка статьи.

Правила, которые модель обязана соблюдать, заданы в системном промте:
не выдумывать факты, помечать непроверенные утверждения строкой
«Требуется проверка факта», не придумывать ссылки и не копировать конкурентов.
"""

from __future__ import annotations

import json
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIRequest, AIResponse
from app.ai.factory import get_project_provider
from app.ai.prompts import system_prompt
from app.core.errors import ExternalServiceError, ValidationAppError
from app.models.ai import AIUsage
from app.models.article import Article
from app.models.project import Project
from app.schemas.article import (
    ADVISORY_ACTIONS,
    IMPROVE_LABELS,
    GenerateRequest,
    ImproveRequest,
    OutlineResponse,
    OutlineSection,
)
from app.services import article_service

OUTLINE_SCHEMA = """{
  "title_variants": ["десять вариантов заголовка"],
  "lead": "вступление на 2-4 предложения",
  "sections": [
    {"heading": "подзаголовок", "points": ["тезис", "тезис"]}
  ],
  "conclusion": "заключение",
  "cta": "призыв к действию"
}"""


def _extract_json(text: str) -> dict:
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
                "Модель вернула ответ в неожиданном формате. Попробуйте ещё раз."
            ) from None
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ExternalServiceError(
                "Не удалось разобрать ответ модели. Попробуйте ещё раз."
            ) from exc

    if not isinstance(parsed, dict):
        raise ExternalServiceError("Модель вернула ответ в неожиданном формате.")
    return parsed


def _context_lines(article: Article, project: Project) -> list[str]:
    """Общий контекст, который передаётся модели на всех шагах."""
    generation_input = article.generation_input or {}
    lines = [
        f"Тема статьи: {article.title}",
        f"Цель статьи: {article.goal or 'привлечь и удержать читателя'}",
        f"Аудитория: {article.audience or project.target_audience or 'широкая аудитория Дзена'}",
        f"Тон общения: {article.tone or project.tone_of_voice or 'живой, без канцелярита'}",
        f"Примерный объём: {article.target_length or 7000} знаков",
        f"Регион: {generation_input.get('region') or project.region or 'Россия'}",
    ]

    if article.keywords:
        lines.append("Ключевые слова: " + ", ".join(str(item) for item in article.keywords))

    facts = generation_input.get("required_facts") or []
    if facts:
        lines.append("Обязательно использовать эти факты:")
        lines += [f"- {item}" for item in facts]

    links = generation_input.get("source_links") or []
    if links:
        lines.append("Источники, на которые можно ссылаться:")
        lines += [f"- {item}" for item in links]

    products = generation_input.get("products") or []
    if products:
        lines.append("Упомянуть товары или услуги: " + ", ".join(str(item) for item in products))

    forbidden = generation_input.get("forbidden_words") or []
    if forbidden:
        lines.append("Запрещённые слова, не использовать: " + ", ".join(str(w) for w in forbidden))

    if article.cta:
        lines.append(f"Призыв к действию: {article.cta}")

    return lines


async def _track_usage(
    db: AsyncSession,
    project_id: uuid.UUID,
    article: Article,
    response: AIResponse,
    operation: str,
) -> None:
    db.add(
        AIUsage(
            project_id=project_id,
            provider=response.provider,
            model=response.model,
            operation=operation,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=response.cost_usd,
            entity_type="article",
            entity_id=article.id,
        )
    )
    article.ai_provider = response.provider
    article.ai_model = response.model
    article.tokens_input = (article.tokens_input or 0) + response.tokens_input
    article.tokens_output = (article.tokens_output or 0) + response.tokens_output
    if response.cost_usd is not None:
        article.cost_usd = (article.cost_usd or 0) + response.cost_usd


# --------------------------------------------------------------------------
# Шаг 2. Структура
# --------------------------------------------------------------------------

async def generate_outline(
    db: AsyncSession, article: Article, project: Project
) -> OutlineResponse:
    provider = await get_project_provider(db, project.id)

    prompt = "\n".join(
        [
            *_context_lines(article, project),
            "",
            "Составь структуру статьи для Яндекс Дзена.",
            "Нужно ровно 10 вариантов заголовка: разных по приёму — с числом,",
            "с вопросом, с обещанием пользы, с интригой без обмана.",
            "План должен состоять из 4-7 разделов, у каждого 2-4 тезиса.",
            "",
            "Верни ответ строго в виде JSON по схеме:",
            OUTLINE_SCHEMA,
            "",
            "Верни только JSON, без пояснений вокруг.",
        ]
    )

    response = await provider.complete(
        AIRequest(
            prompt=prompt,
            system=system_prompt("article_outline"),
            max_tokens=4000,
            temperature=0.8,
            json_mode=True,
        )
    )
    payload = _extract_json(response.text)

    variants = [
        str(item).strip()
        for item in (payload.get("title_variants") or [])
        if str(item).strip()
    ][:10]

    sections: list[OutlineSection] = []
    for raw in payload.get("sections") or []:
        if not isinstance(raw, dict):
            continue
        heading = str(raw.get("heading", "")).strip()
        if not heading:
            continue
        points = [str(point).strip() for point in (raw.get("points") or []) if str(point).strip()]
        sections.append(OutlineSection(heading=heading, points=points[:6]))

    if not sections:
        raise ExternalServiceError(
            "Модель не вернула план статьи. Уточните тему и попробуйте ещё раз."
        )

    lead = str(payload.get("lead", "") or "").strip()
    conclusion = str(payload.get("conclusion", "") or "").strip()
    cta = str(payload.get("cta", "") or article.cta or "").strip()

    article.lead = lead or article.lead
    article.cta = cta or article.cta
    article.outline = [
        {"heading": section.heading, "points": section.points} for section in sections
    ]
    article.generation_input = {
        **(article.generation_input or {}),
        "title_variants": variants,
        "conclusion": conclusion,
    }

    await _track_usage(db, project.id, article, response, "article_outline")
    await db.flush()

    return OutlineResponse(
        title_variants=variants,
        lead=lead,
        sections=sections,
        conclusion=conclusion,
        cta=cta,
        message=(
            "Структура готова. Отредактируйте план, если нужно, "
            "и переходите к генерации текста."
        ),
    )


# --------------------------------------------------------------------------
# Шаг 3. Полный текст
# --------------------------------------------------------------------------

async def generate_body(
    db: AsyncSession,
    article: Article,
    project: Project,
    request: GenerateRequest,
    user_id: uuid.UUID,
) -> Article:
    if request.use_outline and not article.outline:
        raise ValidationAppError(
            "Сначала создайте структуру статьи — это шаг 2 мастера."
        )

    provider = await get_project_provider(db, project.id)
    generation_input = article.generation_input or {}

    plan_lines: list[str] = []
    if request.use_outline:
        plan_lines.append("План статьи, которого нужно придерживаться:")
        for index, section in enumerate(article.outline, start=1):
            heading = section.get("heading") if isinstance(section, dict) else str(section)
            plan_lines.append(f"{index}. {heading}")
            points = section.get("points", []) if isinstance(section, dict) else []
            plan_lines += [f"   - {point}" for point in points]
        if generation_input.get("conclusion"):
            plan_lines.append(f"Заключение: {generation_input['conclusion']}")

    prompt = "\n".join(
        [
            *_context_lines(article, project),
            "",
            *plan_lines,
            *([f"Вступление: {article.lead}"] if article.lead else []),
            *([request.extra_instructions] if request.extra_instructions else []),
            "",
            "Напиши готовую статью в формате Markdown.",
            "Требования:",
            "- подзаголовки уровня ##;",
            "- короткие абзацы по 2-4 предложения;",
            "- без воды и повторов;",
            "- ключевые слова вставляй естественно, не более двух раз каждое;",
            "- не выдумывай цифры, даты, цитаты и имена;",
            "- каждое утверждение, которое требует проверки, помечай отдельной строкой",
            "  «Требуется проверка факта»;",
            "- не придумывай ссылки: если источника нет, так и напиши;",
            "- не копируй чужие тексты;",
            "- заверши статью призывом к действию.",
            "",
            "Верни только текст статьи без пояснений и без заголовка первого уровня.",
        ]
    )

    response = await provider.complete(
        AIRequest(
            prompt=prompt,
            system=system_prompt("article_write"),
            max_tokens=max(4000, min(16000, (article.target_length or 7000) // 2)),
            temperature=0.75,
        )
    )

    body = response.text.strip()
    if not body:
        raise ExternalServiceError("Модель вернула пустой текст. Попробуйте ещё раз.")

    if article.body_markdown:
        await article_service.save_version(db, article, "Перед новой генерацией", user_id)

    article.body_markdown = body
    article.prompt_used = prompt
    article_service.refresh_counters(article)

    await _track_usage(db, project.id, article, response, "article_write")
    await article_service.save_version(db, article, "Сгенерировано моделью", user_id)
    await db.flush()
    return article


# --------------------------------------------------------------------------
# Шаг 4. Доработка
# --------------------------------------------------------------------------

ACTION_PROMPTS: dict[str, str] = {
    "shorten": "Сократи текст примерно на треть, сохранив все факты и структуру.",
    "expand": "Расширь текст примерно в полтора раза: добавь подробности и пояснения, "
    "но не воду и не выдуманные факты.",
    "simplify": "Перепиши проще: короткие предложения, обычные слова, без терминов. "
    "Читатель — обычный человек без специальной подготовки.",
    "expertise": "Сделай текст экспертнее: точнее формулировки, больше конкретики "
    "и профессиональных деталей. Не добавляй непроверяемые утверждения.",
    "change_tone": "Измени тон текста согласно указанию пользователя, смысл сохрани.",
    "rewrite_fragment": "Перепиши только переданный фрагмент. Верни новый вариант фрагмента.",
    "add_examples": "Добавь конкретные примеры и жизненные ситуации там, где их не хватает. "
    "Примеры должны быть правдоподобными и обобщёнными, без выдуманных имён и цифр.",
    "remove_repeats": "Убери повторы мыслей и однотипные формулировки. Объём может уменьшиться.",
    "check_structure": "Оцени структуру статьи: логика разделов, порядок мыслей, "
    "переходы. Дай список конкретных замечаний и предложений.",
    "check_title": "Оцени заголовок: понятность, обещание, длина, отсутствие обмана. "
    "Предложи три улучшенных варианта.",
    "check_clickability": "Оцени кликабельность заголовка и вступления в ленте Дзена. "
    "Объясни, что заставит человека открыть статью, а что оттолкнёт.",
    "check_readability": "Оцени читаемость с телефона: длина абзацев и предложений, "
    "сложные слова. Дай список замечаний.",
    "find_unverified": "Найди в тексте все утверждения, которые требуют проверки: "
    "цифры, даты, имена, ссылки на исследования. Выведи их списком с цитатой из текста.",
    "image_description": "Опиши, какие изображения подойдут статье: обложка и 2-3 "
    "иллюстрации. Для каждого укажи, что на нём и зачем оно нужно.",
    "image_prompts": "Составь промты на английском языке для генерации изображений "
    "к статье: обложка и 2-3 иллюстрации. Каждый промт отдельной строкой.",
}


async def improve(
    db: AsyncSession,
    article: Article,
    project: Project,
    request: ImproveRequest,
    user_id: uuid.UUID,
) -> tuple[str, bool]:
    """Возвращает результат и признак, изменился ли текст статьи."""
    if not article.body_markdown:
        raise ValidationAppError("Сначала сгенерируйте или вставьте текст статьи.")

    if request.action == "rewrite_fragment" and not (request.fragment or "").strip():
        raise ValidationAppError("Выделите фрагмент, который нужно переписать.")
    if request.action == "change_tone" and not (request.instruction or "").strip():
        raise ValidationAppError("Укажите, какой тон нужен, например «дружелюбный».")

    provider = await get_project_provider(db, project.id)
    advisory = request.action in ADVISORY_ACTIONS

    target = (
        request.fragment
        if request.action == "rewrite_fragment"
        else article.body_markdown
    )

    prompt_parts = [
        f"Заголовок статьи: {article.title}",
        f"Аудитория: {article.audience or 'широкая аудитория Дзена'}",
        f"Тон: {article.tone or 'живой, без канцелярита'}",
        "",
        "Задача: " + ACTION_PROMPTS[request.action],
    ]
    if request.instruction:
        prompt_parts.append(f"Уточнение пользователя: {request.instruction}")

    prompt_parts += [
        "",
        "Текст:",
        "---",
        target or "",
        "---",
        "",
        (
            "Верни только заключение или список замечаний на русском языке. "
            "Текст статьи переписывать не нужно."
            if advisory
            else "Верни только готовый текст в формате Markdown, без пояснений вокруг."
        ),
    ]

    response = await provider.complete(
        AIRequest(
            prompt="\n".join(prompt_parts),
            system=system_prompt("article_improve"),
            max_tokens=12000 if not advisory else 3000,
            temperature=0.4 if advisory else 0.7,
        )
    )

    result = response.text.strip()
    if not result:
        raise ExternalServiceError("Модель вернула пустой ответ. Попробуйте ещё раз.")

    applied = False
    if not advisory:
        await article_service.save_version(
            db, article, f"Перед действием «{IMPROVE_LABELS[request.action]}»", user_id
        )
        if request.action == "rewrite_fragment" and request.fragment:
            article.body_markdown = article.body_markdown.replace(request.fragment, result, 1)
        else:
            article.body_markdown = result
        article_service.refresh_counters(article)
        applied = True

    await _track_usage(db, project.id, article, response, f"article_{request.action}")
    await db.flush()
    return result, applied
