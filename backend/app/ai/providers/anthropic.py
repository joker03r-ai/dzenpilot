"""Провайдер Anthropic Claude — основная модель сервиса.

Используется прямой HTTP-вызов Messages API через httpx: так у всех провайдеров
одинаковая реализация и нет зависимости от версий разных SDK.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from decimal import Decimal

import httpx

from app.ai.base import AIProvider, AIRequest, AIResponse
from app.core.config import settings
from app.core.errors import ExternalServiceError

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"

# Цена за миллион токенов в долларах. Используется только для оценки затрат;
# если модели нет в таблице, стоимость не рассчитывается.
PRICING: dict[str, tuple[Decimal, Decimal]] = {
    "claude-opus-5": (Decimal("5"), Decimal("25")),
    "claude-sonnet-5": (Decimal("3"), Decimal("15")),
    "claude-haiku-4-5-20251001": (Decimal("1"), Decimal("5")),
}


class AnthropicProvider(AIProvider):
    name = "anthropic"
    title = "Anthropic Claude"

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ExternalServiceError(
                "Не задан ключ Anthropic. Добавьте его в разделе «Интеграции»."
            )
        return {
            "x-api-key": self.api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }

    def _payload(self, request: AIRequest, stream: bool = False) -> dict:
        payload: dict = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system:
            payload["system"] = request.system
        if request.stop_sequences:
            payload["stop_sequences"] = request.stop_sequences
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def _cost(model: str, tokens_in: int, tokens_out: int) -> Decimal | None:
        prices = PRICING.get(model)
        if not prices:
            return None
        price_in, price_out = prices
        million = Decimal(1_000_000)
        return (
            Decimal(tokens_in) / million * price_in + Decimal(tokens_out) / million * price_out
        ).quantize(Decimal("0.0001"))

    async def complete(self, request: AIRequest) -> AIResponse:
        try:
            async with httpx.AsyncClient(timeout=settings.ai_request_timeout_seconds) as client:
                response = await client.post(
                    self.base_url or API_URL,
                    headers=self._headers(),
                    json=self._payload(request),
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Не удалось связаться с Anthropic API: {exc}") from exc

        if response.status_code >= 400:
            raise ExternalServiceError(_error_text(response))

        data = response.json()
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        tokens_in = int(usage.get("input_tokens", 0))
        tokens_out = int(usage.get("output_tokens", 0))
        return AIResponse(
            text=text,
            provider=self.name,
            model=data.get("model", self.model),
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cost_usd=self._cost(self.model, tokens_in, tokens_out),
            raw=data,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=settings.ai_request_timeout_seconds) as client:
            async with client.stream(
                "POST",
                self.base_url or API_URL,
                headers=self._headers(),
                json=self._payload(request, stream=True),
            ) as response:
                if response.status_code >= 400:
                    await response.aread()
                    raise ExternalServiceError(_error_text(response))
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "content_block_delta":
                        chunk = event.get("delta", {}).get("text", "")
                        if chunk:
                            yield chunk


def _error_text(response: httpx.Response) -> str:
    """Понятное сообщение вместо технического ответа API."""
    hints = {
        401: "Ключ Anthropic недействителен. Проверьте его в разделе «Интеграции».",
        403: "Доступ запрещён. Проверьте права ключа Anthropic.",
        404: "Модель не найдена. Выберите другую модель в настройках.",
        429: "Превышен лимит запросов Anthropic. Повторите через минуту.",
        529: "Сервис Anthropic перегружен. Повторите попытку позже.",
    }
    if response.status_code in hints:
        return hints[response.status_code]
    try:
        detail = response.json().get("error", {}).get("message", "")
    except (ValueError, AttributeError):
        detail = response.text[:300]
    return f"Ошибка Anthropic API ({response.status_code}): {detail}"
