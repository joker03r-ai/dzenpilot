"""Формула оценки темы от 0 до 100.

Разделение ответственности намеренное: модель ИИ даёт оценки по отдельным
составляющим, а итоговый балл считает обычный код. Поэтому одна и та же тема
с одними и теми же исходными данными всегда получает один и тот же балл,
и пользователю можно показать, из чего он сложился.

Две составляющие инвертированы: чем выше сложность создания статьи и риск
быстрого устаревания, тем ниже вклад в итог.
"""

from __future__ import annotations

from dataclasses import dataclass

FORMULA_VERSION = "1.0"

# Вес каждой составляющей. Сумма равна 100.
WEIGHTS: dict[str, int] = {
    "interest": 18,
    "growth": 12,
    "competition": 12,
    "seasonality": 6,
    "competitor_success": 14,
    "series_potential": 10,
    "commercial": 8,
    "difficulty": 8,
    "decay_risk": 6,
    "audience_fit": 6,
}

# Составляющие, где большее значение означает худший результат
INVERTED = {"difficulty", "decay_risk"}

RU_NAMES: dict[str, str] = {
    "interest": "интерес аудитории",
    "growth": "рост темы",
    "competition": "свободная ниша",
    "seasonality": "устойчивость по сезонам",
    "competitor_success": "успешные публикации конкурентов",
    "series_potential": "возможность серии материалов",
    "commercial": "коммерческий потенциал",
    "difficulty": "простота подготовки",
    "decay_risk": "долгий срок жизни",
    "audience_fit": "соответствие вашей аудитории",
}


@dataclass(slots=True)
class ScoreComponents:
    """Оценки составляющих от 0 до 100."""

    interest: int = 50
    growth: int = 50
    competition: int = 50
    seasonality: int = 50
    competitor_success: int = 50
    series_potential: int = 50
    commercial: int = 50
    difficulty: int = 50
    decay_risk: int = 50
    audience_fit: int = 50

    def clamped(self) -> dict[str, int]:
        return {
            name: max(0, min(100, int(getattr(self, name))))
            for name in WEIGHTS
        }


@dataclass(slots=True)
class ScoreResult:
    total: int
    components: dict[str, int]
    explanation: str
    formula_version: str = FORMULA_VERSION


def _effective(name: str, value: int) -> int:
    """Значение с учётом инверсии: для сложности и устаревания меньше — лучше."""
    return 100 - value if name in INVERTED else value


def calculate(components: ScoreComponents, *, context: str | None = None) -> ScoreResult:
    """Считает итоговый балл и собирает объяснение на русском языке."""
    values = components.clamped()

    weighted_sum = sum(_effective(name, values[name]) * weight for name, weight in WEIGHTS.items())
    total = round(weighted_sum / sum(WEIGHTS.values()))
    total = max(0, min(100, total))

    ranked = sorted(
        ((name, _effective(name, values[name])) for name in WEIGHTS),
        key=lambda item: item[1],
        reverse=True,
    )
    strengths = [RU_NAMES[name] for name, value in ranked[:3] if value >= 60]
    weaknesses = [RU_NAMES[name] for name, value in reversed(ranked[-3:]) if value <= 45]

    parts = [f"Оценка: {total} из 100."]
    if strengths:
        parts.append("Сильные стороны: " + ", ".join(strengths) + ".")
    if weaknesses:
        parts.append("Слабые места: " + ", ".join(weaknesses) + ".")
    if not strengths and not weaknesses:
        parts.append("Показатели средние по всем составляющим.")
    if context:
        parts.append(context)

    return ScoreResult(total=total, components=values, explanation=" ".join(parts))


def competitor_success_signal(
    matching_publications: int, publications_with_views: int, average_views: int | None
) -> tuple[int, str]:
    """Оценка по фактическим данным конкурентов, а не по мнению модели.

    Если публикаций конкурентов по теме нет, возвращается нейтральные 50
    и честная пометка, что данных не хватило.
    """
    if matching_publications == 0:
        return 50, "у конкурентов нет публикаций по этой теме в вашей базе"

    volume_score = min(60, matching_publications * 12)

    if publications_with_views == 0 or average_views is None:
        return (
            min(100, volume_score),
            f"у конкурентов {matching_publications} публикаций по теме, "
            "но данных о просмотрах нет",
        )

    if average_views >= 50_000:
        views_score = 40
    elif average_views >= 20_000:
        views_score = 32
    elif average_views >= 5_000:
        views_score = 22
    elif average_views >= 1_000:
        views_score = 12
    else:
        views_score = 5

    return (
        min(100, volume_score + views_score),
        f"у конкурентов {matching_publications} публикаций по теме, "
        f"средние просмотры {average_views}",
    )


def competition_signal(level: str | None) -> int:
    """Уровень конкуренции в балл. Меньше конкуренции — выше вклад."""
    return {"low": 85, "medium": 55, "high": 25}.get(level or "", 50)


def describe(total: int) -> str:
    """Короткая словесная оценка для интерфейса."""
    if total >= 80:
        return "Отличная тема"
    if total >= 65:
        return "Хорошая тема"
    if total >= 50:
        return "Средняя тема"
    if total >= 35:
        return "Слабая тема"
    return "Мало перспектив"
