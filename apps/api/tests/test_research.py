from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.schemas.research import (
    AnalysisMode,
    CompetitorType,
    DecisionSummaryContent,
    MerchantResearchRequest,
    RefreshSection,
    ResearchBriefContent,
    Synthesis,
)
from app.services.gemini import GeminiTemporaryError
from app.services.jev import JevShoppingClassification
from app.services.research import (
    ResearchService,
    build_fallback_research_brief,
    build_maps_query_ladder,
    build_research_plan,
    classify_shopping_result,
    deduplicate_warnings,
    extract_pack_metrics,
)

client = TestClient(app)


SAMPLE_REQUEST = {
    "product_name": "Roasted methi khakhra",
    "category": "Packaged healthy snacks",
    "current_city": "Bolpur, West Bengal",
    "target_cities": ["Kolkata"],
    "price_min_inr": 120,
    "price_max_inr": 180,
    "pack_size": "200 g",
    "differentiators": ["low oil", "roasted", "travel friendly"],
    "constraints": ["small production capacity"],
    "business_background": (
        "This is my father's family-run khakhra business in Bolpur. "
        "I want to help him expand carefully."
    ),
    "expansion_goal": "Test Kolkata without risking a large upfront investment.",
}


def test_plan_contains_product_first_query_ladder_and_maps_channel_search() -> None:
    request = MerchantResearchRequest.model_validate(SAMPLE_REQUEST)
    plan = build_research_plan(request)
    assert len(plan.queries) == 30
    assert {query.engine for query in plan.queries} == {
        "google_shopping",
        "google_maps",
        "google_trends",
        "google",
        "google_news",
    }
    shopping = [query for query in plan.queries if query.engine == "google_shopping"]
    assert [query.fallback_rank for query in shopping] == [1, 2, 3, 4, 5]
    assert shopping[0].query == "Roasted methi khakhra 200 g"
    assert shopping[-1].query == "khakra"
    maps = [query for query in plan.queries if query.engine == "google_maps"]
    assert [query.query for query in maps] == [
        "khakhra shop",
        "khakhra store",
        "Gujarati snacks shop",
        "namkeen shop",
        "farsan shop",
    ]
    assert all(query.provider == "SerpApi" for query in plan.queries)
    assert len([query for query in plan.queries if query.engine == "google_trends"]) == 2
    web_queries = [query for query in plan.queries if query.engine == "google"]
    assert [query.city for query in web_queries] == ["Kolkata"] * 6
    assert [query.query for query in web_queries] == [
        "Roasted methi khakhra",
        "where to buy khakhra",
        "khakhra sellers distributor wholesale",
        "khakhra brands price",
        "upcoming Packaged healthy snacks exhibition trade fair",
        "Packaged healthy snacks association government scheme MSME",
    ]
    news_queries = [query for query in plan.queries if query.engine == "google_news"]
    assert [query.query for query in news_queries] == [
        "Roasted methi khakhra Kolkata",
        "khakhra Kolkata",
        "Packaged healthy snacks Kolkata",
        "khakhra India",
        "Packaged healthy snacks India",
        "upcoming Packaged healthy snacks festival event Kolkata",
        "upcoming Packaged healthy snacks exhibition trade fair expo Kolkata",
        "Packaged healthy snacks retailer supermarket expansion Kolkata",
        "Packaged healthy snacks distributor wholesale expansion Kolkata",
        "Packaged healthy snacks new product launch brand expansion India",
        "Packaged healthy snacks regulation FSSAI government scheme MSME India",
        "Packaged healthy snacks raw material price supply consumer trend India",
    ]
    assert len(web_queries) + len(news_queries) == 18
    assert all("when:12m" not in query.query for query in news_queries)
    assert all(query.research_question for query in plan.queries)


