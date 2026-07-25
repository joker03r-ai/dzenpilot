"""Провайдер Google Gemini. Подключается по желанию пользователя."""

from __future__ import annotations

import httpx

from app.ai.base import AIProvider, AIRequest, AIResponse
from app.core.config import settings
from app.core.errors import ExternalServiceError

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(AIProvider):
    name = "gemini"
    title = "Google Gemini"

    async def complete(self, request: AIRequest) -> AIResponse:
        if not self.api_key:
            raise ExternalServiceError(
                "Не задан ключ Gemini. Добавьте его в разделе «Интеграции»."
            )
        url = f"{self.base_url or API_BASE}/{self.model}:generateContent"
        payload: dict = {
            "contents": [{"role": "user", "parts": [{"text": request.prompt}]}],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        if request.system:
            payload["systemInstruction"] = {"parts": [{"text": request.system}]}

        try:
            async with httpx.AsyncClient(timeout=settings.ai_request_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    params={"key": self.api_key},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Не удалось связаться с Gemini API: {exc}") from exc

        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Ошибка Gemini API ({response.status_code}): {response.text[:300]}"
            )

        data = response.json()
        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts)
        usage = data.get("usageMetadata", {})
        return AIResponse(
            text=text,
            provider=self.name,
            model=self.model,
            tokens_input=int(usage.get("promptTokenCount", 0)),
            tokens_output=int(usage.get("candidatesTokenCount", 0)),
            raw=data,
        )
