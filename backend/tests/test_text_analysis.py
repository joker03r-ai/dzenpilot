"""Тесты разбора заголовков — он работает без ИИ, поэтому результат воспроизводим."""

from __future__ import annotations

from app.services import text_analysis


def test_detects_numbers_in_title() -> None:
    assert text_analysis.has_numbers("7 фактов о быте XIX века") is True
    assert text_analysis.has_numbers("Как жили крестьяне") is False


def test_detects_question_by_mark_and_by_start() -> None:
    assert text_analysis.has_question("Почему письма шли месяцами") is True
    assert text_analysis.has_question("Кто построил этот мост?") is True
    assert text_analysis.has_question("История одного города") is False


def test_detects_call_to_action() -> None:
    assert text_analysis.has_cta("Подпишитесь, чтобы не пропустить продолжение") is True
    assert text_analysis.has_cta("Обычный заголовок без призыва") is False


def test_emotionality_grows_with_loud_words() -> None:
    calm = text_analysis.title_emotionality("История почтовой связи в России")
    loud = text_analysis.title_emotionality("ШОК! Невероятная тайна, о которой молчали!")

    assert calm < 20
    assert loud > 60
    assert 0 <= calm <= 100 and 0 <= loud <= 100


def test_emotionality_handles_empty_title() -> None:
    assert text_analysis.title_emotionality("") == 0
    assert text_analysis.title_emotionality("   ") == 0


def test_popular_words_skip_stop_words() -> None:
    titles = [
        "Как жили крестьяне в деревне",
        "Как жили горожане в городе",
        "Быт крестьяне и деревня",
    ]
    words = [item["word"] for item in text_analysis.popular_title_words(titles)]

    assert "крестьяне" in words
    assert "как" not in words  # служебное слово отфильтровано
    assert "в" not in words


def test_analyze_title_returns_all_fields() -> None:
    result = text_analysis.analyze_title("5 причин, почему это работает?", "Текст статьи")

    assert result["title_length"] == len("5 причин, почему это работает?")
    assert result["has_numbers"] is True
    assert result["has_question"] is True
    assert result["body_length"] == len("Текст статьи")


def test_title_style_reports_no_data() -> None:
    assert text_analysis.describe_title_style([]) == "Данные недоступны"


def test_title_style_mentions_questions_and_numbers() -> None:
    style = text_analysis.describe_title_style(
        ["Почему это так?", "Как это устроено?", "7 фактов", "5 причин"]
    )

    assert "вопрос" in style.lower() or "числ" in style.lower()


def test_reading_time_is_at_least_one_minute() -> None:
    assert text_analysis.reading_time_minutes("слово " * 100) >= 1
    assert text_analysis.reading_time_minutes("") == 0