def test_generic_maps_ladder_uses_product_and_category_without_food_assumptions() -> None:
    request = MerchantResearchRequest.model_validate(
        {
            **SAMPLE_REQUEST,
            "product_name": "Handmade neem soap",
            "category": "Natural personal care",
        }
    )

    queries = build_maps_query_ladder(request)

    assert queries == [
        "soap shop",
        "soap store",
        "Natural personal care",
        "Natural personal care store",
    ]
    assert "namkeen shop" not in queries


def test_preview_is_free_plan_only_mode() -> None:
    response = client.post("/api/v1/research/preview", json=SAMPLE_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "plan_only"
    assert body["evidence"] == []
    assert "consumes no credits" in body["warnings"][0]


def test_invalid_price_range_is_rejected() -> None:
    invalid = {**SAMPLE_REQUEST, "price_min_inr": 200, "price_max_inr": 100}
    response = client.post("/api/v1/research/preview", json=invalid)
    assert response.status_code == 422


def test_duplicate_provider_warnings_are_collapsed_in_display_order() -> None:
    warnings = deduplicate_warnings(
        [
            "SerpApi Google Search failed for Bengaluru: ReadTimeout",
            "SerpApi Google Search failed for Bengaluru: ReadTimeout",
            "SerpApi Google Search failed for Hyderabad: ReadTimeout",
            "SerpApi Google Search failed for Bengaluru: ReadTimeout",
        ]
    )

    assert warnings == [
        "SerpApi Google Search failed for Bengaluru: ReadTimeout",
        "SerpApi Google Search failed for Hyderabad: ReadTimeout",
    ]


class FakeSerpApi:
    def __init__(self) -> None:
        self.news_calls: list[str] = []
        self.shopping_calls = 0
        self.shopping_bypass_states: list[bool] = []
        self.bypass_cache = False

    async def shopping(self, query: str, city: str | None = None) -> dict[str, object]:
        self.shopping_calls += 1
        self.shopping_bypass_states.append(self.bypass_cache)
        return {
            "shopping_results": [
                {
                    "position": 1,
                    "title": "Roasted methi khakhra 200g",
                    "source": "Example merchant",
                    "extracted_price": 149,
                    "rating": 4.4,
                    "reviews": 82,
                    "product_link": f"https://example.com/khakhra?check={self.shopping_calls}",
                }
            ]
        }

    async def maps(self, query: str, city: str) -> dict[str, object]:
        return {
            "local_results": [
                {
                    "title": "Healthy Snack Store",
                    "type": "Health food store",
                    "rating": 4.2,
                    "reviews": 51,
                    "address": f"Central {city}",
                    "data_id": "example-data-id",
                    "link": "https://maps.example.com/store",
                }
            ]
        }

    async def maps_reviews(
        self,
        data_id: str,
        query: str | None = None,
        sort_by: str = "qualityScore",
    ) -> dict[str, object]:
        assert data_id == "example-data-id"
        assert query == "khakhra"
        return {"reviews": [{"snippet": "Good khakhra selection"}]}

    async def web(self, query: str, city: str) -> dict[str, object]:
        return {
            "organic_results": [
                {
                    "position": 1,
                    "title": f"Khakhra sellers in {city}",
                    "link": "https://example.com/kolkata-khakhra",
                    "displayed_link": "example.com",
                    "snippet": f"A guide to khakhra sellers and snack shops in {city}.",
                }
            ]
        }

    async def trends(self, query: str, geo: str = "IN") -> dict[str, object]:
        assert query == "khakhra"
        assert geo == "IN"
        return {
            "interest_over_time": {
                "timeline_data": [
                    {
                        "date": "January 2026",
                        "values": [{"query": query, "extracted_value": 30}],
                    },
                    {
                        "date": "April 2026",
                        "values": [{"query": query, "extracted_value": 40}],
                    },
                    {
                        "date": "July 2026",
                        "values": [{"query": query, "extracted_value": 55}],
                    },
                    {
                        "date": "September 2026",
                        "values": [{"query": query, "extracted_value": 65}],
                    },
                ]
            }
        }

    async def trends_by_region(
        self,
        query: str,
        geo: str = "IN",
        region: str = "CITY",
    ) -> dict[str, object]:
        assert query == "khakhra"
        assert geo == "IN"
        assert region == "CITY"
        return {
            "interest_by_region": [
                {"location": "Ahmedabad", "extracted_value": 100},
                {"location": "Kolkata", "extracted_value": 34},
            ]
        }

    async def news(self, query: str) -> dict[str, object]:
        self.news_calls.append(query)
        call_number = len(self.news_calls)
        return {
            "news_results": [
                {
                    "position": index,
                    "title": f"Kolkata snack market report {call_number}-{index}",
                    "link": f"https://news.example.com/kolkata-snacks-{call_number}-{index}",
                    "source": {"name": "Example Business News"},
                    "snippet": "Kolkata snack sellers discuss recent category changes.",
                    "iso_date": "2026-09-01T09:00:00Z",
                }
                for index in range(1, 3)
            ]
        }


class FakeGemini:
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[ResearchBriefContent],
    ) -> tuple[ResearchBriefContent, str]:
        assert "father's family-run" in prompt
        return (
            response_model(
                research_brief=(
                    "Investigate a low-risk Kolkata expansion for the family-run khakhra "
                    "business using separate direct and alternative competitor evidence."
                ),
                business_facts=["The business currently operates in Bolpur."],
                merchant_goals=["Help the family business expand carefully."],
                constraints=["Small production capacity."],
                assumptions=[],
                open_questions=["What shelf life can the product support?"],
            ),
            "gemini-3.8-flash",
        )

    async def synthesize(self, prompt: str) -> Synthesis:
        assert "Roasted methi khakhra" in prompt
        assert "Evidence ledger" in prompt
        assert "business_review" in prompt
        assert "Good khakhra selection" in prompt
        return Synthesis(
            headline="Kolkata warrants a bounded pilot",
            recommendation="Test demand before committing to city-wide distribution.",
            product_changes=["Validate pack size against comparable listings."],
            risks=["Public search evidence does not measure offline sales."],
            next_experiments=["Run a 50-customer pilot."],
            confidence="low",
        )


