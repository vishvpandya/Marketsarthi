from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class EvidenceType(StrEnum):
    SHOPPING = "shopping"
    LOCAL_COMPETITOR = "local_competitor"
    LOCAL_CHANNEL = "local_channel"
    REVIEW = "review"
    TREND = "trend"
    WEB = "web"
    NEWS = "news"


class EvidenceScope(StrEnum):
    CITY_LOCAL = "city_local"
    INDIA_WIDE_ONLINE = "india_wide_online"
    BUSINESS_REVIEW = "business_review"


class AnalysisMode(StrEnum):
    PLAN_ONLY = "plan_only"
    LIVE_EVIDENCE = "live_evidence"
    LIVE_WITH_SYNTHESIS = "live_with_synthesis"


class CompetitorType(StrEnum):
    DIRECT = "direct"
    ALTERNATIVE = "alternative"
    UNCERTAIN = "uncertain"


class LocalChannelStatus(StrEnum):
    POTENTIAL = "potential"
    VERIFIED_PRODUCT_MENTION = "verified_product_mention"


class EvidenceCoverageLevel(StrEnum):
    LIMITED = "limited"
    DEVELOPING = "developing"
    PILOT_READY = "pilot_ready"


class PriceBandSignal(StrEnum):
    BELOW_OBSERVED = "below_observed"
    OVERLAPS_OBSERVED = "overlaps_observed"
    ABOVE_OBSERVED = "above_observed"
    UNKNOWN = "unknown"


class ToolRunStatus(StrEnum):
    SUCCESS = "success"
    NO_RESULTS = "no_results"
    FAILED = "failed"


class RefreshSection(StrEnum):
    SHOPPING = "shopping"
    MAPS_REVIEWS = "maps_reviews"
    TRENDS = "trends"
    WEB_SEARCH = "web_search"
    NEWS = "news"


class CopilotRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class PilotOutcome(StrEnum):
    CONTINUE_SMALL_TEST = "continue_small_test"
    MODIFY_AND_RETEST = "modify_and_retest"
    INVESTIGATE_BEFORE_NEXT_TEST = "investigate_before_next_test"
    STOP_AND_REVIEW = "stop_and_review"


class MerchantResearchRequest(BaseModel):
    product_name: str = Field(min_length=2, max_length=120, examples=["Roasted methi khakhra"])
    category: str = Field(min_length=2, max_length=100, examples=["Packaged healthy snacks"])
    current_city: str = Field(min_length=2, max_length=100, examples=["Bolpur, West Bengal"])
    target_cities: list[str] = Field(min_length=1, max_length=5, examples=[["Kolkata"]])
    price_min_inr: int = Field(ge=1, le=100_000, examples=[120])
    price_max_inr: int = Field(ge=1, le=100_000, examples=[180])
    pack_size: str | None = Field(default=None, max_length=80, examples=["200 g"])
    differentiators: list[str] = Field(default_factory=list, max_length=8)
    constraints: list[str] = Field(default_factory=list, max_length=8)
    business_background: str | None = Field(default=None, max_length=2_000)
    expansion_goal: str | None = Field(default=None, max_length=1_000)
    research_brief: str | None = Field(default=None, max_length=5_000)
    language: str = Field(default="English", max_length=40)

    @field_validator("product_name", "category", "current_city")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("target_cities")
    @classmethod
    def normalize_target_cities(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(" ".join(value.split()) for value in values if value.strip()))
        if not normalized:
            raise ValueError("at least one target city is required")
        return normalized

    @model_validator(mode="after")
    def validate_price_range(self) -> "MerchantResearchRequest":
        if self.price_min_inr > self.price_max_inr:
            raise ValueError("price_min_inr cannot exceed price_max_inr")
        return self


class PlannedQuery(BaseModel):
    provider: str = "SerpApi"
    research_question: str
    tool: str
    engine: str
    stage: str
    city: str
    query: str
    purpose: str
    fallback_rank: int | None = None


class ToolRun(BaseModel):
    provider: str = "SerpApi"
    research_question: str
    engine: str
    tool: str
    stage: str
    city: str
    scope: str
    query: str
    status: ToolRunStatus
    result_count: int = 0
    cache_hit: bool = False
    note: str | None = None


class ResearchPlan(BaseModel):
    product_summary: str
    approved_brief: str | None = None
    queries: list[PlannedQuery]
    limitations: list[str]


class ResearchBriefContent(BaseModel):
    research_brief: str = Field(min_length=40, max_length=5_000)
    business_facts: list[str] = Field(default_factory=list, max_length=8)
    merchant_goals: list[str] = Field(default_factory=list, max_length=6)
    constraints: list[str] = Field(default_factory=list, max_length=8)
    assumptions: list[str] = Field(default_factory=list, max_length=6)
    open_questions: list[str] = Field(default_factory=list, max_length=6)


