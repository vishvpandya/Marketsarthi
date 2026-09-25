import json
from unittest.mock import AsyncMock

import httpx
import pytest

from app.core.config import Settings
from app.services.gemini import GeminiClient


async def test_gemini_request_uses_auth_header_and_strict_json_schema() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "test-gemini-key"
        assert request.url.path.endswith("/models/gemini-3.8-flash:generateContent")
        body = json.loads(request.content)
        response_format = body["generationConfig"]["responseFormat"]["text"]
        assert response_format["mimeType"] == "APPLICATION_JSON"
        assert "properties" in response_format["schema"]
        synthesis = {
            "headline": "Pilot before expansion",
            "recommendation": "Use a bounded test.",
            "product_changes": [],
            "risks": ["Demand is not directly measured."],
            "next_experiments": ["Test with 50 customers."],
            "confidence": "low",
        }
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": json.dumps(synthesis)}]}}
                ]
            },
        )

    settings = Settings(gemini_api_key="test-gemini-key", _env_file=None)
    client = GeminiClient(settings, transport=httpx.MockTransport(handler))

    result = await client.synthesize("Use only this evidence")

    assert result.headline == "Pilot before expansion"
    assert result.confidence == "low"


async def test_gemini_falls_back_after_temporary_primary_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_models: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_models.append(request.url.path)
        if "gemini-3.8-flash" in request.url.path:
            return httpx.Response(
                503,
                json={"error": {"message": "Temporary high demand"}},
            )
        synthesis = {
            "headline": "Use the fallback",
            "recommendation": "Run a bounded pilot.",
            "product_changes": [],
            "risks": [],
            "next_experiments": [],
            "confidence": "low",
        }
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": json.dumps(synthesis)}]}}
                ]
            },
        )

    monkeypatch.setattr("app.services.gemini.asyncio.sleep", AsyncMock())
    settings = Settings(
        gemini_api_key="test-gemini-key",
        gemini_model="gemini-3.8-flash",
        gemini_fallback_model="gemini-3.6-flash",
        _env_file=None,
    )
    client = GeminiClient(settings, transport=httpx.MockTransport(handler))

    result = await client.synthesize("Use only this evidence")

    assert result.headline == "Use the fallback"
    assert sum("gemini-3.8-flash" in path for path in requested_models) == 3
    assert sum("gemini-3.6-flash" in path for path in requested_models) == 1