class FakeJev:
    async def classify_shopping(
        self,
        request: MerchantResearchRequest,
        evidence: list,
    ) -> list[JevShoppingClassification]:
        assert request.product_name == "Roasted methi khakhra"
        shopping = [item for item in evidence if item.evidence_type == "shopping"]
        return [
            JevShoppingClassification(
                evidence_id=item.id,
                competitor_type=CompetitorType.ALTERNATIVE,
                confidence=0.92,
            )
            for item in shopping
        ]


async def test_jev_classifies_shopping_without_replacing_other_services() -> None:
    settings = Settings(
        serpapi_key="test-serp-key",
        typesafe_api_key="test-typesafe-key",
        _env_file=None,
    )
    service = ResearchService(
        settings,
        serpapi=FakeSerpApi(),  # type: ignore[arg-type]
        jev=FakeJev(),  # type: ignore[arg-type]
    )

    response = await service.analyze(
        MerchantResearchRequest.model_validate(SAMPLE_REQUEST),
        include_synthesis=False,
    )

    shopping = [item for item in response.evidence if item.evidence_type == "shopping"]
    assert shopping
    assert all(item.competitor_type == CompetitorType.ALTERNATIVE for item in shopping)
    assert all(item.classification_source == "TypeSafe Jev" for item in shopping)
    assert all(item.classification_confidence == 0.92 for item in shopping)
    assert response.classification_model_used == "jev-latest"
    assert response.classification_items_applied == len(shopping)
    assert response.classification_items_skipped == 0