class ResearchBriefResponse(BaseModel):
    brief: ResearchBriefContent
    model_used: str
    warnings: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    evidence_type: EvidenceType
    city: str
    title: str
    observation: str
    source_name: str
    source_url: HttpUrl | None = None
    provider: str = "SerpApi"
    engine: str | None = None
    evidence_scope: EvidenceScope
    competitor_type: CompetitorType | None = None
    channel_status: LocalChannelStatus | None = None
    classification_reason: str | None = None
    classification_source: str | None = None
    classification_confidence: float | None = Field(default=None, ge=0, le=1)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metrics: dict[str, Any] = Field(default_factory=dict)


class CityEvidenceSummary(BaseModel):
    city: str
    shopping_results: int = 0
    local_competitors: int = 0
    local_channels: int = 0
    direct_competitors: int = 0
    alternative_competitors: int = 0
    uncertain_competitors: int = 0
    observed_price_min: float | None = None
    observed_price_median: float | None = None
    observed_price_max: float | None = None
    direct_price_per_100g_median: float | None = None
    verified_local_channels: int = 0
    city_specific_web_results: int = 0
    city_specific_news_results: int = 0
    trend_interest_score: float | None = None
    evidence_dimensions_met: int = 0
    evidence_dimensions_total: int = 6
    evidence_coverage_percent: int = 0
    coverage_level: EvidenceCoverageLevel = EvidenceCoverageLevel.LIMITED
    price_band_signal: PriceBandSignal = PriceBandSignal.UNKNOWN
    evidence_gaps: list[str] = Field(default_factory=list)
    next_action: str = "Collect more market evidence before choosing a pilot."


class CompetitorClassification(BaseModel):
    evidence_id: UUID
    competitor_type: CompetitorType
    reason: str = Field(min_length=5, max_length=300)


class Synthesis(BaseModel):
    headline: str
    recommendation: str
    product_changes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_experiments: list[str] = Field(default_factory=list)
    confidence: str = "insufficient_evidence"
    competitor_classifications: list[CompetitorClassification] = Field(default_factory=list)


class DecisionSummaryContent(BaseModel):
    observed: list[str] = Field(min_length=1, max_length=6)
    unknowns: list[str] = Field(min_length=1, max_length=6)
    next_actions: list[str] = Field(min_length=1, max_length=6)
    do_not_conclude: list[str] = Field(min_length=1, max_length=5)


class ResearchResponse(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    mode: AnalysisMode
    plan: ResearchPlan
    tool_runs: list[ToolRun] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    city_summaries: list[CityEvidenceSummary] = Field(default_factory=list)
    synthesis: Synthesis | None = None
    decision_summary: DecisionSummaryContent | None = None
    decision_model_used: str | None = None
    decision_warnings: list[str] = Field(default_factory=list)
    classification_model_used: str | None = None
    classification_items_applied: int = 0
    classification_items_skipped: int = 0
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResearchRefreshRequest(BaseModel):
    request: MerchantResearchRequest
    current_result: ResearchResponse
    sections: list[RefreshSection] = Field(min_length=1, max_length=5)

    @field_validator("sections")
    @classmethod
    def unique_sections(cls, values: list[RefreshSection]) -> list[RefreshSection]:
        return list(dict.fromkeys(values))


class DecisionSummaryRequest(BaseModel):
    request: MerchantResearchRequest
    current_result: ResearchResponse


class DecisionSummaryResponse(BaseModel):
    summary: DecisionSummaryContent
    model_used: str
    warnings: list[str] = Field(default_factory=list)


class CopilotMerchantContext(BaseModel):
    preferred_name: str | None = Field(default=None, max_length=60)
    product_name: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=100)
    current_city: str | None = Field(default=None, max_length=100)
    target_cities: list[str] = Field(default_factory=list, max_length=5)
    price_min_inr: float | None = Field(default=None, ge=0, le=1_000_000_000)
    price_max_inr: float | None = Field(default=None, ge=0, le=1_000_000_000)
    pack_size: str | None = Field(default=None, max_length=80)
    business_background: str | None = Field(default=None, max_length=2_000)
    expansion_goal: str | None = Field(default=None, max_length=1_000)


class CopilotPilotContext(BaseModel):
    city: str | None = Field(default=None, max_length=100)
    selected_shops: int = Field(default=0, ge=0, le=10_000)
    confirmed_shops: int = Field(default=0, ge=0, le=10_000)
    has_completed_review: bool = False
    saved_rounds: int = Field(default=0, ge=0, le=100)


class CopilotHistoryMessage(BaseModel):
    role: CopilotRole
    content: str = Field(min_length=1, max_length=2_000)


class CopilotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1_000)
    merchant_context: CopilotMerchantContext = Field(default_factory=CopilotMerchantContext)
    current_result: ResearchResponse | None = None
    pilot_context: CopilotPilotContext = Field(default_factory=CopilotPilotContext)
    history: list[CopilotHistoryMessage] = Field(default_factory=list, max_length=8)
    research_details_changed: bool = False

    @field_validator("question")
    @classmethod
    def trim_question(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("question must not be blank")
        return value


class CopilotDraft(BaseModel):
    answer: str = Field(min_length=10, max_length=2_500)
    source_ids: list[UUID] = Field(default_factory=list, max_length=5)


class CopilotSource(BaseModel):
    evidence_id: UUID
    title: str
    source_url: HttpUrl
    source_name: str
    engine: str | None = None
    city: str
    checked_at: datetime


class CopilotResponse(BaseModel):
    answer: str
    preferred_name: str | None = None
    sources: list[CopilotSource] = Field(default_factory=list, max_length=5)
    suggested_refresh: RefreshSection | None = None
    refresh_instruction: str | None = None
    model_used: str
    warnings: list[str] = Field(default_factory=list)


class ShopPilotMeasurement(BaseModel):
    shop_name: str = Field(min_length=1, max_length=200)
    packets_given: int = Field(ge=1, le=1_000_000)
    packets_bought: int = Field(ge=0, le=1_000_000)
    packets_returned: int = Field(ge=0, le=1_000_000)
    packets_damaged: int = Field(default=0, ge=0, le=1_000_000)
    packets_missing: int = Field(default=0, ge=0, le=1_000_000)
    packets_still_at_shop: int = Field(default=0, ge=0, le=1_000_000)
    wants_another_batch: bool | None = None
    notes: str | None = Field(default=None, max_length=1_000)

    @model_validator(mode="after")
    def validate_packet_accounting(self) -> "ShopPilotMeasurement":
        accounted_packets = (
            self.packets_bought
            + self.packets_returned
            + self.packets_damaged
            + self.packets_missing
            + self.packets_still_at_shop
        )
        if accounted_packets != self.packets_given:
            raise ValueError(
                "bought, returned, damaged, missing, and still-at-shop packets "
                "must add up to packets_given"
            )
        return self


class PilotReviewRequest(BaseModel):
    product_name: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=100)
    planned_packets: int = Field(ge=1, le=1_000_000)
    actual_packets_given: int = Field(ge=1, le=1_000_000)
    packets_bought: int = Field(ge=0, le=1_000_000)
    packets_returned: int = Field(ge=0, le=1_000_000)
    packets_damaged: int = Field(default=0, ge=0, le=1_000_000)
    packets_missing: int = Field(default=0, ge=0, le=1_000_000)
    packets_still_at_shops: int = Field(default=0, ge=0, le=1_000_000)
    target_bought_percent: float = Field(ge=0, le=100)
    maximum_returned_percent: float = Field(ge=0, le=100)
    shops_planned: int = Field(ge=1, le=10_000)
    shops_asking_another_batch: int = Field(ge=0, le=10_000)
    money_received_inr: float | None = Field(default=None, ge=0, le=1_000_000_000)
    nonrecoverable_costs_inr: float | None = Field(default=None, ge=0, le=1_000_000_000)
    maximum_acceptable_loss_inr: float | None = Field(
        default=None, ge=0, le=1_000_000_000
    )
    change_from_previous_round: str | None = Field(default=None, min_length=3, max_length=1_000)
    shop_results: list[ShopPilotMeasurement] = Field(default_factory=list, max_length=20)
    merchant_notes: str | None = Field(default=None, max_length=3_000)
    research_context: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_aggregate_results(self) -> "PilotReviewRequest":
        accounted_packets = (
            self.packets_bought
            + self.packets_returned
            + self.packets_damaged
            + self.packets_missing
            + self.packets_still_at_shops
        )
        if accounted_packets > self.actual_packets_given:
            raise ValueError(
                "bought, returned, damaged, missing, and still-at-shop packets "
                "cannot exceed actual_packets_given"
            )
        if self.shops_asking_another_batch > self.shops_planned:
            raise ValueError("shops_asking_another_batch cannot exceed shops_planned")
        money_values = (
            self.money_received_inr,
            self.nonrecoverable_costs_inr,
            self.maximum_acceptable_loss_inr,
        )
        if any(value is not None for value in money_values) and not all(
            value is not None for value in money_values
        ):
            raise ValueError(
                "money_received_inr, nonrecoverable_costs_inr, and "
                "maximum_acceptable_loss_inr must be supplied together"
            )
        return self


class PilotDecisionFacts(BaseModel):
    outcome: PilotOutcome
    bought_percent: float
    returned_percent: float
    bought_target_met: bool
    returned_limit_met: bool
    merchant_checks_met: bool
    planned_packets: int
    actual_packets_given: int
    packets_bought: int
    packets_returned: int
    packets_damaged: int
    packets_missing: int
    packets_still_at_shops: int
    packets_unaccounted_for: int
    shops_planned: int
    shops_asking_another_batch: int
    money_received_inr: float | None = None
    nonrecoverable_costs_inr: float | None = None
    maximum_acceptable_loss_inr: float | None = None
    net_cash_result_inr: float | None = None
    cash_check_met: bool | None = None
    reasons: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class PilotReviewNarrative(BaseModel):
    summary: str = Field(min_length=20, max_length=1_200)
    what_worked: list[str] = Field(default_factory=list, max_length=5)
    what_needs_attention: list[str] = Field(default_factory=list, max_length=5)
    next_experiment: str = Field(min_length=20, max_length=1_000)
    do_not_conclude: list[str] = Field(min_length=1, max_length=5)


class PilotReviewResponse(BaseModel):
    facts: PilotDecisionFacts
    review: PilotReviewNarrative
    model_used: str
    warnings: list[str] = Field(default_factory=list)
