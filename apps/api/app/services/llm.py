import httpx

from app.core.config import Settings
from app.schemas.research import Synthesis
from app.services.deepseek import DeepSeekClient
from app.services.gemini import GeminiClient
from app.services.llm_types import (
    LanguageModelError,
    ResponseModel,
    StructuredLanguageModel,
)
from app.services.serpapi import ServiceNotConfiguredError


class LanguageModelClient:
    """Routes structured generation through the configured primary and fallback providers."""

    def __init__(
        self,
        settings: Settings,
        deepseek: StructuredLanguageModel | None = None,
        gemini: StructuredLanguageModel | None = None,
    ):
        self.settings = settings
        self.deepseek = deepseek or DeepSeekClient(settings)
        self.gemini = gemini or GeminiClient(settings)

    async def synthesize(self, prompt: str) -> Synthesis:
        result, _ = await self.generate_structured(prompt, Synthesis)
        return result

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[ResponseModel],
    ) -> tuple[ResponseModel, str]:
        providers = {
            "deepseek": (self.deepseek, self.settings.has_deepseek),
            "gemini": (self.gemini, self.settings.has_gemini),
        }
        provider_order = [self.settings.llm_provider]
        fallback = self.settings.llm_fallback_provider
        if fallback and fallback not in provider_order:
            provider_order.append(fallback)

        configured = False
        failures: list[str] = []
        for provider_name in provider_order:
            provider, is_configured = providers[provider_name]
            if not is_configured:
                continue
            configured = True
            try:
                return await provider.generate_structured(prompt, response_model)
            except (LanguageModelError, ServiceNotConfiguredError, httpx.HTTPError) as exc:
                detail = str(exc).strip() or type(exc).__name__
                failures.append(f"{provider_name}: {detail}")

        if not configured:
            raise ServiceNotConfiguredError(
                "No language-model API key is configured for the selected provider chain"
            )
        raise LanguageModelError(
            "All configured language-model providers failed: " + "; ".join(failures)
        )