async def test_live_vertical_slice_normalizes_and_preserves_evidence() -> None:
    settings = Settings(
        serpapi_key="test-serp-key",
        gemini_api_key="test-gemini-key",
        _env_file=None,
    )
    serpapi = FakeSerpApi()
    service = ResearchService(
        settings,
        serpapi=serpapi,  # type: ignore[arg-type]
        gemini=FakeGemini(),  # type: ignore[arg-type]
    )

    response = await service.analyze(MerchantResearchRequest.model_validate(SAMPLE_REQUEST))

    assert response.mode == AnalysisMode.LIVE_WITH_SYNTHESIS
    assert len(response.evidence) == 18
    assert all(item.retrieved_at.tzinfo is not None for item in response.evidence)
    assert response.city_summaries[0].observed_price_median == 149
    assert response.city_summaries[0].local_channels == 1
    assert response.city_summaries[0].direct_competitors == 1
    assert response.city_summaries[0].verified_local_channels == 1
    assert response.city_summaries[0].city_specific_web_results == 1
    assert response.city_summaries[0].city_specific_news_results == 12
    assert response.city_summaries[0].trend_interest_score == 34
    assert response.city_summaries[0].evidence_dimensions_met == 4
    assert response.city_summaries[0].evidence_dimensions_total == 6
    assert response.city_summaries[0].evidence_coverage_percent == 67
    assert response.city_summaries[0].coverage_level == "developing"
    assert response.city_summaries[0].price_band_signal == "overlaps_observed"
    assert response.city_summaries[0].evidence_gaps == [
        "We found fewer than three prices for the same kind of product.",
        "We found fewer than five nearby shops to check.",
    ]
    assert {run.engine for run in response.tool_runs} == {
        "google_shopping",
        "google_maps",
        "google_maps_reviews",
        "google_trends",
        "google",
        "google_news",
    }
    assert all(run.research_question for run in response.tool_runs)
    local_channel = next(
        item for item in response.evidence if item.evidence_type == "local_channel"
    )
    assert local_channel.channel_status == "verified_product_mention"
    assert local_channel.metrics["matching_review_count"] == 1
    assert local_channel.evidence_scope == "city_local"
    shopping_item = next(
        item for item in response.evidence if item.evidence_type == "shopping"
    )
    assert shopping_item.evidence_scope == "city_local"
    review_item = next(
        item for item in response.evidence if item.evidence_type == "review"
    )
    assert review_item.evidence_scope == "business_review"
    assert review_item.metrics["themes"] == ["availability_and_variety"]
    assert "Good khakhra selection" in review_item.observation
    trend_items = [item for item in response.evidence if item.evidence_type == "trend"]
    assert len(trend_items) == 2
    assert trend_items[0].evidence_scope == "india_wide_online"
    assert any("Kolkata: 34/100" in item.observation for item in trend_items)
    web_item = next(item for item in response.evidence if item.evidence_type == "web")
    assert web_item.evidence_scope == "city_local"
    assert "Kolkata" in web_item.observation
    news_item = next(item for item in response.evidence if item.evidence_type == "news")
    assert news_item.evidence_scope == "city_local"
    assert news_item.source_name == "Example Business News"
    assert "2026-09-01" in news_item.observation
    assert len([item for item in response.evidence if item.evidence_type == "news"]) == 12
    assert len([run for run in response.tool_runs if run.engine == "google_news"]) == 6
    assert response.synthesis is not None
    assert response.synthesis.confidence == "low"


