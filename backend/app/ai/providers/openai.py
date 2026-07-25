"""Провайдер OpenAI (Chat Completions API). Подключается по желанию пользователя."""

from __future__ import annotations

import httpx

from app.ai.base import AIProvider, AIRequest, AIResponse
from app.core.config import settings
from app.core.errors import ExternalServiceError

API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(AIProvider):
    name = "openai"
    title = "OpenAI"

    async def complete(self, request: AIRequest) -> AIResponse:
        if not self.api_key:
            raise ExternalServiceError(
                "Не задан ключ OpenAI. Добавьте его в разделе «Интеграции»."
            )
        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=settings.ai_request_timeout_seconds) as client:
                response = await client.post(
                    self.base_url or API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Не удалось связаться с OpenAI API: {exc}") from exc

        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Ошибка OpenAI API ({response.status_code}): {response.text[:300]}"
            )

        data = response.json()
        choices = data.get("choices", [])
        text = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = data.get("usage", {})
        return AIResponse(
            text=text,
            provider=self.name,
            model=data.get("model", self.model),
            tokens_input=int(usage.get("prompt_tokens", 0)),
            tokens_output=int(usage.get("completion_tokens", 0)),
            raw=data,
        )
