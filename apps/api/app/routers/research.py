from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.research import (
    AnalysisMode,
    CopilotRequest,
    CopilotResponse,
    DecisionSummaryRequest,
    DecisionSummaryResponse,
    MerchantResearchRequest,
    PilotReviewRequest,
    PilotReviewResponse,
    ResearchBriefResponse,
    ResearchRefreshRequest,
    ResearchResponse,
)
from app.services.copilot import CopilotService
from app.services.llm_types import LanguageModelError
from app.services.pilot_review import PilotReviewService
from app.services.research import ResearchService, build_research_plan
from app.services.serpapi import SerpApiError, ServiceNotConfiguredError

router = APIRouter(prefix="/research", tags=["research"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("/preview", response_model=ResearchResponse)
async def preview(request: MerchantResearchRequest) -> ResearchResponse:
    return ResearchResponse(
        mode=AnalysisMode.PLAN_ONLY,
        plan=build_research_plan(request),
        warnings=["Preview mode does not call SerpApi or an AI model and consumes no credits."],
    )


@router.post("/brief", response_model=ResearchBriefResponse)
async def generate_brief(
    request: MerchantResearchRequest,
    settings: SettingsDependency,
) -> ResearchBriefResponse:
    try:
        return await ResearchService(settings).generate_brief(request)
    except ServiceNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "service_not_configured",
                "message": str(exc),
                "next_step": "Add DEEPSEEK_API_KEY or the configured fallback key to the root .env file and restart the API.",
            },
        ) from exc
    except (LanguageModelError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "brief_generation_error", "message": str(exc)},
        ) from exc


@router.post("/analyze", response_model=ResearchResponse)
async def analyze(
    request: MerchantResearchRequest,
    settings: SettingsDependency,
) -> ResearchResponse:
    try:
        return await ResearchService(settings).analyze(request)
    except ServiceNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "service_not_configured",
                "message": str(exc),
                "next_step": "Add the missing key to the root .env file and restart the API.",
            },
        ) from exc
    except SerpApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "research_provider_error", "message": str(exc)},
        ) from exc


@router.post("/refresh", response_model=ResearchResponse)
async def refresh_research(
    refresh_request: ResearchRefreshRequest,
    settings: SettingsDependency,
) -> ResearchResponse:
    try:
        return await ResearchService(settings).refresh_sections(
            refresh_request.request,
            refresh_request.current_result,
            refresh_request.sections,
        )
    except ServiceNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_not_configured", "message": str(exc)},
        ) from exc
    except SerpApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "research_provider_error", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "research_context_changed", "message": str(exc)},
        ) from exc


@router.post("/decision-summary", response_model=DecisionSummaryResponse)
async def update_decision_summary(
    summary_request: DecisionSummaryRequest,
    settings: SettingsDependency,
) -> DecisionSummaryResponse:
    try:
        return await ResearchService(settings).update_decision_summary(
            summary_request.request,
            summary_request.current_result,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "research_context_changed", "message": str(exc)},
        ) from exc


@router.post("/copilot", response_model=CopilotResponse)
async def ask_copilot(
    copilot_request: CopilotRequest,
    settings: SettingsDependency,
) -> CopilotResponse:
    return await CopilotService(settings).answer(copilot_request)


@router.post("/pilot-review", response_model=PilotReviewResponse)
async def review_pilot(
    request: PilotReviewRequest,
    settings: SettingsDependency,
) -> PilotReviewResponse:
    return await PilotReviewService(settings).review(request)
