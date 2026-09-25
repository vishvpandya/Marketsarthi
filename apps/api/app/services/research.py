import asyncio
import json
import re
import statistics
from collections.abc import Iterable
from typing import Any

import httpx

from app.core.config import Settings
from app.schemas.research import (
    AnalysisMode,
    CityEvidenceSummary,
    CompetitorClassification,
    CompetitorType,
    DecisionSummaryContent,
    DecisionSummaryResponse,
    EvidenceCoverageLevel,
    EvidenceItem,
    EvidenceScope,
    EvidenceType,
    LocalChannelStatus,
    MerchantResearchRequest,
    PlannedQuery,
    PriceBandSignal,
    RefreshSection,
    ResearchBriefContent,
    ResearchBriefResponse,
    ResearchPlan,
    ResearchResponse,
    ToolRun,
    ToolRunStatus,
)
from app.services.gemini import GeminiClient
from app.services.jev import JevClassificationError, JevClient, JevShoppingClassification
from app.services.llm import LanguageModelClient
from app.services.llm_types import LanguageModelError, StructuredLanguageModel
from app.services.serpapi import SerpApiClient, SerpApiError, ServiceNotConfiguredError


def deduplicate_warnings(warnings: Iterable[str]) -> list[str]:
    """Keep the first copy of each merchant-facing warning in display order."""
    return list(dict.fromkeys(warning for warning in warnings if warning.strip()))


def build_research_plan(request: MerchantResearchRequest) -> ResearchPlan:
    queries: list[PlannedQuery] = []

    for city in request.target_cities:
        for rank, query in enumerate(build_shopping_query_ladder(request), start=1):
            queries.append(
                PlannedQuery(
                    research_question=(
                        "Which similar products, brands, prices and pack sizes are visible?"
                    ),
                    tool="product_discovery",
                    engine="google_shopping",
                    stage="product_intelligence",
                    city=city,
                    query=query,
                    purpose=(
                        "Find similar products and compare their prices, pack sizes, brands and "
                        "how they are described."
                    ),
                    fallback_rank=rank,
                )
            )
        for rank, query in enumerate(build_maps_query_ladder(request), start=1):
            queries.append(
                PlannedQuery(
                    research_question=(
                        f"Which shops in {city} could already sell or test this product?"
                    ),
                    tool="find_local_channels",
                    engine="google_maps",
                    stage="local_availability",
                    city=city,
                    query=query,
                    purpose=(
                        "Find nearby shops that may suit this product. Do not assume a shop sells "
                        "it until a review or direct call confirms it."
                    ),
                    fallback_rank=rank,
                )
            )
        for rank, (query, question, purpose) in enumerate(
            build_web_query_ladder(request, city),
            start=1,
        ):
            queries.append(
                PlannedQuery(
                    research_question=question,
                    tool="find_web_evidence",
                    engine="google",
                    stage="web_corroboration",
                    city=city,
                    query=query,
                    purpose=purpose,
                    fallback_rank=rank,
                )
            )
        for rank, (query, question, purpose) in enumerate(
            build_news_query_ladder(request, city),
            start=1,
        ):
            queries.append(
                PlannedQuery(
                    research_question=question,
                    tool="find_recent_market_changes",
                    engine="google_news",
                    stage="event_intelligence",
                    city=city,
                    query=query,
                    purpose=purpose,
                    fallback_rank=rank,
                )
            )

    trend_query = product_core_term(request.product_name)
    queries.extend(
        [
            PlannedQuery(
                research_question="How has Google search interest changed over time?",
                tool="measure_search_interest",
                engine="google_trends",
                stage="interest_over_time",
                city="India",
                query=trend_query,
                purpose=(
                    "Show how relative Google search interest changed during the past 12 months. "
                    "This does not measure demand or sales."
                ),
            ),
            PlannedQuery(
                research_question=(
                    "Which Indian cities appear in the returned search-interest data?"
                ),
                tool="compare_city_interest",
                engine="google_trends",
                stage="interest_by_city",
                city="India",
                query=trend_query,
                purpose=(
                    "Compare where relative search interest appears across Indian cities, when "
                    "Google Trends has enough data."
                ),
            ),
        ]
    )

    return ResearchPlan(
        product_summary=(
            f"{request.product_name} in {request.category}, priced at "
            f"₹{request.price_min_inr}–₹{request.price_max_inr}"
        ),
        approved_brief=request.research_brief,
        queries=queries,
        limitations=[
            "Shopping uses a product-first fallback ladder; broader alternatives are not used for direct-price benchmarks.",
            "Maps discovery deliberately widens from product shops to adjacent retail channels.",
            "A Maps business becomes verified only when its reviews contain the product query.",
            "Google Search results are pages to inspect, not proof that a city wants the product.",
            "Google Trends uses a relative 0–100 search-interest scale; it is not search volume, demand, or sales.",
            "The 18-angle Search and News question bank widens human-style market investigation, but pages and articles remain leads to verify, not proof of demand, impact, or future sales.",
            "Search visibility is evidence of market activity, not proof of future sales.",
            "A city recommendation must be validated through a small merchant pilot.",
        ],
    )


def build_research_brief_prompt(request: MerchantResearchRequest) -> str:
    merchant_input = request.model_dump(exclude={"research_brief"}, mode="json")
    return f"""
You are MarketSarthi, an evidence-first research planner for Indian MSME merchants.

Turn the supplied merchant information into a clear research brief that the merchant can edit.

Rules:
- Write in plain English for a small-business merchant. Avoid unexplained research or marketing
  jargon. If a technical term is necessary, explain it in simple words.
- Preserve the merchant's business background, motivation and expansion goal.
- Separate stated facts from assumptions and unknowns.
- Never invent sales, demand, demographics, customer preferences, budget or production facts.
- The brief must request separate analysis of direct competitors and alternative competitors.
- Direct competitors sell the same product type. Alternative competitors solve the same customer
  need but sell a different product type.
- Ask for normalized pack pricing and a small, low-risk pilot rather than guaranteed success.
- Mention important constraints in the brief.
- Keep the main research_brief between 120 and 260 words and write in {request.language}.
- Return valid JSON only with exactly these keys: research_brief, business_facts,
  merchant_goals, constraints, assumptions, open_questions.

Merchant information:
{json.dumps(merchant_input, indent=2)}
""".strip()


def build_fallback_research_brief(
    request: MerchantResearchRequest,
) -> ResearchBriefContent:
    cities = ", ".join(request.target_cities)
    pack_detail = f" in a {request.pack_size} pack" if request.pack_size else ""
    differentiators = ", ".join(request.differentiators) or "not yet specified"
    constraints = ", ".join(request.constraints) or "not yet specified"
    context = (
        f" Merchant context: {request.business_background.strip()}"
        if request.business_background
        else ""
    )
    goal = (
        f" Merchant goal: {request.expansion_goal.strip()}"
        if request.expansion_goal
        else ""
    )
    brief = (
        f"Research whether {request.product_name}{pack_detail}, currently sold from "
        f"{request.current_city} at ₹{request.price_min_inr}–₹{request.price_max_inr}, can be "
        f"tested responsibly in {cities}. Preserve these stated differentiators: "
        f"{differentiators}. Respect these business constraints: {constraints}. Compare businesses "
        "selling the same product separately from other products customers may choose for the "
        "same need. Put prices on a fair basis, such as per pack and per 100 g, when the available "
        "information allows it. Treat shops found on Google Maps as businesses to contact, not "
        "confirmed sellers, unless a product-specific review supports the match. Show missing or "
        "conflicting information, "
        "avoid promising demand or success, and recommend a small measurable pilot before any "
        f"large investment.{context}{goal}"
    )
    facts = [
        f"The product is {request.product_name} in the {request.category} category.",
        f"The current market is {request.current_city}.",
        f"The candidate market(s) are {cities}.",
        f"The stated price range is ₹{request.price_min_inr}–₹{request.price_max_inr}.",
    ]
    if request.pack_size:
        facts.append(f"The stated pack size is {request.pack_size}.")
    return ResearchBriefContent(
        research_brief=brief,
        business_facts=facts[:8],
        merchant_goals=[request.expansion_goal] if request.expansion_goal else [],
        constraints=request.constraints[:8],
        assumptions=[],
        open_questions=[
            "Which pilot size and duration can the business support?",
            "What shelf life and delivery radius can the product reliably support?",
            "Which of the shops we found currently sell this kind of product?",
        ],
    )


_GENERIC_PRODUCT_WORDS = {
    "and",
    "food",
    "foods",
    "healthy",
    "homemade",
    "low",
    "oil",
    "packaged",
    "premium",
    "ready",
    "roasted",
    "snack",
    "snacks",
    "traditional",
}
_ALTERNATIVE_SIGNAL_WORDS = {
    "bar",
    "biscuit",
    "biscuits",
    "chips",
    "cookie",
    "cookies",
    "cracker",
    "crackers",
    "namkeen",
    "protein",
    "snack",
    "snacks",
}


