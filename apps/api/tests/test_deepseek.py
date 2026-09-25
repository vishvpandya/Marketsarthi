import json

import httpx

from app.core.config import Settings
from app.schemas.research import Synthesis
from app.services.deepseek import DeepSeekClient, DeepSeekTemporaryError
from app.services.llm import LanguageModelClient


def synthesis_payload(headline: str) -> dict[str, object]:
    return {
        "headline": headline,
        "recommendation": "Run a bounded pilot.",
        "product_changes": [],
        "risks": ["Demand is not directly measured."],
        "next_experiments": ["Test with a small number of shops."],
        "confidence": "low",
        "competitor_classifications": [],
    }


async def test_deepseek_uses_v41_flash_in_non_thinking_json_mode() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/chat/completions"
        assert request.headers["authorization"] == "Bearer test-deepseek-key"
        body = json.loads(request.content)
        assert body["model"] == "deepseek-flash"
        assert body["thinking"] == {"type": "disabled"}
        assert body["response_format"] == {"type": "json_object"}
        assert "headline" in body["messages"][0]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": json.dumps(synthesis_payload("Use a pilot"))}}
                ]
            },
        )

    settings = Settings(deepseek_api_key="test-deepseek-key", _env_file=None)
    client = DeepSeekClient(settings, transport=httpx.MockTransport(handler))

    result, model = await client.generate_structured("Use only this evidence", Synthesis)

    assert model == "deepseek-flash"
    assert result.headline == "Use a pilot"


async def test_language_model_router_uses_gemini_after_deepseek_failure() -> None:
    class FailingDeepSeek:
        async def generate_structured(self, prompt: str, response_model: type[Synthesis]):
            raise DeepSeekTemporaryError("temporary capacity problem")

    class WorkingGemini:
        async def generate_structured(self, prompt: str, response_model: type[Synthesis]):
            return response_model.model_validate(synthesis_payload("Fallback worked")), "gemini-test"

    settings = Settings(
        deepseek_api_key="test-deepseek-key",
        gemini_api_key="test-gemini-key",
        _env_file=None,
    )
    client = LanguageModelClient(
        settings,
        deepseek=FailingDeepSeek(),  # type: ignore[arg-type]
        gemini=WorkingGemini(),  # type: ignore[arg-type]
    )

    result, model = await client.generate_structured("Use only this evidence", Synthesis)

    assert model == "gemini-test"
    assert result.headline == "Fallback worked"
