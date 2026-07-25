"""Локальная модель через OpenAI-совместимый интерфейс (Ollama, LM Studio, vLLM).

Адрес задаётся переменной LOCAL_AI_BASE_URL, например http://localhost:11434/v1.
"""

from __future__ import annotations

import httpx

from app.ai.base import AIProvider, AIRequest, AIResponse
from app.core.config import settings
from app.core.errors import ExternalServiceError


class LocalProvider(AIProvider):
    name = "local"
    title = "Локальная модель"

    async def complete(self, request: AIRequest) -> AIResponse:
        base = self.base_url or settings.local_ai_base_url
        if not base:
            raise ExternalServiceError(
                "Не задан адрес локальной модели. Укажите LOCAL_AI_BASE_URL."
            )
        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        try:
            async with httpx.AsyncClient(timeout=settings.ai_request_timeout_seconds) as client:
                response = await client.post(
                    f"{base.rstrip('/')}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": request.max_tokens,
                        "temperature": request.temperature,
                    },
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Локальная модель недоступна: {exc}") from exc

        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Ошибка локальной модели ({response.status_code}): {response.text[:300]}"
            )

        data = response.json()
        choices = data.get("choices", [])
        text = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = data.get("usage", {})
        return AIResponse(
            text=text,
            provider=self.name,
            model=self.model,
            tokens_input=int(usage.get("prompt_tokens", 0)),
            tokens_output=int(usage.get("completion_tokens", 0)),
            raw=data,
        )