def _normalized_words(value: str) -> list[str]:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return ["khakhra" if word == "khakra" else word for word in normalized.split()]


def product_core_term(product_name: str) -> str:
    meaningful = [
        word
        for word in _normalized_words(product_name)
        if len(word) > 2 and word not in _GENERIC_PRODUCT_WORDS
    ]
    return meaningful[-1] if meaningful else " ".join(_normalized_words(product_name))


def build_shopping_query_ladder(request: MerchantResearchRequest) -> list[str]:
    core = product_core_term(request.product_name)
    candidates = [
        " ".join(part for part in [request.product_name, request.pack_size] if part),
        request.product_name,
        " ".join(part for part in [core, request.pack_size] if part),
        core,
    ]
    if core == "khakhra":
        candidates.append("khakra")
    elif core == "khakra":
        candidates.append("khakhra")
    return list(dict.fromkeys(" ".join(query.split()) for query in candidates if query.strip()))


def build_maps_query_ladder(request: MerchantResearchRequest) -> list[str]:
    core = product_core_term(request.product_name)
    candidates = [f"{core} shop", f"{core} store"]
    if core == "khakhra":
        candidates.extend(["Gujarati snacks shop", "namkeen shop", "farsan shop"])
    else:
        candidates.extend([request.category, f"{request.category} store"])
    return list(dict.fromkeys(" ".join(query.split()) for query in candidates if query.strip()))


def build_web_query_ladder(
    request: MerchantResearchRequest,
    city: str,
) -> list[tuple[str, str, str]]:
    core = product_core_term(request.product_name)
    availability_question = (
        f"Where is {request.product_name} currently visible or sold in {city}?"
    )
    candidates = [
        (
            request.product_name,
            availability_question,
            "Find pages that clearly connect the merchant's product with the target city.",
        ),
        (
            f"where to buy {core}",
            availability_question,
            "Look for sellers, marketplaces and shop pages using customer buying language.",
        ),
        (
            f"{core} sellers distributor wholesale",
            f"Which distribution or wholesale leads are visible for {city}?",
            "Find seller, retailer and distribution leads that the merchant can verify directly.",
        ),
        (
            f"{core} brands price",
            f"Which {core} brands and price positions appear online around {city}?",
            "Find brand and price pages that can support, but not replace, Shopping evidence.",
        ),
        (
            f"upcoming {request.category} exhibition trade fair",
            f"Which announced fairs, exhibitions or trade events could matter in {city}?",
            "Find official event, venue, organizer or registration pages for announced events.",
        ),
        (
            f"{request.category} association government scheme MSME",
            f"Which associations, government notices or MSME programmes could matter in {city}?",
            "Find official organizations, schemes and notices that the merchant can inspect.",
        ),
    ]
    unique: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for query, question, purpose in candidates:
        normalized = " ".join(query.split())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            unique.append((normalized, question, purpose))
    return unique


def build_news_query_ladder(
    request: MerchantResearchRequest,
    city: str,
) -> list[tuple[str, str, str]]:
    core = product_core_term(request.product_name)
    candidates = [
        (
            f"{request.product_name} {city}",
            f"Has the exact product appeared in reported developments around {city}?",
            "Start with the merchant's full product wording without forcing an exact quoted phrase.",
        ),
        (
            f"{core} {city}",
            f"Has the broader product type appeared in reported developments around {city}?",
            "Widen from the full product name to its main product term.",
        ),
        (
            f"{request.category} {city}",
            f"What reported changes are affecting the wider category in {city}?",
            "Look for city-level category developments without treating coverage as demand.",
        ),
        (
            f"{core} India",
            f"What product developments elsewhere in India could still matter to {city}?",
            "Look for national product changes that may provide wider context.",
        ),
        (
            f"{request.category} India",
            f"What wider Indian category developments could affect a pilot in {city}?",
            "Look for national category context while keeping it separate from city evidence.",
        ),
        (
            f"upcoming {request.category} festival event {city}",
            f"Are any relevant festivals or public events announced for {city}?",
            "Look for announced events; an article is not confirmation until its source is checked.",
        ),
        (
            f"upcoming {request.category} exhibition trade fair expo {city}",
            f"Are any relevant exhibitions, trade fairs or expos announced for {city}?",
            "Look for business events where a merchant might learn, exhibit or meet buyers.",
        ),
        (
            f"{request.category} retailer supermarket expansion {city}",
            f"Are retailers or supermarkets expanding relevant channels in {city}?",
            "Look for reported retail openings or expansion without assuming product fit.",
        ),
        (
            f"{request.category} distributor wholesale expansion {city}",
            f"Are distribution or wholesale networks changing around {city}?",
            "Look for reported distribution changes that require direct business verification.",
        ),
        (
            f"{request.category} new product launch brand expansion India",
            "Which competitor launches or brand expansions could affect this category?",
            "Look for launches and expansion announcements as competitive context.",
        ),
        (
            f"{request.category} regulation FSSAI government scheme MSME India",
            "Have regulations, government notices or MSME schemes changed for this category?",
            "Look for reported policy or support changes and verify them on official sources.",
        ),
        (
            f"{request.category} raw material price supply consumer trend India",
            "Are supply, input-price or consumer-behaviour changes being reported?",
            "Look for reported operating or customer-context changes without inferring future sales.",
        ),
    ]
    unique: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for query, question, purpose in candidates:
        normalized = " ".join(query.split())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            unique.append((normalized, question, purpose))
    return unique


def classify_shopping_result(
    title: str,
    request: MerchantResearchRequest,
) -> tuple[CompetitorType, str]:
    title_words = set(_normalized_words(title))
    product_words = [
        word
        for word in _normalized_words(request.product_name)
        if len(word) > 2 and word not in _GENERIC_PRODUCT_WORDS
    ]
    product_core = product_words[-1] if product_words else None
    category_words = {
        word
        for word in _normalized_words(request.category)
        if len(word) > 3 and word not in _GENERIC_PRODUCT_WORDS
    }

    if product_core and product_core in title_words:
        return (
            CompetitorType.DIRECT,
            f"Same product type: the listing explicitly contains '{product_core}'.",
        )
    if title_words & (category_words | _ALTERNATIVE_SIGNAL_WORDS):
        return (
            CompetitorType.ALTERNATIVE,
            "This is a different product, but customers may choose it for the same snacking need.",
        )
    return (
        CompetitorType.UNCERTAIN,
        "The title does not contain enough product information for a reliable classification.",
    )


def extract_pack_metrics(title: str, price: Any) -> dict[str, float | int | None]:
    pack_match = re.search(r"(?:pack\s+of|pack\s*x|x)\s*(\d+)", title, flags=re.IGNORECASE)
    pack_count = int(pack_match.group(1)) if pack_match else 1
    weight_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(kg|g|gm|grams?)\b",
        title,
        flags=re.IGNORECASE,
    )
    grams_per_pack: float | None = None
    if weight_match:
        weight = float(weight_match.group(1))
        grams_per_pack = weight * 1_000 if weight_match.group(2).lower() == "kg" else weight

    numeric_price = float(price) if isinstance(price, (int, float)) else None
    price_per_pack = numeric_price / pack_count if numeric_price is not None else None
    price_per_100g = (
        price_per_pack / grams_per_pack * 100
        if price_per_pack is not None and grams_per_pack
        else None
    )
    return {
        "pack_count": pack_count,
        "grams_per_pack": grams_per_pack,
        "price_per_pack_inr": round(price_per_pack, 2) if price_per_pack is not None else None,
        "price_per_100g_inr": round(price_per_100g, 2) if price_per_100g is not None else None,
    }


def _source_url(result: dict[str, Any]) -> str | None:
    for key in ("product_link", "link", "website"):
        value = result.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return None


def deduplicate_shopping_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for result in results:
        product_id = result.get("product_id") or result.get("product_id_v2")
        if product_id:
            key: tuple[Any, ...] = ("product", str(product_id))
        else:
            key = (
                "listing",
                str(result.get("title", "")).strip().lower(),
                str(result.get("source", "")).strip().lower(),
                result.get("extracted_price"),
            )
        existing = unique.get(key)
        if existing is None:
            unique[key] = result
            continue
        source_queries = existing.setdefault("_source_queries", [])
        for query in result.get("_source_queries", []):
            if query not in source_queries:
                source_queries.append(query)
        if result.get("_evidence_scope") == EvidenceScope.CITY_LOCAL:
            existing["_evidence_scope"] = EvidenceScope.CITY_LOCAL
    return list(unique.values())


def deduplicate_maps_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for result in results:
        place_key = result.get("data_id") or result.get("place_id")
        if place_key:
            key: tuple[Any, ...] = ("place", str(place_key))
        else:
            key = (
                "listing",
                str(result.get("title", "")).strip().lower(),
                str(result.get("address", "")).strip().lower(),
            )
        existing = unique.get(key)
        if existing is None:
            unique[key] = result
            continue
        existing_queries = existing.setdefault("_discovered_by_queries", [])
        for query in result.get("_discovered_by_queries", []):
            if query not in existing_queries:
                existing_queries.append(query)
    return list(unique.values())


