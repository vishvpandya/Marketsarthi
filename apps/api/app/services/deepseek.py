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


class DeepSeekError(LanguageModelError):
    """Raised when DeepSeek cannot produce a validated response."""


class DeepSeekTemporaryError(DeepSeekError, LanguageModelTemporaryError):
    """Raised after retryable DeepSeek failures have been exhausted."""


class DeepSeekClient:
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
        if not self.settings.has_deepseek:
            raise ServiceNotConfiguredError("DEEPSEEK_API_KEY is not configured")

        result = await self._generate_with_model(
            prompt,
            self.settings.deepseek_model,
            response_model,
        )
        return result, self.settings.deepseek_model

    async def _generate_with_model(
        self,
        prompt: str,
        model: str,
        response_model: type[ResponseModel],
    ) -> ResponseModel:
        schema = json.dumps(response_model.model_json_schema(), separators=(",", ":"))
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return exactly one valid JSON object. Do not use Markdown or add text "
                        f"outside the object. The JSON must match this schema: {schema}"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "max_tokens": 3000,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        url = f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"
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
                        detail = error.get("message") or error.get("type")
                    except (AttributeError, TypeError, ValueError):
                        detail = None
                    message = f"DeepSeek returned HTTP {response.status_code}"
                    if detail:
                        message = f"{message}: {detail}"
                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise DeepSeekTemporaryError(message) from exc
                    raise DeepSeekError(message) from exc
                break
            data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("DeepSeek message content was not text")
            return response_model.model_validate(json.loads(content))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            raise DeepSeekError(
                "DeepSeek response did not match the requested JSON contract"
            ) from exc
