"""Safe integration smoke test that never prints credential values or full provider payloads."""

import asyncio

import httpx

from app.core.config import get_settings
from app.services.serpapi import (
    SerpApiClient,
    SerpApiError,
    ServiceNotConfiguredError,
)


async def main() -> None:
    settings = get_settings()
    print(f"DeepSeek configured: {settings.has_deepseek}")
    print(f"Gemini fallback configured: {settings.has_gemini}")
    print(f"SerpApi configured: {settings.has_serpapi}")

    client = SerpApiClient(settings)
    checks = {
        "shopping": client.shopping("khakhra", "Kolkata, West Bengal, India"),
        "maps": client.maps("khakhra shop", "Kolkata, West Bengal, India"),
    }
    for name, operation in checks.items():
        try:
            payload = await operation
            result_key = "shopping_results" if name == "shopping" else "local_results"
            print(
                f"{name}: success; results={len(payload.get(result_key, []))}; "
                f"response_sections={sorted(payload.keys())}"
            )
        except (httpx.HTTPError, SerpApiError, ServiceNotConfiguredError, ValueError) as exc:
            print(f"{name}: failed; {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