def normalize_shopping(
    payload: dict[str, Any],
    city: str,
    request: MerchantResearchRequest,
) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for result in payload.get("shopping_results", [])[:12]:
        title = result.get("title")
        if not title:
            continue
        price = result.get("extracted_price")
        rating = result.get("rating")
        reviews = result.get("reviews")
        seller = result.get("source", "Google Shopping")
        competitor_type, classification_reason = classify_shopping_result(str(title), request)
        pack_metrics = extract_pack_metrics(str(title), price)
        facts = [f"Seller: {seller}"]
        if price is not None:
            facts.append(f"Listed price: ₹{price}")
        if rating is not None:
            facts.append(f"Rating: {rating}")
        if reviews is not None:
            facts.append(f"Reviews: {reviews}")
        if pack_metrics["price_per_pack_inr"] is not None and pack_metrics["pack_count"] != 1:
            facts.append(f"Normalized price/pack: ₹{pack_metrics['price_per_pack_inr']}")
        if pack_metrics["price_per_100g_inr"] is not None:
            facts.append(f"Normalized price/100g: ₹{pack_metrics['price_per_100g_inr']}")
        evidence.append(
            EvidenceItem(
                evidence_type=EvidenceType.SHOPPING,
                city=city,
                title=str(title),
                observation="; ".join(facts),
                source_name=str(seller),
                source_url=_source_url(result),
                provider="SerpApi",
                engine="google_shopping",
                evidence_scope=result.get(
                    "_evidence_scope",
                    EvidenceScope.INDIA_WIDE_ONLINE,
                ),
                competitor_type=competitor_type,
                classification_reason=classification_reason,
                metrics={
                    "price_inr": price,
                    "rating": rating,
                    "review_count": reviews,
                    "position": result.get("position"),
                    "source_queries": result.get("_source_queries", []),
                    **pack_metrics,
                },
            )
        )
    return evidence


def normalize_maps(payload: dict[str, Any], city: str) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for result in payload.get("local_results", [])[:20]:
        title = result.get("title")
        if not title:
            continue
        rating = result.get("rating")
        reviews = result.get("reviews")
        place_type = result.get("type") or result.get("type_id") or "Local business"
        address = result.get("address")
        facts = [f"Category: {place_type}"]
        if rating is not None:
            facts.append(f"Rating: {rating}")
        if reviews is not None:
            facts.append(f"Reviews: {reviews}")
        if address:
            facts.append(f"Address: {address}")
        evidence.append(
            EvidenceItem(
                evidence_type=EvidenceType.LOCAL_CHANNEL,
                city=city,
                title=str(title),
                observation="; ".join(facts),
                source_name="Google Maps via SerpApi",
                source_url=_source_url(result),
                provider="SerpApi",
                engine="google_maps",
                evidence_scope=EvidenceScope.CITY_LOCAL,
                channel_status=LocalChannelStatus.POTENTIAL,
                classification_reason=(
                    "This shop may be worth contacting, but we have not confirmed that it sells "
                    "the product now."
                ),
                metrics={
                    "rating": rating,
                    "review_count": reviews,
                    "category": place_type,
                    "data_id": result.get("data_id"),
                    "place_id": result.get("place_id"),
                    "discovered_by_queries": result.get("_discovered_by_queries", []),
                },
            )
        )
    return evidence


def _metadata_source_url(payload: dict[str, Any], *keys: str) -> str | None:
    metadata = payload.get("search_metadata", {})
    if not isinstance(metadata, dict):
        return None
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return None


def payload_cache_hit(payload: dict[str, Any]) -> bool:
    return payload.get("_marketsarthi_cache_hit") is True


def normalize_web(
    payload: dict[str, Any],
    city: str,
    query: str,
    research_question: str | None = None,
) -> list[EvidenceItem]:
    results = payload.get("organic_results", [])
    if not isinstance(results, list):
        return []
    city_name = city.split(",", maxsplit=1)[0].strip().lower()
    evidence: list[EvidenceItem] = []
    seen: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            continue
        title = str(result.get("title", "")).strip()
        link = result.get("link")
        if not title or not isinstance(link, str) or not link.startswith(("http://", "https://")):
            continue
        identity = link.lower().rstrip("/")
        if identity in seen:
            continue
        seen.add(identity)
        snippet = " ".join(str(result.get("snippet", "")).split())[:500]
        displayed_link = str(result.get("displayed_link", "")).strip()
        haystack = f"{title} {snippet} {displayed_link}".lower()
        city_mentioned = bool(city_name and city_name in haystack)
        observation = snippet or f"Google returned this page for the search '{query} {city}'."
        evidence.append(
            EvidenceItem(
                evidence_type=EvidenceType.WEB,
                city=city,
                title=title,
                observation=observation,
                source_name=displayed_link or "Google Search via SerpApi",
                source_url=link,
                provider="SerpApi",
                engine="google",
                evidence_scope=(
                    EvidenceScope.CITY_LOCAL
                    if city_mentioned
                    else EvidenceScope.INDIA_WIDE_ONLINE
                ),
                classification_reason=(
                    f"This page clearly mentions {city}."
                    if city_mentioned
                    else (
                        f"This result came from a search for {city}, but the page preview does not "
                        "clearly mention the city. Treat it as wider online evidence."
                    )
                ),
                metrics={
                    "position": result.get("position"),
                    "date": result.get("date"),
                    "displayed_link": displayed_link,
                    "query": f"{query} {city}",
                    "research_question": research_question,
                    "city_mentioned": city_mentioned,
                },
            )
        )
        if len(evidence) >= 8:
            break
    return evidence


def _news_source_name(source: Any) -> str:
    if isinstance(source, dict):
        name = source.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    if isinstance(source, str) and source.strip():
        return source.strip()
    return "Google News via SerpApi"


def _flatten_news_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("news_results", [])
    if not isinstance(results, list):
        return []
    flattened: list[dict[str, Any]] = []
    queue = [item for item in results if isinstance(item, dict)]
    while queue and len(flattened) < 30:
        item = queue.pop(0)
        stories = item.get("stories", [])
        if isinstance(stories, list):
            queue.extend(story for story in stories if isinstance(story, dict))
        if item.get("title") and item.get("link"):
            flattened.append(item)
    return flattened


def normalize_news(
    payload: dict[str, Any],
    city: str,
    query: str,
    research_question: str | None = None,
) -> list[EvidenceItem]:
    city_name = city.split(",", maxsplit=1)[0].strip().lower()
    evidence: list[EvidenceItem] = []
    seen: set[str] = set()
    for result in _flatten_news_results(payload):
        title = str(result.get("title", "")).strip()
        link = result.get("link")
        if not title or not isinstance(link, str) or not link.startswith(("http://", "https://")):
            continue
        identity = link.lower().rstrip("/")
        if identity in seen:
            continue
        seen.add(identity)
        snippet = " ".join(str(result.get("snippet", "")).split())[:500]
        published = result.get("iso_date") or result.get("date")
        source_name = _news_source_name(result.get("source"))
        haystack = f"{title} {snippet}".lower()
        city_mentioned = bool(city_name and city_name in haystack)
        details = [snippet] if snippet else []
        if source_name:
            details.append(f"Publisher: {source_name}")
        if published:
            details.append(f"Published: {published}")
        evidence.append(
            EvidenceItem(
                evidence_type=EvidenceType.NEWS,
                city=city,
                title=title,
                observation="; ".join(details),
                source_name=source_name,
                source_url=link,
                provider="SerpApi",
                engine="google_news",
                evidence_scope=(
                    EvidenceScope.CITY_LOCAL
                    if city_mentioned
                    else EvidenceScope.INDIA_WIDE_ONLINE
                ),
                classification_reason=(
                    f"This recent article preview clearly mentions {city}. It provides context, "
                    "not proof of demand or market impact."
                    if city_mentioned
                    else (
                        f"This article came from a news search for {city}, but its preview does not "
                        "clearly mention the city. Treat it as wider context, not local evidence."
                    )
                ),
                metrics={
                    "position": result.get("position"),
                    "date": result.get("date"),
                    "iso_date": result.get("iso_date"),
                    "query": query,
                    "research_question": research_question,
                    "city_mentioned": city_mentioned,
                },
            )
        )
        if len(evidence) >= 8:
            break
    return evidence


