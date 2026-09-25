import asyncio
import json
from typing import Any

import httpx

from app.core.config import Settings
from app.schemas.research import Synthesis
from app.services.llm_types import (
    LanguageModelError,
    LanguageModelTemporaryError,
    ResponseModel,
)
from app.services.serpapi import ServiceNotConfiguredError


class GeminiError(LanguageModelError):
    """Raised when Gemini cannot produce a validated response."""


class GeminiTemporaryError(GeminiError, LanguageModelTemporaryError):
    """Raised after retryable Gemini failures have been exhausted."""


class GeminiClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    async def synthesize(self, prompt: str) -> Synthesis:
        result, _ = await self.generate_structured(prompt, Synthesis)
        return result

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[ResponseModel],
    ) -> tuple[ResponseModel, str]:
        if not self.settings.has_gemini:
            raise ServiceNotConfiguredError("GEMINI_API_KEY is not configured")

        models = [self.settings.gemini_model]
        fallback = self.settings.gemini_fallback_model
        if fallback and fallback not in models:
            models.append(fallback)

        last_error: GeminiTemporaryError | None = None
        for model in models:
            try:
                result = await self._generate_with_model(prompt, model, response_model)
                return result, model
            except GeminiTemporaryError as exc:
                last_error = exc

        if last_error is not None:
            raise last_error
        raise GeminiError("No Gemini model is configured")

    async def _generate_with_model(
        self,
        prompt: str,
        model: str,
        response_model: type[ResponseModel],
    ) -> ResponseModel:
        url = (
            f"{self.settings.gemini_base_url}/models/"
            f"{model}:generateContent"
        )
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseFormat": {
                    "text": {
                        "mimeType": "APPLICATION_JSON",
                        "schema": response_model.model_json_schema(),
                    }
                },
                "maxOutputTokens": 3000,
            },
        }
        headers = {
            "x-goog-api-key": self.settings.gemini_api_key.get_secret_value(),
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            for attempt in range(3):
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                    await asyncio.sleep(2**attempt)
                    continue
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    try:
                        error = response.json().get("error", {})
                        detail = error.get("message") or error.get("status")
                    except (TypeError, ValueError):
                        detail = None
                    message = f"Gemini returned HTTP {response.status_code}"
                    if detail:
                        message = f"{message}: {detail}"
                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise GeminiTemporaryError(message) from exc
                    raise GeminiError(message) from exc
                break
            data = response.json()

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return response_model.model_validate(json.loads(text))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            raise GeminiError("Gemini response did not match the requested JSON contract") from exc