async def test_targeted_refresh_replaces_only_selected_evidence() -> None:
    settings = Settings(
        serpapi_key="test-serp-key",
        gemini_api_key="test-gemini-key",
        _env_file=None,
    )
    serpapi = FakeSerpApi()
    service = ResearchService(
        settings,
        serpapi=serpapi,  # type: ignore[arg-type]
        gemini=FakeGemini(),  # type: ignore[arg-type]
    )
    request = MerchantResearchRequest.model_validate(SAMPLE_REQUEST)
    original = await service.analyze(request)
    original_nonshopping = {
        item.id for item in original.evidence if item.engine != "google_shopping"
    }
    original_shopping = {
        item.id for item in original.evidence if item.engine == "google_shopping"
    }

    refreshed = await service.refresh_sections(
        request,
        original,
        [RefreshSection.SHOPPING],
    )

    assert refreshed.mode == AnalysisMode.LIVE_EVIDENCE
    assert refreshed.synthesis is None
    assert refreshed.decision_summary is None
    assert original_nonshopping.issubset({item.id for item in refreshed.evidence})
    assert original_shopping.isdisjoint({item.id for item in refreshed.evidence})
    assert serpapi.shopping_bypass_states[-1] is True
    assert {run.engine for run in refreshed.tool_runs} == {
        "google_shopping",
        "google_maps",
        "google_maps_reviews",
        "google_trends",
        "google",
        "google_news",
    }
    assert any("Refreshed only: shopping" in warning for warning in refreshed.warnings)


class DecisionSummaryModel:
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[DecisionSummaryContent],
    ) -> tuple[DecisionSummaryContent, str]:
        assert "authoritative" in prompt.lower()
        return (
            response_model(
                observed=["Invented observation that must be ignored."],
                unknowns=["Invented gap that must be ignored."],
                next_actions=["Call three shortlisted shops, then run a 20-packet test."],
                do_not_conclude=["Invented warning that must be ignored."],
            ),
            "test-decision-model",
        )


async def test_decision_summary_keeps_deterministic_facts_and_ai_next_actions() -> None:
    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    request = MerchantResearchRequest.model_validate(SAMPLE_REQUEST)
    evidence_service = ResearchService(
        settings,
        serpapi=FakeSerpApi(),  # type: ignore[arg-type]
        gemini=FakeGemini(),  # type: ignore[arg-type]
    )
    research = await evidence_service.analyze(request)
    summary_service = ResearchService(
        settings,
        serpapi=FakeSerpApi(),  # type: ignore[arg-type]
        llm=DecisionSummaryModel(),  # type: ignore[arg-type]
    )

    response = await summary_service.update_decision_summary(request, research)

    assert response.model_used == "test-decision-model"
    assert "Kolkata" in response.summary.observed[0]
    assert "Invented observation" not in " ".join(response.summary.observed)
    assert response.summary.next_actions == [
        "Call three shortlisted shops, then run a 20-packet test."
    ]
    assert all(
        "proof" in item.lower()
        or "conclude" in item.lower()
        or "commitment" in item.lower()
        for item in response.summary.do_not_conclude
    )


class QuotaExhaustedGemini:
    async def synthesize(self, prompt: str) -> Synthesis:
        raise GeminiTemporaryError("HTTP 429 quota exceeded")


async def test_city_scorecard_survives_gemini_quota_exhaustion() -> None:
    settings = Settings(
        serpapi_key="test-serp-key",
        gemini_api_key="test-gemini-key",
        _env_file=None,
    )
    service = ResearchService(
        settings,
        serpapi=FakeSerpApi(),  # type: ignore[arg-type]
        gemini=QuotaExhaustedGemini(),  # type: ignore[arg-type]
    )

    response = await service.analyze(MerchantResearchRequest.model_validate(SAMPLE_REQUEST))

    assert response.mode == AnalysisMode.LIVE_EVIDENCE
    assert response.synthesis is None
    assert response.city_summaries[0].coverage_level == "developing"
    assert response.city_summaries[0].verified_local_channels == 1
    assert "HTTP 429 quota exceeded" in response.warnings[0]


async def test_research_brief_preserves_merchant_background() -> None:
    settings = Settings(gemini_api_key="test-gemini-key", _env_file=None)
    service = ResearchService(settings, gemini=FakeGemini())  # type: ignore[arg-type]

    response = await service.generate_brief(
        MerchantResearchRequest.model_validate(SAMPLE_REQUEST)
    )

    assert response.model_used == "gemini-3.8-flash"
    assert "family-run" in response.brief.research_brief
    assert response.brief.assumptions == []


