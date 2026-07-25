"""Тесты формулы оценки тем.

Формула должна быть воспроизводимой: одни и те же входные данные
всегда дают один и тот же балл.
"""

from __future__ import annotations

from app.services import topic_scoring
from app.services.topic_scoring import ScoreComponents


def test_weights_sum_to_hundred() -> None:
    assert sum(topic_scoring.WEIGHTS.values()) == 100


def test_score_is_reproducible() -> None:
    components = ScoreComponents(interest=80, growth=70, competition=60)

    first = topic_scoring.calculate(components)
    second = topic_scoring.calculate(components)

    assert first.total == second.total
    assert first.explanation == second.explanation


def test_all_perfect_gives_hundred() -> None:
    perfect = ScoreComponents(
        interest=100, growth=100, competition=100, seasonality=100,
        competitor_success=100, series_potential=100, commercial=100,
        difficulty=0, decay_risk=0, audience_fit=100,
    )

    assert topic_scoring.calculate(perfect).total == 100


def test_all_worst_gives_zero() -> None:
    worst = ScoreComponents(
        interest=0, growth=0, competition=0, seasonality=0,
        competitor_success=0, series_potential=0, commercial=0,
        difficulty=100, decay_risk=100, audience_fit=0,
    )

    assert topic_scoring.calculate(worst).total == 0


def test_difficulty_is_inverted() -> None:
    """Чем сложнее готовить статью, тем ниже итоговый балл."""
    easy = topic_scoring.calculate(ScoreComponents(difficulty=10))
    hard = topic_scoring.calculate(ScoreComponents(difficulty=90))

    assert easy.total > hard.total


def test_decay_risk_is_inverted() -> None:
    stable = topic_scoring.calculate(ScoreComponents(decay_risk=10))
    fleeting = topic_scoring.calculate(ScoreComponents(decay_risk=90))

    assert stable.total > fleeting.total


def test_values_are_clamped_to_range() -> None:
    result = topic_scoring.calculate(ScoreComponents(interest=500, growth=-200))

    assert result.components["interest"] == 100
    assert result.components["growth"] == 0
    assert 0 <= result.total <= 100


def test_explanation_starts_with_score_and_mentions_strengths() -> None:
    result = topic_scoring.calculate(
        ScoreComponents(interest=95, growth=90, competitor_success=88, commercial=20)
    )

    assert result.explanation.startswith(f"Оценка: {result.total} из 100.")
    assert "интерес аудитории" in result.explanation


def test_explanation_can_include_context() -> None:
    result = topic_scoring.calculate(
        ScoreComponents(), context="У конкурентов 5 публикаций по теме."
    )

    assert "У конкурентов 5 публикаций по теме." in result.explanation


def test_competitor_signal_without_publications_is_neutral() -> None:
    score, note = topic_scoring.competitor_success_signal(0, 0, None)

    assert score == 50
    assert "нет публикаций" in note


def test_competitor_signal_without_views_is_honest() -> None:
    score, note = topic_scoring.competitor_success_signal(4, 0, None)

    assert score > 0
    assert "данных о просмотрах нет" in note


def test_competitor_signal_grows_with_views() -> None:
    low, _ = topic_scoring.competitor_success_signal(5, 5, 800)
    high, _ = topic_scoring.competitor_success_signal(5, 5, 60_000)

    assert high > low


def test_competition_signal_prefers_low_competition() -> None:
    assert topic_scoring.competition_signal("low") > topic_scoring.competition_signal("high")
    assert topic_scoring.competition_signal(None) == 50


def test_describe_covers_all_ranges() -> None:
    assert topic_scoring.describe(90) == "Отличная тема"
    assert topic_scoring.describe(70) == "Хорошая тема"
    assert topic_scoring.describe(55) == "Средняя тема"
    assert topic_scoring.describe(40) == "Слабая тема"
    assert topic_scoring.describe(10) == "Мало перспектив"
