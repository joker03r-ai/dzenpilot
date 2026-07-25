"""Единый интерфейс работы с моделями ИИ.

Весь остальной код обращается только к AIProvider. Чтобы добавить новую модель,
достаточно написать ещё одну реализацию и зарегистрировать её в factory.py —
переписывать сервисы не нужно.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class AIRequest:
    """Запрос к модели."""

    prompt: str
    system: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7
    stop_sequences: list[str] = field(default_factory=list)
    json_mode: bool = False


@dataclass(slots=True)
class AIResponse:
    """Ответ модели вместе с расходом токенов."""

    text: str
    provider: str
    model: str
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: Decimal | None = None
    raw: dict | None = None


class AIProvider(ABC):
    """Базовый класс провайдера."""

    name: str = "base"
    title: str = "Базовый провайдер"

    def __init__(self, api_key: str | None, model: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    @abstractmethod
    async def complete(self, request: AIRequest) -> AIResponse:
        """Выполняет запрос и возвращает готовый текст."""

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        """Потоковая выдача. По умолчанию — один блок с полным ответом."""
        response = await self.complete(request)
        yield response.text

    async def healthcheck(self) -> tuple[bool, str]:
        """Короткий проверочный запрос для раздела «Интеграции»."""
        try:
            result = await self.complete(
                AIRequest(prompt="Ответь одним словом: работает", max_tokens=32)
            )
        except Exception as exc:  # noqa: BLE001 — текст ошибки показываем пользователю
            return False, f"Подключение не удалось: {exc}"
        return True, f"Подключение работает. Модель ответила: {result.text.strip()[:120]}"
