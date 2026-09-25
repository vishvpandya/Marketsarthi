from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.schemas.research import (
    AnalysisMode,
    CityEvidenceSummary,
    CompetitorType,
    CopilotDraft,
    CopilotMerchantContext,
    CopilotRequest,
    EvidenceItem,
    EvidenceScope,
    EvidenceType,
    MerchantResearchRequest,
    RefreshSection,
    ResearchResponse,
)
from app.services.copilot import CopilotService
from app.services.research import build_research_plan

client = TestClient(app)


def make_request() -> CopilotRequest:
    merchant = CopilotMerchantContext(
        product_name="Roasted methi khakhra",
        category="Packaged healthy snacks",
        current_city="Bolpur, West Bengal",
        target_cities=["Kolkata"],
        price_min_inr=120,
        price_max_inr=180,
        pack_size="200 g",
    )
    research_request = {
        "product_name": merchant.product_name,
        "category": merchant.category,
        "current_city": merchant.current_city,
        "target_cities": merchant.target_cities,
        "price_min_inr": merchant.price_min_inr,
        "price_max_inr": merchant.price_max_inr,
        "pack_size": merchant.pack_size,
    }
    evidence = EvidenceItem(
        evidence_type=EvidenceType.SHOPPING,
        city="Kolkata",
        title="Roasted methi khakhra 200g",
        observation="Seller: Example merchant; Listed price: ₹149",
        source_name="Example merchant",
        source_url="https://example.com/khakhra",
        engine="google_shopping",
        evidence_scope=EvidenceScope.CITY_LOCAL,
        competitor_type=CompetitorType.DIRECT,
        retrieved_at=datetime(2026, 9, 24, 8, 30, tzinfo=UTC),
        metrics={"price_inr": 149},
    )
    validated_request = MerchantResearchRequest.model_validate(research_request)
    result = ResearchResponse(
        mode=AnalysisMode.LIVE_EVIDENCE,
        plan=build_research_plan(validated_request),
        evidence=[evidence],
    )
    return CopilotRequest(
        question="What is the latest khakhra price?",
        merchant_context=merchant,
        current_result=result,
    )


async def test_copilot_answers_from_saved_price_and_guides_refresh() -> None:
    response = await CopilotService(Settings(_env_file=None)).answer(make_request())

    assert "₹149" in response.answer
    assert "Refresh Shopping" in response.answer
    assert "24 September 2026" in response.answer
    assert response.suggested_refresh == RefreshSection.SHOPPING
    assert response.model_used == "local-workspace-guide"
    assert len(response.sources) == 1
    assert str(response.sources[0].source_url) == "https://example.com/khakhra"


class SafeCopilotModel:
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[CopilotDraft],
    ) -> tuple[CopilotDraft, str]:
        assert "authoritative local draft" in prompt.lower()
        return (
            response_model(
                answer=(
                    "The saved Shopping evidence lists the same product at ₹149. "
                    "This is a listed benchmark, not a confirmed local selling price."
                ),
                source_ids=[],
            ),
            "test-copilot-model",
        )


async def test_copilot_uses_ai_wording_but_server_adds_refresh_guidance() -> None:
    response = await CopilotService(
        Settings(_env_file=None),
        llm=SafeCopilotModel(),  # type: ignore[arg-type]
    ).answer(make_request())

    assert response.model_used == "test-copilot-model"
    assert "Refresh Shopping" in response.answer
    assert len(response.sources) == 1


class UnsafeCopilotModel:
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[CopilotDraft],
    ) -> tuple[CopilotDraft, str]:
        return (
            response_model(
                answer="The ₹149 listing proves demand and guarantees this market will succeed.",
                source_ids=[],
            ),
            "unsafe-model",
        )


async def test_copilot_rejects_unsafe_market_success_claims() -> None:
    response = await CopilotService(
        Settings(_env_file=None),
        llm=UnsafeCopilotModel(),  # type: ignore[arg-type]
    ).answer(make_request())

    assert response.model_used == "local-workspace-guide"
    assert "guarantees" not in response.answer
    assert "listed prices" in response.answer
    assert response.warnings


async def test_copilot_greeting_works_without_research_or_ai() -> None:
    request = CopilotRequest(
        question="Hi",
        merchant_context=CopilotMerchantContext(product_name="khakhra"),
    )

    response = await CopilotService(Settings(_env_file=None)).answer(request)

    assert "Hello" in response.answer
    assert "MarketSarthi Copilot" in response.answer
    assert response.warnings == []


async def test_copilot_remembers_preferred_name_without_using_ai() -> None:
    introduction = CopilotRequest(
        question="My name is vishv",
        merchant_context=CopilotMerchantContext(product_name="handmade soap"),
    )
    introduction_response = await CopilotService(Settings(_env_file=None)).answer(introduction)

    assert introduction_response.preferred_name == "Vishv"
    assert "remember your name" in introduction_response.answer

    recall = CopilotRequest(
        question="What is my name?",
        merchant_context=CopilotMerchantContext(
            preferred_name=introduction_response.preferred_name,
            product_name="handmade soap",
        ),
    )
    recall_response = await CopilotService(Settings(_env_file=None)).answer(recall)

    assert recall_response.answer == "Your name is Vishv."
    assert recall_response.preferred_name == "Vishv"
    assert recall_response.warnings == []


class LeakyEvidenceIdModel:
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[CopilotDraft],
    ) -> tuple[CopilotDraft, str]:
        return (
            response_model(
                answer=(
                    "The saved listing price is ₹149.\n\n"
                    "Evidence IDs: 2a15f7a9-f206-490c-a798-39c39e9f32aa"
                ),
                source_ids=[],
            ),
            "leaky-test-model",
        )


async def test_copilot_removes_internal_evidence_ids_from_answer() -> None:
    response = await CopilotService(
        Settings(_env_file=None),
        llm=LeakyEvidenceIdModel(),  # type: ignore[arg-type]
    ).answer(make_request())

    assert response.answer.startswith("The saved listing price is ₹149.")
    assert "Evidence ID" not in response.answer
    assert "2a15f7a9" not in response.answer


async def test_copilot_compares_all_researched_cities() -> None:
    request = make_request()
    request.question = "Compare Bengaluru and Hyderabad."
    request.merchant_context.target_cities = ["Bengaluru", "Hyderabad"]
    assert request.current_result is not None
    request.current_result.city_summaries = [
        CityEvidenceSummary(
            city="Bengaluru",
            direct_competitors=10,
            local_channels=20,
            evidence_coverage_percent=83,
        ),
        CityEvidenceSummary(
            city="Hyderabad",
            direct_competitors=8,
            local_channels=14,
            evidence_coverage_percent=67,
        ),
    ]

    response = await CopilotService(Settings(_env_file=None)).answer(request)

    assert "Bengaluru: 10 same-product listings" in response.answer
    assert "Hyderabad: 8 same-product listings" in response.answer
    assert "not demand" in response.answer


def test_copilot_endpoint_handles_greeting_without_live_research() -> None:
    response = client.post(
        "/api/v1/research/copilot",
        json={
            "question": "Hello",
            "merchant_context": {"product_name": "khakhra"},
        },
    )

    assert response.status_code == 200
    assert "MarketSarthi Copilot" in response.json()["answer"]
    assert response.json()["sources"] == []
