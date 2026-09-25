from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(prefix="/health", tags=["health"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@router.get("/ready")
async def ready(settings: SettingsDependency) -> dict[str, object]:
    configured = {
        "deepseek": settings.has_deepseek,
        "gemini": settings.has_gemini,
        "serpapi": settings.has_serpapi,
        "typesafe_jev": settings.has_typesafe,
    }
    return {
        "status": "ready" if settings.has_serpapi and settings.has_llm else "configuration_required",
        "services": configured,
        "llm_provider": settings.llm_provider,
        "llm_fallback_provider": settings.llm_fallback_provider,
        "model": settings.primary_llm_model,
        "live_analysis_available": settings.has_serpapi,
        "full_synthesis_available": settings.has_serpapi and settings.has_llm,
        "jev_classification_available": settings.has_typesafe,
    }