def _trend_value(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def normalize_trends_timeseries(
    payload: dict[str, Any],
    query: str,
) -> list[EvidenceItem]:
    interest = payload.get("interest_over_time", {})
    timeline = interest.get("timeline_data", []) if isinstance(interest, dict) else []
    if not isinstance(timeline, list):
        return []
    points: list[tuple[str, float]] = []
    for row in timeline:
        if not isinstance(row, dict):
            continue
        values = row.get("values", [])
        if not isinstance(values, list) or not values:
            continue
        selected = next(
            (
                value
                for value in values
                if isinstance(value, dict)
                and str(value.get("query", query)).strip().lower() == query.lower()
            ),
            values[0],
        )
        if not isinstance(selected, dict):
            continue
        score = _trend_value(selected.get("extracted_value"))
        if score is None:
            score = _trend_value(selected.get("value"))
        if score is not None:
            points.append((str(row.get("date", "Unknown period")), score))
    if not points:
        return []

    window = max(1, min(13, len(points) // 4 or 1))
    earlier_average = statistics.mean(score for _, score in points[:window])
    recent_average = statistics.mean(score for _, score in points[-window:])
    change = recent_average - earlier_average
    direction = "similar"
    if change >= 5:
        direction = "higher"
    elif change <= -5:
        direction = "lower"
    peak_date, peak_value = max(points, key=lambda point: point[1])
    observation = (
        f"Across {len(points)} Google Trends time points for India, recent relative search "
        f"interest averaged {recent_average:.0f}/100 versus {earlier_average:.0f}/100 near the "
        f"start of the period. Recent interest was {direction}. The peak was {peak_value:.0f}/100 "
        f"during {peak_date}. This scale is relative and does not measure demand or sales."
    )
    return [
        EvidenceItem(
            evidence_type=EvidenceType.TREND,
            city="India",
            title=f"How searches for {query} changed over 12 months",
            observation=observation,
            source_name="Google Trends via SerpApi",
            source_url=_metadata_source_url(payload, "google_trends_url", "google_url"),
            provider="SerpApi",
            engine="google_trends",
            evidence_scope=EvidenceScope.INDIA_WIDE_ONLINE,
            classification_reason=(
                "This is a relative Google search-interest signal for India, not a count of "
                "searches, buyers, demand, or sales."
            ),
            metrics={
                "query": query,
                "period": "past_12_months",
                "points": len(points),
                "earlier_average": round(earlier_average, 1),
                "recent_average": round(recent_average, 1),
                "change_points": round(change, 1),
                "direction": direction,
                "peak_value": peak_value,
                "peak_date": peak_date,
            },
        )
    ]


def normalize_trends_by_city(
    payload: dict[str, Any],
    query: str,
    target_cities: list[str],
) -> list[EvidenceItem]:
    regions = payload.get("interest_by_region", [])
    if not isinstance(regions, list):
        return []
    usable: list[tuple[str, float]] = []
    for region in regions:
        if not isinstance(region, dict):
            continue
        location = str(region.get("location", "")).strip()
        score = _trend_value(region.get("extracted_value"))
        if score is None:
            score = _trend_value(region.get("value"))
        if location and score is not None:
            usable.append((location, score))
    if not usable:
        return []

    target_names = [city.split(",", maxsplit=1)[0].strip() for city in target_cities]
    target_rows = [
        (location, score)
        for location, score in usable
        if any(
            target.lower() in location.lower() or location.lower() in target.lower()
            for target in target_names
        )
    ]
    top_rows = sorted(usable, key=lambda row: row[1], reverse=True)[:5]
    target_text = (
        ", ".join(f"{location}: {score:.0f}/100" for location, score in target_rows)
        if target_rows
        else "No candidate city appeared in the returned city rows"
    )
    top_text = ", ".join(f"{location}: {score:.0f}/100" for location, score in top_rows)
    observation = (
        f"Candidate-city results: {target_text}. Highest returned city rows: {top_text}. "
        "Scores are relative within this Google Trends result. A missing or low score does not "
        "prove that demand is absent."
    )
    return [
        EvidenceItem(
            evidence_type=EvidenceType.TREND,
            city="India",
            title=f"Where searches for {query} appeared in India",
            observation=observation,
            source_name="Google Trends via SerpApi",
            source_url=_metadata_source_url(payload, "google_trends_url", "google_url"),
            provider="SerpApi",
            engine="google_trends",
            evidence_scope=EvidenceScope.INDIA_WIDE_ONLINE,
            classification_reason=(
                "This compares relative Google search interest between returned cities. It does "
                "not measure market size, buyer intent, demand, or sales."
            ),
            metrics={
                "query": query,
                "target_city_scores": [
                    {"city": location, "score": score} for location, score in target_rows
                ],
                "top_city_scores": [
                    {"city": location, "score": score} for location, score in top_rows
                ],
            },
        )
    ]


_REVIEW_THEME_WORDS = {
    "taste_and_texture": {
        "taste",
        "tasty",
        "flavor",
        "flavour",
        "delicious",
        "spicy",
        "salt",
        "salty",
        "crisp",
        "crispy",
        "crunch",
        "crunchy",
    },
    "oil_and_health": {"oil", "oily", "healthy", "health", "light", "roasted"},
    "price_and_value": {
        "price",
        "cost",
        "expensive",
        "cheap",
        "value",
        "affordable",
    },
    "packaging_and_freshness": {
        "pack",
        "package",
        "packaging",
        "fresh",
        "stale",
        "expiry",
        "shelf",
    },
    "availability_and_variety": {
        "stock",
        "available",
        "availability",
        "variety",
        "selection",
    },
}


def extract_review_text(review: dict[str, Any]) -> str | None:
    extracted = review.get("extracted_snippet")
    if isinstance(extracted, dict):
        for key in ("original", "translated"):
            value = extracted.get(key)
            if isinstance(value, str) and value.strip():
                return " ".join(value.split())
    snippet = review.get("snippet")
    if isinstance(snippet, str) and snippet.strip():
        return " ".join(snippet.split())
    return None


def extract_review_themes(text: str) -> list[str]:
    words = set(_normalized_words(text))
    return [
        theme
        for theme, signals in _REVIEW_THEME_WORDS.items()
        if words & signals
    ]


def normalize_review_evidence(
    payload: dict[str, Any],
    channel: EvidenceItem,
    city: str,
    product_query: str,
) -> list[EvidenceItem]:
    reviews = payload.get("reviews", [])
    if not isinstance(reviews, list):
        return []
    evidence: list[EvidenceItem] = []
    for review in reviews:
        if not isinstance(review, dict):
            continue
        text = extract_review_text(review)
        if not text:
            continue
        clipped_text = text[:280].rstrip()
        facts = [f'Review excerpt: "{clipped_text}"']
        if review.get("rating") is not None:
            facts.append(f"Rating: {review['rating']}")
        review_date = review.get("iso_date") or review.get("date")
        if review_date:
            facts.append(f"Date: {review_date}")
        evidence.append(
            EvidenceItem(
                evidence_type=EvidenceType.REVIEW,
                city=city,
                title=f"Product mention at {channel.title}",
                observation="; ".join(facts),
                source_name="Google Maps Reviews via SerpApi",
                source_url=_source_url(review) or channel.source_url,
                provider="SerpApi",
                engine="google_maps_reviews",
                evidence_scope=EvidenceScope.BUSINESS_REVIEW,
                classification_reason=(
                    f"This review was found by searching for '{product_query}'. It is one customer "
                    "comment from one shop, not proof of what the whole city thinks."
                ),
                metrics={
                    "rating": review.get("rating"),
                    "date": review_date,
                    "review_id": review.get("review_id"),
                    "themes": extract_review_themes(text),
                    "review_query": product_query,
                    "channel_title": channel.title,
                },
            )
        )
        if len(evidence) >= 3:
            break
    return evidence


def apply_review_verification(
    item: EvidenceItem,
    review_payload: dict[str, Any],
    product_query: str,
) -> int:
    reviews = review_payload.get("reviews", [])
    if not isinstance(reviews, list):
        reviews = []
    matching_reviews = [review for review in reviews if isinstance(review, dict)]
    count = len(matching_reviews)
    item.metrics["matching_review_count"] = count
    item.metrics["review_query"] = product_query
    if count:
        item.channel_status = LocalChannelStatus.VERIFIED_PRODUCT_MENTION
        item.classification_reason = (
            f"{count} Google Maps review(s) mentioned '{product_query}' at this shop. "
            "Call the shop to confirm that it sells the product now."
        )
    return count


def summarize_city(
    city: str,
    evidence: Iterable[EvidenceItem],
    request: MerchantResearchRequest,
) -> CityEvidenceSummary:
    all_evidence = list(evidence)
    city_evidence = [item for item in all_evidence if item.city == city]
    shopping = [item for item in city_evidence if item.evidence_type == EvidenceType.SHOPPING]
    local = [
        item
        for item in city_evidence
        if item.evidence_type in {EvidenceType.LOCAL_CHANNEL, EvidenceType.LOCAL_COMPETITOR}
    ]
    customer_voice = [
        item for item in city_evidence if item.evidence_type == EvidenceType.REVIEW
    ]
    direct = [item for item in shopping if item.competitor_type == CompetitorType.DIRECT]
    alternative = [item for item in shopping if item.competitor_type == CompetitorType.ALTERNATIVE]
    uncertain = [item for item in shopping if item.competitor_type == CompetitorType.UNCERTAIN]
    verified_local = [
        item
        for item in local
        if item.channel_status == LocalChannelStatus.VERIFIED_PRODUCT_MENTION
    ]
    city_specific_web = [
        item
        for item in city_evidence
        if item.evidence_type == EvidenceType.WEB
        and item.evidence_scope == EvidenceScope.CITY_LOCAL
    ]
    city_specific_news = [
        item
        for item in city_evidence
        if item.evidence_type == EvidenceType.NEWS
        and item.evidence_scope == EvidenceScope.CITY_LOCAL
    ]
    city_name = city.split(",", maxsplit=1)[0].strip().lower()
    trend_interest_score: float | None = None
    for item in all_evidence:
        if item.evidence_type != EvidenceType.TREND:
            continue
        target_scores = item.metrics.get("target_city_scores", [])
        if not isinstance(target_scores, list):
            continue
        for score_row in target_scores:
            if not isinstance(score_row, dict):
                continue
            score_city = str(score_row.get("city", "")).strip().lower()
            score = score_row.get("score")
            if city_name and (
                city_name in score_city or score_city in city_name
            ) and isinstance(score, (int, float)):
                trend_interest_score = float(score)
                break
        if trend_interest_score is not None:
            break
    prices = [
        float(item.metrics.get("price_per_pack_inr") or item.metrics["price_inr"])
        for item in direct
        if isinstance(
            item.metrics.get("price_per_pack_inr") or item.metrics.get("price_inr"),
            (int, float),
        )
    ]
    prices_per_100g = [
        float(item.metrics["price_per_100g_inr"])
        for item in direct
        if isinstance(item.metrics.get("price_per_100g_inr"), (int, float))
    ]
    observed_min = min(prices) if prices else None
    observed_max = max(prices) if prices else None
    if observed_min is None or observed_max is None:
        price_signal = PriceBandSignal.UNKNOWN
    elif request.price_max_inr < observed_min:
        price_signal = PriceBandSignal.BELOW_OBSERVED
    elif request.price_min_inr > observed_max:
        price_signal = PriceBandSignal.ABOVE_OBSERVED
    else:
        price_signal = PriceBandSignal.OVERLAPS_OBSERVED

    evidence_gaps: list[str] = []
    if len(direct) < 3:
        evidence_gaps.append("We found fewer than three prices for the same kind of product.")
    if len(local) < 5:
        evidence_gaps.append("We found fewer than five nearby shops to check.")
    if not verified_local:
        evidence_gaps.append("We did not find a shop review that mentions this product.")
    if not customer_voice:
        evidence_gaps.append("We did not find a usable customer review excerpt for this product.")
    if not prices:
        evidence_gaps.append("We did not find a usable pack price for the same kind of product.")
    if not prices_per_100g:
        evidence_gaps.append("We could not compare prices per 100 g from the available listings.")

    if len(direct) >= 3 and len(local) >= 5 and verified_local and prices:
        coverage_level = EvidenceCoverageLevel.PILOT_READY
        next_action = (
            "Call the shop with a product mention to confirm current stock, then plan a small "
            "measured test."
        )
    elif direct or local:
        coverage_level = EvidenceCoverageLevel.DEVELOPING
        next_action = (
            "Check the missing information below and confirm which shops currently sell this "
            "kind of product before sending stock."
        )
    else:
        coverage_level = EvidenceCoverageLevel.LIMITED
        next_action = (
            "Search for more similar products and nearby shops before choosing where to run a test."
        )

    evidence_dimensions = [
        len(direct) >= 3,
        bool(prices),
        len(local) >= 5,
        bool(verified_local),
        bool(city_specific_web),
        trend_interest_score is not None,
    ]
    dimensions_met = sum(evidence_dimensions)
    dimensions_total = len(evidence_dimensions)

    return CityEvidenceSummary(
        city=city,
        shopping_results=len(shopping),
        local_channels=len(local),
        direct_competitors=len(direct),
        alternative_competitors=len(alternative),
        uncertain_competitors=len(uncertain),
        observed_price_min=observed_min,
        observed_price_median=statistics.median(prices) if prices else None,
        observed_price_max=observed_max,
        direct_price_per_100g_median=(
            statistics.median(prices_per_100g) if prices_per_100g else None
        ),
        verified_local_channels=len(verified_local),
        city_specific_web_results=len(city_specific_web),
        city_specific_news_results=len(city_specific_news),
        trend_interest_score=trend_interest_score,
        evidence_dimensions_met=dimensions_met,
        evidence_dimensions_total=dimensions_total,
        evidence_coverage_percent=round(dimensions_met / dimensions_total * 100),
        coverage_level=coverage_level,
        price_band_signal=price_signal,
        evidence_gaps=evidence_gaps,
        next_action=next_action,
    )


def apply_competitor_classifications(
    evidence: list[EvidenceItem],
    classifications: list[CompetitorClassification],
) -> None:
    shopping_by_id = {
        item.id: item for item in evidence if item.evidence_type == EvidenceType.SHOPPING
    }
    for classification in classifications:
        item = shopping_by_id.get(classification.evidence_id)
        if item is None:
            continue
        item.competitor_type = classification.competitor_type
        item.classification_reason = classification.reason


def apply_jev_classifications(
    evidence: list[EvidenceItem],
    classifications: list[JevShoppingClassification],
    minimum_confidence: float,
) -> tuple[int, int]:
    """Apply only confidence-gated Jev decisions; preserve existing labels otherwise."""
    shopping_by_id = {
        item.id: item for item in evidence if item.evidence_type == EvidenceType.SHOPPING
    }
    applied = 0
    skipped = 0
    label_explanations = {
        CompetitorType.DIRECT: "the same product type",
        CompetitorType.ALTERNATIVE: "a different product serving a similar customer need",
        CompetitorType.UNCERTAIN: "uncertain or insufficiently described",
    }
    for classification in classifications:
        item = shopping_by_id.get(classification.evidence_id)
        if item is None:
            continue
        if classification.confidence < minimum_confidence:
            skipped += 1
            continue
        item.competitor_type = classification.competitor_type
        item.classification_source = "TypeSafe Jev"
        item.classification_confidence = round(classification.confidence, 4)
        item.classification_reason = (
            "Jev classified this listing as "
            f"{label_explanations[classification.competitor_type]} "
            f"with {classification.confidence:.0%} confidence."
        )
        applied += 1
    return applied, skipped


def build_synthesis_prompt(
    request: MerchantResearchRequest,
    evidence: list[EvidenceItem],
    summaries: list[CityEvidenceSummary],
) -> str:
    evidence_payload = [item.model_dump(mode="json") for item in evidence]
    summary_payload = [item.model_dump(mode="json") for item in summaries]
    return f"""
You are MarketSarthi, an evidence-first Indian MSME market expansion analyst.

Rules:
- Write for a small-business merchant in plain English. Prefer familiar words and short sentences.
  Avoid unexplained research, analytics, or marketing jargon.
- Use only the supplied evidence. Do not invent demographics, demand, taste, or sales.
- Treat the merchant-approved research brief as context, not as market evidence.
- Treat search visibility as a signal, never proof of market success.
- State uncertainty clearly and recommend a small pilot.
- Refer to observations precisely, but do not claim causation.
- Return valid JSON only with exactly these keys:
  headline, recommendation, product_changes, risks, next_experiments, confidence,
  competitor_classifications.
- confidence must be one of: low, medium, high, insufficient_evidence.
- Classify every shopping evidence item as direct, alternative or uncertain.
- Direct means the same product type. Alternative means a different product serving a similar
  customer need. Do not classify Google Maps evidence.
- Treat Google Maps evidence as unverified local retail or distribution leads. Never call a Maps
  result a competitor or claim it stocks the product unless the supplied evidence proves that.
- Treat Google Maps review excerpts as bounded customer-language observations. Never infer theme
  prevalence, city-wide sentiment or demand from this small filtered sample.
- Treat Google Search items as page previews to inspect. Do not call a page official, local, or
  factually correct unless the supplied fields support that claim.
- Treat Google Trends values as relative search-interest scores within the returned result. Never
  turn them into search volume, buyer intent, demand, market size, sales, or a success forecast.
- Treat Google News items as article previews about reported or publicly announced developments.
  Never treat the number or tone of articles as demand, sentiment, business impact, market size,
  sales, or a prediction. A future event may be mentioned only when the supplied evidence shows it
  was publicly announced. Respect article dates and whether the preview names the target city.
- Respect each evidence_scope: city_local is city-specific, india_wide_online is a national online
  benchmark, and business_review applies only to the named business.
- Base direct price benchmarks only on shopping items classified as direct competitors.
- For every classification, return evidence_id, competitor_type and a short evidence-based reason.

Merchant request:
{request.model_dump_json(indent=2)}

Computed evidence summaries:
{json.dumps(summary_payload, indent=2)}

Evidence ledger:
{json.dumps(evidence_payload, indent=2)}
""".strip()


REFRESH_ENGINES: dict[RefreshSection, set[str]] = {
    RefreshSection.SHOPPING: {"google_shopping"},
    RefreshSection.MAPS_REVIEWS: {"google_maps", "google_maps_reviews"},
    RefreshSection.TRENDS: {"google_trends"},
    RefreshSection.WEB_SEARCH: {"google"},
    RefreshSection.NEWS: {"google_news"},
}


def build_fallback_decision_summary(
    request: MerchantResearchRequest,
    result: ResearchResponse,
) -> DecisionSummaryContent:
    observed: list[str] = []
    for summary in result.city_summaries:
        price_text = (
            f" Similar-product prices found ranged from ₹{summary.observed_price_min:.0f} "
            f"to ₹{summary.observed_price_max:.0f}."
            if summary.observed_price_min is not None and summary.observed_price_max is not None
            else " No reliable similar-product price range was available."
        )
        observed.append(
            f"For {summary.city}, MarketSarthi found {summary.direct_competitors} same-product "
            f"listings and {summary.local_channels} shops to check.{price_text}"
        )
    if not observed:
        observed.append("No usable live market evidence has been collected yet.")

    unknowns = list(
        dict.fromkeys(
            gap
            for summary in result.city_summaries
            for gap in summary.evidence_gaps
        )
    )
    failed_calls = sum(run.status == ToolRunStatus.FAILED for run in result.tool_runs)
    if failed_calls:
        unknowns.append(
            f"{failed_calls} planned searches failed, so those questions remain unanswered."
        )
    if not unknowns:
        unknowns.append(
            "Public search evidence still cannot confirm real purchases, current shop stock, or retailer willingness."
        )

    next_actions = list(
        dict.fromkeys(summary.next_action for summary in result.city_summaries if summary.next_action)
    )
    if not next_actions:
        next_actions.append(
            "Collect the missing evidence, then prepare one small merchant-defined pilot."
        )

    return DecisionSummaryContent(
        observed=observed[:6],
        unknowns=unknowns[:6],
        next_actions=next_actions[:6],
        do_not_conclude=[
            f"Do not conclude that {', '.join(request.target_cities)} will buy the product from search visibility alone.",
            "Do not treat a listed price, review mention, article, or Trends score as proof of demand or future sales.",
            "Do not make a large production or distribution commitment before a bounded real-world pilot.",
        ],
    )


def build_decision_summary_prompt(
    request: MerchantResearchRequest,
    result: ResearchResponse,
    deterministic_summary: DecisionSummaryContent,
) -> str:
    evidence_payload: list[dict[str, Any]] = []
    engines = (
        "google_shopping",
        "google_maps",
        "google_maps_reviews",
        "google_trends",
        "google",
        "google_news",
    )
    for engine in engines:
        evidence_payload.extend(
            {
                "city": item.city,
                "type": item.evidence_type,
                "scope": item.evidence_scope,
                "title": item.title,
                "observation": item.observation,
            }
            for item in [entry for entry in result.evidence if entry.engine == engine][:10]
        )
    return f"""
You are MarketSarthi's final decision-summary assistant for a small Indian merchant.

The deterministic observations, unknowns, and safety warnings below are authoritative. Do not
change their numbers, strengthen them, or invent market facts. Produce short, simple-English next
actions grounded only in the supplied material. Never claim demand, market validation, likely
success, current stock, retailer agreement, or future sales. Recommend a bounded pilot rather than
a large launch.

Merchant request:
{request.model_dump_json(indent=2)}

Authoritative deterministic summary:
{deterministic_summary.model_dump_json(indent=2)}

Source-linked evidence observations:
{json.dumps(evidence_payload, indent=2, default=str)}
""".strip()


class ResearchService:
    def __init__(
        self,
        settings: Settings,
        serpapi: SerpApiClient | None = None,
        gemini: GeminiClient | None = None,
        llm: StructuredLanguageModel | None = None,
        jev: JevClient | None = None,
    ):
        self.settings = settings
        self.serpapi = serpapi or SerpApiClient(settings)
        self.llm = llm or gemini or LanguageModelClient(settings)
        self.jev = jev if jev is not None else (JevClient(settings) if settings.has_typesafe else None)

    async def generate_brief(
        self,
        request: MerchantResearchRequest,
    ) -> ResearchBriefResponse:
        warnings = [
            "Review and edit this AI-generated brief before using it for research.",
            "Do not enter private identity, banking or confidential customer information.",
        ]
        try:
            brief, model_used = await self.llm.generate_structured(
                build_research_brief_prompt(request),
                ResearchBriefContent,
            )
        except (LanguageModelError, ServiceNotConfiguredError, httpx.HTTPError) as exc:
            detail = str(exc).strip() or type(exc).__name__
            brief = build_fallback_research_brief(request)
            model_used = "local-template"
            warnings = [
                f"The AI provider was unavailable ({detail}); MarketSarthi created an editable local draft.",
                "This fallback uses only the merchant-entered facts and makes no AI market claims.",
                "Review and edit the draft before using it for research.",
            ]
        return ResearchBriefResponse(
            brief=brief,
            model_used=model_used,
            warnings=warnings,
        )

    async def refresh_sections(
        self,
        request: MerchantResearchRequest,
        current_result: ResearchResponse,
        sections: list[RefreshSection],
    ) -> ResearchResponse:
        expected_plan = build_research_plan(request)
        if current_result.plan != expected_plan:
            raise ValueError(
                "The merchant details or query plan changed. Run full live analysis before a targeted refresh."
            )
        engines = set().union(*(REFRESH_ENGINES[section] for section in sections))
        previous_bypass = getattr(self.serpapi, "bypass_cache", False)
        if hasattr(self.serpapi, "bypass_cache"):
            self.serpapi.bypass_cache = True
        try:
            refreshed = await self.analyze(
                request,
                enabled_engines=engines,
                include_synthesis=False,
                allow_empty=True,
            )
        finally:
            if hasattr(self.serpapi, "bypass_cache"):
                self.serpapi.bypass_cache = previous_bypass

        merged_evidence = [
            item for item in current_result.evidence if item.engine not in engines
        ] + refreshed.evidence
        merged_runs = [
            run for run in current_result.tool_runs if run.engine not in engines
        ] + refreshed.tool_runs
        summaries = [
            summarize_city(city, merged_evidence, request) for city in request.target_cities
        ]
        section_names = ", ".join(section.value.replace("_", " ") for section in sections)
        shopping_refreshed = "google_shopping" in engines
        return ResearchResponse(
            mode=AnalysisMode.LIVE_EVIDENCE,
            plan=expected_plan,
            tool_runs=merged_runs,
            evidence=merged_evidence,
            city_summaries=summaries,
            synthesis=None,
            decision_summary=None,
            decision_model_used=None,
            decision_warnings=[],
            classification_model_used=(
                refreshed.classification_model_used
                if shopping_refreshed
                else current_result.classification_model_used
            ),
            classification_items_applied=(
                refreshed.classification_items_applied
                if shopping_refreshed
                else current_result.classification_items_applied
            ),
            classification_items_skipped=(
                refreshed.classification_items_skipped
                if shopping_refreshed
                else current_result.classification_items_skipped
            ),
            warnings=deduplicate_warnings(
                [
                    *refreshed.warnings,
                    f"Refreshed only: {section_names}. Untouched evidence was preserved.",
                    "Update the final decision summary when all desired refreshes are complete.",
                ]
            ),
        )

    async def update_decision_summary(
        self,
        request: MerchantResearchRequest,
        current_result: ResearchResponse,
    ) -> DecisionSummaryResponse:
        if current_result.plan != build_research_plan(request):
            raise ValueError(
                "The merchant details or query plan changed. Run full live analysis before updating the decision summary."
            )
        fallback = build_fallback_decision_summary(request, current_result)
        warnings = [
            "This summary organizes observed evidence and gaps; it is not a demand or success score."
        ]
        if not current_result.evidence:
            return DecisionSummaryResponse(
                summary=fallback,
                model_used="local-rule-summary",
                warnings=[*warnings, "No live evidence was available for AI explanation."],
            )
        try:
            generated, model_used = await self.llm.generate_structured(
                build_decision_summary_prompt(request, current_result, fallback),
                DecisionSummaryContent,
            )
            unsafe_text = " ".join(generated.next_actions).lower()
            unsafe_phrases = (
                "proves demand",
                "market is validated",
                "city is validated",
                "guaranteed success",
                "guaranteed",
                "proven demand",
                "strong demand",
                "validated demand",
                "will succeed",
                "certain to succeed",
                "full rollout",
                "full expansion",
            )
            if any(phrase in unsafe_text for phrase in unsafe_phrases):
                raise LanguageModelError("AI summary contained a prohibited market-success claim")
            summary = DecisionSummaryContent(
                observed=fallback.observed,
                unknowns=fallback.unknowns,
                next_actions=generated.next_actions,
                do_not_conclude=fallback.do_not_conclude,
            )
        except (LanguageModelError, ServiceNotConfiguredError, httpx.HTTPError) as exc:
            detail = str(exc).strip() or type(exc).__name__
            summary = fallback
            model_used = "local-rule-summary"
            warnings.append(
                f"AI explanation unavailable ({detail}); the deterministic summary was preserved."
            )
        return DecisionSummaryResponse(
            summary=summary,
            model_used=model_used,
            warnings=deduplicate_warnings(warnings),
        )

    async def analyze(
        self,
        request: MerchantResearchRequest,
        enabled_engines: set[str] | None = None,
        include_synthesis: bool = True,
        allow_empty: bool = False,
    ) -> ResearchResponse:
        plan = build_research_plan(request)
        warnings: list[str] = []
        evidence: list[EvidenceItem] = []
        tool_runs: list[ToolRun] = []
        provider_errors = (httpx.HTTPError, SerpApiError, ServiceNotConfiguredError, ValueError)

        async def research_city(
            city: str,
        ) -> tuple[list[EvidenceItem], list[ToolRun], list[str]]:
            city_evidence: list[EvidenceItem] = []
            city_runs: list[ToolRun] = []
            city_warnings: list[str] = []
            city_queries = [
                query
                for query in plan.queries
                if query.city == city
                and (enabled_engines is None or query.engine in enabled_engines)
            ]
            shopping_queries = sorted(
                (query for query in city_queries if query.engine == "google_shopping"),
                key=lambda query: query.fallback_rank or 0,
            )
            maps_queries = sorted(
                (query for query in city_queries if query.engine == "google_maps"),
                key=lambda query: query.fallback_rank or 0,
            )
            web_queries = [query for query in city_queries if query.engine == "google"]
            news_queries = [query for query in city_queries if query.engine == "google_news"]

            collected_products: list[dict[str, Any]] = []
            for query in shopping_queries:
                localized_city = city if query.fallback_rank == 1 else None
                scope = city if localized_city else "India-wide online market"
                try:
                    payload = await self.serpapi.shopping(query.query, localized_city)
                    products = payload.get("shopping_results", [])
                    if not isinstance(products, list):
                        products = []
                    evidence_scope = (
                        EvidenceScope.CITY_LOCAL
                        if localized_city
                        else EvidenceScope.INDIA_WIDE_ONLINE
                    )
                    for product in products:
                        if not isinstance(product, dict):
                            continue
                        tagged_product = {**product}
                        tagged_product["_evidence_scope"] = evidence_scope
                        tagged_product["_source_queries"] = [query.query]
                        collected_products.append(tagged_product)
                    unique_products = deduplicate_shopping_results(collected_products)
                    city_runs.append(
                        ToolRun(
                            research_question=query.research_question,
                            engine=query.engine,
                            tool=query.tool,
                            stage=query.stage,
                            city=city,
                            scope=scope,
                            query=query.query,
                            status=(
                                ToolRunStatus.SUCCESS
                                if products
                                else ToolRunStatus.NO_RESULTS
                            ),
                            result_count=len(products),
                            cache_hit=payload_cache_hit(payload),
                            note=(
                                f"Fallback query {query.fallback_rank}; "
                                f"{len(unique_products)} unique products accumulated."
                            ),
                        )
                    )
                    direct_count = sum(
                        classify_shopping_result(str(product.get("title", "")), request)[0]
                        == CompetitorType.DIRECT
                        for product in unique_products
                    )
                    if len(unique_products) >= 12 or direct_count >= 6:
                        break
                except provider_errors as exc:
                    detail = str(exc).strip() or type(exc).__name__
                    city_runs.append(
                        ToolRun(
                            research_question=query.research_question,
                            engine=query.engine,
                            tool=query.tool,
                            stage=query.stage,
                            city=city,
                            scope=scope,
                            query=query.query,
                            status=ToolRunStatus.FAILED,
                            note=detail,
                        )
                    )

            unique_products = deduplicate_shopping_results(collected_products)
            if unique_products:
                city_evidence.extend(
                    normalize_shopping(
                        {"shopping_results": unique_products},
                        city,
                        request,
                    )
                )
            elif shopping_queries:
                city_warnings.append(
                    "SerpApi Google Shopping found no product evidence for "
                    f"{city} after {len(shopping_queries)} product-first queries."
                )

            collected_places: list[dict[str, Any]] = []
            unique_places: list[dict[str, Any]] = []
            for maps_query in maps_queries:
                try:
                    maps_payload = await self.serpapi.maps(maps_query.query, city)
                    local_results = maps_payload.get("local_results", [])
                    if not isinstance(local_results, list):
                        local_results = []
                    for result in local_results:
                        if not isinstance(result, dict):
                            continue
                        tagged_result = {**result}
                        tagged_result["_discovered_by_queries"] = [maps_query.query]
                        collected_places.append(tagged_result)
                    unique_places = deduplicate_maps_results(collected_places)
                    city_runs.append(
                        ToolRun(
                            research_question=maps_query.research_question,
                            engine=maps_query.engine,
                            tool=maps_query.tool,
                            stage=maps_query.stage,
                            city=city,
                            scope=city,
                            query=maps_query.query,
                            status=(
                                ToolRunStatus.SUCCESS
                                if local_results
                                else ToolRunStatus.NO_RESULTS
                            ),
                            result_count=len(local_results),
                            cache_hit=payload_cache_hit(maps_payload),
                            note=(
                                "Discovery query only; businesses remain potential channels "
                                "until product-specific review verification. "
                                f"{len(unique_places)} unique shops accumulated."
                            ),
                        )
                    )
                except provider_errors as exc:
                    detail = str(exc).strip() or type(exc).__name__
                    city_runs.append(
                        ToolRun(
                            research_question=maps_query.research_question,
                            engine=maps_query.engine,
                            tool=maps_query.tool,
                            stage=maps_query.stage,
                            city=city,
                            scope=city,
                            query=maps_query.query,
                            status=ToolRunStatus.FAILED,
                            note=detail,
                        )
                    )
                    city_warnings.append(
                        f"SerpApi Google Maps query '{maps_query.query}' failed for {city}: {detail}"
                    )

            local_evidence = normalize_maps({"local_results": unique_places}, city)
            city_evidence.extend(local_evidence)

            collected_web_evidence: list[EvidenceItem] = []
            seen_web_sources: set[str] = set()
            city_specific_pages = 0
            for web_query in web_queries:
                try:
                    web_payload = await self.serpapi.web(web_query.query, city)
                    web_evidence = normalize_web(
                        web_payload,
                        city,
                        web_query.query,
                        web_query.research_question,
                    )
                    for item in web_evidence:
                        source_key = str(item.source_url or item.title).lower().rstrip("/")
                        if source_key not in seen_web_sources:
                            seen_web_sources.add(source_key)
                            collected_web_evidence.append(item)
                    city_specific_pages = sum(
                        item.evidence_scope == EvidenceScope.CITY_LOCAL
                        for item in collected_web_evidence
                    )
                    city_runs.append(
                        ToolRun(
                            research_question=web_query.research_question,
                            engine=web_query.engine,
                            tool=web_query.tool,
                            stage=web_query.stage,
                            city=city,
                            scope=city,
                            query=web_query.query,
                            status=(
                                ToolRunStatus.SUCCESS
                                if web_evidence
                                else ToolRunStatus.NO_RESULTS
                            ),
                            result_count=len(web_evidence),
                            cache_hit=payload_cache_hit(web_payload),
                            note=(
                                "Pages that clearly mention the city are labeled city-specific; "
                                "other pages remain wider online evidence. "
                                f"{len(collected_web_evidence)} unique pages and "
                                f"{city_specific_pages} city-specific pages accumulated."
                            ),
                        )
                    )
                except provider_errors as exc:
                    detail = str(exc).strip() or type(exc).__name__
                    city_runs.append(
                        ToolRun(
                            research_question=web_query.research_question,
                            engine=web_query.engine,
                            tool=web_query.tool,
                            stage=web_query.stage,
                            city=city,
                            scope=city,
                            query=web_query.query,
                            status=ToolRunStatus.FAILED,
                            note=detail,
                        )
                    )
                    city_warnings.append(
                        f"SerpApi Google Search failed for {city}: {detail}"
                    )
            city_evidence.extend(collected_web_evidence[:12])

            collected_news_evidence: list[EvidenceItem] = []
            seen_news_sources: set[str] = set()
            for news_index, news_query in enumerate(news_queries, start=1):
                try:
                    news_payload = await self.serpapi.news(news_query.query)
                    news_evidence = normalize_news(
                        news_payload,
                        city,
                        news_query.query,
                        news_query.research_question,
                    )
                    for item in news_evidence:
                        source_key = str(item.source_url or item.title).lower().rstrip("/")
                        if source_key not in seen_news_sources:
                            seen_news_sources.add(source_key)
                            collected_news_evidence.append(item)
                    city_specific_articles = sum(
                        item.evidence_scope == EvidenceScope.CITY_LOCAL
                        for item in collected_news_evidence
                    )
                    city_runs.append(
                        ToolRun(
                            research_question=news_query.research_question,
                            engine=news_query.engine,
                            tool=news_query.tool,
                            stage=news_query.stage,
                            city=city,
                            scope=city,
                            query=news_query.query,
                            status=(
                                ToolRunStatus.SUCCESS
                                if news_evidence
                                else ToolRunStatus.NO_RESULTS
                            ),
                            result_count=len(news_evidence),
                            cache_hit=payload_cache_hit(news_payload),
                            note=(
                                f"Event-intelligence angle {news_query.fallback_rank}; "
                                f"{len(collected_news_evidence)} unique articles and "
                                f"{city_specific_articles} city-specific articles accumulated. "
                                "Articles provide reported context, not proof of demand."
                            ),
                        )
                    )
                    if news_index >= 6 and len(collected_news_evidence) >= 12:
                        break
                except provider_errors as exc:
                    detail = str(exc).strip() or type(exc).__name__
                    city_runs.append(
                        ToolRun(
                            research_question=news_query.research_question,
                            engine=news_query.engine,
                            tool=news_query.tool,
                            stage=news_query.stage,
                            city=city,
                            scope=city,
                            query=news_query.query,
                            status=ToolRunStatus.FAILED,
                            note=detail,
                        )
                    )
                    city_warnings.append(
                        f"SerpApi Google News query '{news_query.query}' failed for {city}: {detail}"
                    )
            city_evidence.extend(collected_news_evidence[:18])

            verification_candidates = [
                item for item in local_evidence if item.metrics.get("data_id")
            ][:3]
            product_query = product_core_term(request.product_name)
            verification_tasks = [
                (
                    item,
                    asyncio.create_task(
                        self.serpapi.maps_reviews(
                            str(item.metrics["data_id"]),
                            query=product_query,
                        )
                    ),
                )
                for item in verification_candidates
            ]
            for item, verification_task in verification_tasks:
                try:
                    review_payload = await verification_task
                    match_count = apply_review_verification(
                        item,
                        review_payload,
                        product_query,
                    )
                    city_evidence.extend(
                        normalize_review_evidence(
                            review_payload,
                            item,
                            city,
                            product_query,
                        )
                    )
                    city_runs.append(
                        ToolRun(
                            research_question=(
                                f"What are customers saying about {product_query} at this shop?"
                            ),
                            engine="google_maps_reviews",
                            tool="verify_local_channel_reviews",
                            stage="local_verification",
                            city=city,
                            scope=item.title,
                            query=product_query,
                            status=(
                                ToolRunStatus.SUCCESS
                                if match_count
                                else ToolRunStatus.NO_RESULTS
                            ),
                            result_count=match_count,
                            cache_hit=payload_cache_hit(review_payload),
                            note=(
                                "Product-specific review matches found; current stock still "
                                "requires direct confirmation."
                                if match_count
                                else "No product-specific review match; lead remains potential."
                            ),
                        )
                    )
                except provider_errors as exc:
                    detail = str(exc).strip() or type(exc).__name__
                    city_runs.append(
                        ToolRun(
                            research_question=(
                                f"What are customers saying about {product_query} at this shop?"
                            ),
                            engine="google_maps_reviews",
                            tool="verify_local_channel_reviews",
                            stage="local_verification",
                            city=city,
                            scope=item.title,
                            query=product_query,
                            status=ToolRunStatus.FAILED,
                            note=detail,
                        )
                    )

            return city_evidence, city_runs, city_warnings

        trend_queries = [
            query
            for query in plan.queries
            if query.engine == "google_trends"
            and (enabled_engines is None or query.engine in enabled_engines)
        ]
        trend_tasks: list[tuple[PlannedQuery, asyncio.Task[dict[str, Any]]]] = []
        for trend_query in trend_queries:
            if trend_query.tool == "compare_city_interest":
                task = asyncio.create_task(
                    self.serpapi.trends_by_region(trend_query.query)
                )
            else:
                task = asyncio.create_task(self.serpapi.trends(trend_query.query))
            trend_tasks.append((trend_query, task))

        city_results = await asyncio.gather(
            *(research_city(city) for city in request.target_cities)
        )
        for city_evidence, city_runs, city_warnings in city_results:
            evidence.extend(city_evidence)
            tool_runs.extend(city_runs)
            warnings.extend(city_warnings)

        for trend_query, trend_task in trend_tasks:
            try:
                trend_payload = await trend_task
                if trend_query.tool == "compare_city_interest":
                    trend_evidence = normalize_trends_by_city(
                        trend_payload,
                        trend_query.query,
                        request.target_cities,
                    )
                    raw_results = trend_payload.get("interest_by_region", [])
                else:
                    trend_evidence = normalize_trends_timeseries(
                        trend_payload,
                        trend_query.query,
                    )
                    interest = trend_payload.get("interest_over_time", {})
                    raw_results = (
                        interest.get("timeline_data", [])
                        if isinstance(interest, dict)
                        else []
                    )
                evidence.extend(trend_evidence)
                raw_count = len(raw_results) if isinstance(raw_results, list) else 0
                tool_runs.append(
                    ToolRun(
                        research_question=trend_query.research_question,
                        engine=trend_query.engine,
                        tool=trend_query.tool,
                        stage=trend_query.stage,
                        city=trend_query.city,
                        scope="India",
                        query=trend_query.query,
                        status=(
                            ToolRunStatus.SUCCESS
                            if trend_evidence
                            else ToolRunStatus.NO_RESULTS
                        ),
                        result_count=raw_count,
                        cache_hit=payload_cache_hit(trend_payload),
                        note=(
                            "Google Trends scores are relative search-interest values, not "
                            "search volume, demand, or sales."
                        ),
                    )
                )
            except provider_errors as exc:
                detail = str(exc).strip() or type(exc).__name__
                tool_runs.append(
                    ToolRun(
                        research_question=trend_query.research_question,
                        engine=trend_query.engine,
                        tool=trend_query.tool,
                        stage=trend_query.stage,
                        city=trend_query.city,
                        scope="India",
                        query=trend_query.query,
                        status=ToolRunStatus.FAILED,
                        note=detail,
                    )
                )
                warnings.append(
                    f"SerpApi Google Trends step '{trend_query.stage}' failed: {detail}"
                )

        if not evidence and not allow_empty:
            if not self.settings.has_serpapi:
                raise ServiceNotConfiguredError("Live analysis requires SERPAPI_KEY")
            raise SerpApiError(
                "SerpApi returned no usable Shopping, Maps, Search, Trends, or News evidence"
            )

        classification_model_used: str | None = None
        classification_items_applied = 0
        classification_items_skipped = 0
        shopping_count = sum(
            item.evidence_type == EvidenceType.SHOPPING for item in evidence
        )
        if self.jev is not None and shopping_count:
            try:
                jev_classifications = await self.jev.classify_shopping(request, evidence)
                classification_items_applied, low_confidence_skipped = apply_jev_classifications(
                    evidence,
                    jev_classifications,
                    self.settings.jev_classification_min_confidence,
                )
                classification_items_skipped = max(
                    shopping_count - classification_items_applied,
                    low_confidence_skipped,
                )
                if classification_items_applied:
                    classification_model_used = self.settings.typesafe_default_model
            except JevClassificationError as exc:
                detail = str(exc).strip() or type(exc).__name__
                classification_items_skipped = shopping_count
                warnings.append(
                    "Jev classification was unavailable; existing MarketSarthi labels were "
                    f"preserved: {detail}"
                )

        summaries = [summarize_city(city, evidence, request) for city in request.target_cities]
        synthesis = None
        mode = AnalysisMode.LIVE_EVIDENCE

        if include_synthesis and self.settings.has_llm:
            try:
                synthesis = await self.llm.synthesize(
                    build_synthesis_prompt(request, evidence, summaries)
                )
                if classification_model_used is None:
                    apply_competitor_classifications(
                        evidence,
                        synthesis.competitor_classifications,
                    )
                summaries = [
                    summarize_city(city, evidence, request) for city in request.target_cities
                ]
                mode = AnalysisMode.LIVE_WITH_SYNTHESIS
            except (LanguageModelError, ServiceNotConfiguredError, httpx.HTTPError) as exc:
                detail = str(exc).strip() or type(exc).__name__
                warnings.append(
                    f"AI synthesis unavailable; evidence was preserved: {detail}"
                )
        elif include_synthesis:
            warnings.append(
                "No language-model API key is configured; returning evidence without synthesis."
            )

        return ResearchResponse(
            mode=mode,
            plan=plan,
            tool_runs=tool_runs,
            evidence=evidence,
            city_summaries=summaries,
            synthesis=synthesis,
            classification_model_used=classification_model_used,
            classification_items_applied=classification_items_applied,
            classification_items_skipped=classification_items_skipped,
            warnings=deduplicate_warnings(warnings),
        )
