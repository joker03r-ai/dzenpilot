"""Разбор заголовков и текстов без обращения к ИИ.

Все показатели считаются по правилам, поэтому результат воспроизводим,
не стоит денег и покрыт тестами. ИИ подключается отдельно — там, где нужен
смысловой вывод, а не арифметика.
"""

from __future__ import annotations

import re
from collections import Counter

# Слова, которые усиливают эмоциональную окраску заголовка
EMOTIONAL_WORDS = {
    "шок", "шокирующий", "невероятный", "сенсация", "тайна", "секрет", "правда",
    "разоблачение", "скандал", "ужас", "катастрофа", "провал", "победа", "чудо",
    "удивительный", "поразительный", "неожиданный", "странный", "загадка",
    "запрещённый", "запрещенный", "опасный", "срочно", "внимание", "важно",
    "никогда", "всегда", "лучший", "худший", "главный", "единственный",
    "впервые", "наконец", "оказывается", "внезапно",
}

# Признаки призыва к действию.
# «подпи\w*» покрывает и «подпишитесь», и «подписаться», и «подписка»:
# корень меняется, поэтому обрывать шаблон на «подпис» нельзя.
CTA_PATTERNS = [
    r"\bподпи\w*", r"\bставьте\b", r"\bжми\w*", r"\bчитайте\b", r"\bузнай\w*",
    r"\bсмотрите\b", r"\bпишите\b", r"\bделитесь\b", r"\bподелит\w*",
    r"\bкоммент\w*", r"\bлайк\w*", r"\bсохрани\w*", r"\bпопробуйте\b",
    r"\bскачайте\b", r"\bоставьте\b", r"\bнапишите\b",
]

# Служебные слова, которые не показательны в статистике заголовков
STOP_WORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то",
    "все", "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за",
    "бы", "по", "только", "ее", "мне", "было", "вот", "от", "меня", "еще",
    "нет", "о", "из", "ему", "теперь", "когда", "даже", "ну", "вдруг", "ли",
    "если", "уже", "или", "ни", "быть", "был", "него", "до", "вас", "нибудь",
    "опять", "уж", "вам", "ведь", "там", "потом", "себя", "ничего", "ей",
    "может", "они", "тут", "где", "есть", "надо", "ней", "для", "мы", "тебя",
    "их", "чем", "была", "сам", "чтоб", "без", "будто", "чего", "раз", "тоже",
    "себе", "под", "будет", "ж", "тогда", "кто", "этот", "того", "потому",
    "этого", "какой", "совсем", "ним", "здесь", "этом", "один", "почти",
    "мой", "тем", "чтобы", "нее", "были", "куда", "зачем", "всех", "никогда",
    "можно", "при", "наконец", "два", "об", "другой", "хоть", "после", "над",
    "больше", "тот", "через", "эти", "нас", "про", "всего", "них", "какая",
    "много", "разве", "три", "эту", "моя", "впрочем", "свою", "этой", "перед",
    "иногда", "лучше", "чуть", "том", "нельзя", "такой", "им", "более", "всю",
    "между", "это", "её", "ещё",
}

QUESTION_STARTERS = (
    "почему", "как", "что", "где", "когда", "зачем", "кто", "какой", "какая",
    "какие", "сколько", "стоит ли", "можно ли", "правда ли",
)


def title_length(title: str) -> int:
    return len(title.strip())


def has_numbers(text: str) -> bool:
    return bool(re.search(r"\d", text))


def has_question(title: str) -> bool:
    """Вопрос — это либо знак вопроса, либо вопросительное начало."""
    normalized = title.strip().lower()
    if "?" in normalized:
        return True
    return normalized.startswith(QUESTION_STARTERS)


def has_cta(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in CTA_PATTERNS)


def title_emotionality(title: str) -> int:
    """Оценка эмоциональности заголовка от 0 до 100.

    Складывается из четырёх сигналов: эмоциональные слова, восклицание,
    капслок и превосходная степень. Это оценка формы, а не качества.
    """
    if not title.strip():
        return 0

    words = re.findall(r"[а-яёa-z]+", title.lower())
    if not words:
        return 0

    score = 0

    emotional_hits = sum(1 for word in words if word in EMOTIONAL_WORDS)
    score += min(45, emotional_hits * 22)

    score += min(20, title.count("!") * 15)

    # Слова капслоком длиннее двух букв — признак крика в заголовке
    caps_words = [word for word in title.split() if len(word) > 2 and word.isupper()]
    score += min(20, len(caps_words) * 12)

    if re.search(r"\b(самый|самая|самые|лучш\w+|худш\w+|единственн\w+)\b", title.lower()):
        score += 15

    return max(0, min(100, score))


def body_length(text: str | None) -> int | None:
    return len(text.strip()) if text else None


def word_count(text: str | None) -> int:
    if not text:
        return 0
    return len(re.findall(r"\S+", text))


def reading_time_minutes(text: str | None) -> int:
    """Средняя скорость чтения на русском — примерно 180 слов в минуту."""
    words = word_count(text)
    return max(1, round(words / 180)) if words else 0


def popular_title_words(titles: list[str], limit: int = 15) -> list[dict[str, object]]:
    """Самые частые значимые слова в заголовках."""
    counter: Counter[str] = Counter()
    for title in titles:
        for word in re.findall(r"[а-яёa-z]{3,}", title.lower()):
            if word not in STOP_WORDS:
                counter[word] += 1

    return [
        {"word": word, "count": count}
        for word, count in counter.most_common(limit)
        if count > 1
    ]


def analyze_title(title: str, body: str | None = None) -> dict[str, object]:
    """Полный разбор одного заголовка."""
    return {
        "title_length": title_length(title),
        "body_length": body_length(body),
        "title_emotionality": title_emotionality(title),
        "has_numbers": has_numbers(title),
        "has_question": has_question(title),
        "has_cta": has_cta(f"{title} {body or ''}"),
    }


def describe_title_style(titles: list[str]) -> str:
    """Короткое описание стиля заголовков — для таблицы сравнения."""
    if not titles:
        return "Данные недоступны"

    total = len(titles)
    questions = sum(1 for title in titles if has_question(title))
    numbers = sum(1 for title in titles if has_numbers(title))
    average_emotion = sum(title_emotionality(title) for title in titles) / total
    average_length = sum(title_length(title) for title in titles) / total

    parts: list[str] = []
    if questions / total > 0.3:
        parts.append("часто вопросы")
    if numbers / total > 0.3:
        parts.append("часто числа")
    if average_emotion > 45:
        parts.append("яркая подача")
    elif average_emotion < 15:
        parts.append("спокойная подача")
    parts.append(f"длина около {round(average_length)} знаков")

    return ", ".join(parts).capitalize()