def test_local_brief_template_uses_only_merchant_facts() -> None:
    request = MerchantResearchRequest.model_validate(SAMPLE_REQUEST)

    brief = build_fallback_research_brief(request)

    assert "Roasted methi khakhra" in brief.research_brief
    assert "Bolpur" in brief.research_brief
    assert "Kolkata" in brief.research_brief
    assert "₹120–₹180" in brief.research_brief
    assert brief.assumptions == []
    assert len(brief.open_questions) == 3


class UnavailableGemini:
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[ResearchBriefContent],
    ) -> tuple[ResearchBriefContent, str]:
        raise GeminiTemporaryError("HTTP 503 high demand")


async def test_research_brief_falls_back_when_gemini_is_busy() -> None:
    settings = Settings(gemini_api_key="test-gemini-key", _env_file=None)
    service = ResearchService(
        settings,
        gemini=UnavailableGemini(),  # type: ignore[arg-type]
    )

    response = await service.generate_brief(
        MerchantResearchRequest.model_validate(SAMPLE_REQUEST)
    )

    assert response.model_used == "local-template"
    assert "editable local draft" in response.warnings[0]
    assert "Roasted methi khakhra" in response.brief.research_brief


def test_direct_and_alternative_competitors_are_separated() -> None:
    request = MerchantResearchRequest.model_validate(SAMPLE_REQUEST)

    direct, _ = classify_shopping_result("Methi Khakra 200 g", request)
    alternative, _ = classify_shopping_result("High protein healthy biscuits", request)

    assert direct == CompetitorType.DIRECT
    assert alternative == CompetitorType.ALTERNATIVE


def test_multipack_price_is_normalized() -> None:
    metrics = extract_pack_metrics("Methi khakhra 170g (Pack of 3)", 459)

    assert metrics["pack_count"] == 3
    assert metrics["grams_per_pack"] == 170
    assert metrics["price_per_pack_inr"] == 153
    assert metrics["price_per_100g_inr"] == 90


class FakeFallbackSerpApi:
    def __init__(self) -> None:
        self.shopping_calls: list[tuple[str, str | None]] = []

    async def shopping(self, query: str, city: str | None = None) -> dict[str, object]:
        self.shopping_calls.append((query, city))
        if len(self.shopping_calls) == 1:
            return {"shopping_results": []}
        return {
            "shopping_results": [
                {
                    "product_id": f"khakhra-{index}",
                    "title": f"Methi khakhra 200g variant {index}",
                    "source": "Example merchant",
                    "extracted_price": 120 + index,
                }
                for index in range(6)
            ]
        }

    async def maps(self, query: str, city: str) -> dict[str, object]:
        return {"local_results": []}

    async def web(self, query: str, city: str) -> dict[str, object]:
        return {"organic_results": []}

    async def trends(self, query: str, geo: str = "IN") -> dict[str, object]:
        return {"interest_over_time": {"timeline_data": []}}

    async def trends_by_region(
        self,
        query: str,
        geo: str = "IN",
        region: str = "CITY",
    ) -> dict[str, object]:
        return {"interest_by_region": []}

    async def news(self, query: str) -> dict[str, object]:
        return {"news_results": []}


async def test_shopping_falls_back_from_city_query_to_broader_product_query() -> None:
    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    serpapi = FakeFallbackSerpApi()
    service = ResearchService(settings, serpapi=serpapi)  # type: ignore[arg-type]

    response = await service.analyze(MerchantResearchRequest.model_validate(SAMPLE_REQUEST))

    assert serpapi.shopping_calls[0] == ("Roasted methi khakhra 200 g", "Kolkata")
    assert serpapi.shopping_calls[1] == ("Roasted methi khakhra", None)
    assert len(response.evidence) == 6
    assert {
        item.evidence_scope for item in response.evidence
    } == {"india_wide_online"}
    shopping_runs = [run for run in response.tool_runs if run.engine == "google_shopping"]
    assert [run.status for run in shopping_runs] == ["no_results", "success"]
