import json

import httpx

from app.core.config import Settings
from app.schemas.research import (
    PilotDecisionFacts,
    PilotOutcome,
    PilotReviewNarrative,
    PilotReviewRequest,
    PilotReviewResponse,
)
from app.services.llm import LanguageModelClient
from app.services.llm_types import LanguageModelError, StructuredLanguageModel
from app.services.serpapi import ServiceNotConfiguredError


def calculate_pilot_facts(request: PilotReviewRequest) -> PilotDecisionFacts:
    bought_percent = round(request.packets_bought / request.actual_packets_given * 100, 1)
    returned_percent = round(request.packets_returned / request.actual_packets_given * 100, 1)
    bought_target_met = bought_percent >= request.target_bought_percent
    returned_limit_met = returned_percent <= request.maximum_returned_percent
    has_money_check = request.money_received_inr is not None
    net_cash_result = (
        round(request.money_received_inr - request.nonrecoverable_costs_inr, 2)
        if request.money_received_inr is not None
        and request.nonrecoverable_costs_inr is not None
        else None
    )
    cash_check_met = (
        net_cash_result >= -request.maximum_acceptable_loss_inr
        if net_cash_result is not None
        and request.maximum_acceptable_loss_inr is not None
        else None
    )
    merchant_checks_met = (
        bought_target_met
        and returned_limit_met
        and cash_check_met is not False
    )
    unaccounted = request.actual_packets_given - (
        request.packets_bought
        + request.packets_returned
        + request.packets_damaged
        + request.packets_missing
        + request.packets_still_at_shops
    )

    reasons = [
        (
            f"Customers bought {bought_percent}% of packets given to shops, compared with "
            f"the merchant's {request.target_bought_percent}% target."
        ),
        (
            f"Shops returned {returned_percent}% of packets, compared with the merchant's "
            f"{request.maximum_returned_percent}% maximum."
        ),
        (
            f"{request.shops_asking_another_batch} of {request.shops_planned} planned shops "
            "were recorded as asking for another batch."
        ),
    ]
    if has_money_check and net_cash_result is not None:
        if net_cash_result >= 0:
            money_result = f"₹{net_cash_result:.2f} was left after the entered test costs"
        else:
            money_result = (
                f"the test costs were ₹{abs(net_cash_result):.2f} more than the money received"
            )
        reasons.append(
            f"{money_result}; the merchant said a loss of up to "
            f"₹{request.maximum_acceptable_loss_inr:.2f} was okay for this test."
        )
    if request.packets_damaged:
        reasons.append(
            f"{request.packets_damaged} packets were recorded as damaged during the test."
        )
    data_gaps: list[str] = []
    has_blocking_gap = False
    if request.packets_missing:
        has_blocking_gap = True
        data_gaps.append(
            f"{request.packets_missing} packets are recorded as missing; find or explain them "
            "before placing more stock."
        )
    if request.packets_still_at_shops:
        has_blocking_gap = True
        data_gaps.append(
            f"{request.packets_still_at_shops} packets are still at shops, so the test result "
            "is not final yet."
        )
    if unaccounted:
        has_blocking_gap = True
        data_gaps.append(
            f"{unaccounted} packets are not explained by any stock count."
        )
    if not request.shop_results:
        data_gaps.append(
            "No complete shop-by-shop results were supplied, so differences between retailers "
            "cannot be reviewed."
        )
    else:
        shop_given = sum(item.packets_given for item in request.shop_results)
        shop_bought = sum(item.packets_bought for item in request.shop_results)
        shop_returned = sum(item.packets_returned for item in request.shop_results)
        shop_damaged = sum(item.packets_damaged for item in request.shop_results)
        shop_missing = sum(item.packets_missing for item in request.shop_results)
        shop_still_at_shops = sum(item.packets_still_at_shop for item in request.shop_results)
        if (
            shop_given != request.actual_packets_given
            or shop_bought != request.packets_bought
            or shop_returned != request.packets_returned
            or shop_damaged != request.packets_damaged
            or shop_missing != request.packets_missing
            or shop_still_at_shops != request.packets_still_at_shops
        ):
            has_blocking_gap = True
            data_gaps.append(
                "The shop-by-shop totals do not match the overall pilot totals; review the entries "
                "before making a larger commitment."
            )

    if has_blocking_gap:
        outcome = PilotOutcome.INVESTIGATE_BEFORE_NEXT_TEST
    elif request.packets_damaged:
        outcome = PilotOutcome.MODIFY_AND_RETEST
    elif merchant_checks_met and request.shops_asking_another_batch > 0:
        outcome = PilotOutcome.CONTINUE_SMALL_TEST
    elif bought_target_met and returned_limit_met and cash_check_met is False:
        outcome = PilotOutcome.MODIFY_AND_RETEST
    elif merchant_checks_met:
        outcome = PilotOutcome.INVESTIGATE_BEFORE_NEXT_TEST
    elif bought_target_met or returned_limit_met or cash_check_met is True:
        outcome = PilotOutcome.MODIFY_AND_RETEST
    else:
        outcome = PilotOutcome.STOP_AND_REVIEW

    return PilotDecisionFacts(
        outcome=outcome,
        bought_percent=bought_percent,
        returned_percent=returned_percent,
        bought_target_met=bought_target_met,
        returned_limit_met=returned_limit_met,
        merchant_checks_met=merchant_checks_met,
        planned_packets=request.planned_packets,
        actual_packets_given=request.actual_packets_given,
        packets_bought=request.packets_bought,
        packets_returned=request.packets_returned,
        packets_damaged=request.packets_damaged,
        packets_missing=request.packets_missing,
        packets_still_at_shops=request.packets_still_at_shops,
        packets_unaccounted_for=unaccounted,
        shops_planned=request.shops_planned,
        shops_asking_another_batch=request.shops_asking_another_batch,
        money_received_inr=request.money_received_inr,
        nonrecoverable_costs_inr=request.nonrecoverable_costs_inr,
        maximum_acceptable_loss_inr=request.maximum_acceptable_loss_inr,
        net_cash_result_inr=net_cash_result,
        cash_check_met=cash_check_met,
        reasons=reasons,
        data_gaps=data_gaps,
    )


def build_fallback_pilot_review(
    request: PilotReviewRequest,
    facts: PilotDecisionFacts,
) -> PilotReviewNarrative:
    next_steps = {
        PilotOutcome.CONTINUE_SMALL_TEST: (
            "Run one more bounded test with a small number of similar shops, keep the same "
            "measurement method, and compare whether the result repeats before increasing production."
        ),
        PilotOutcome.MODIFY_AND_RETEST: (
            "Change only one controllable factor—such as price, pack size, shop type, or display—"
            "and repeat a small test so the merchant can observe whether that change matters."
        ),
        PilotOutcome.INVESTIGATE_BEFORE_NEXT_TEST: (
            "Resolve the missing or conflicting packet and shop records first, then run another "
            "small test only after the merchant can measure every packet consistently."
        ),
        PilotOutcome.STOP_AND_REVIEW: (
            "Pause expansion, review retailer and customer notes, and design a smaller test of one "
            "specific product, price, or channel change before placing more stock."
        ),
    }
    worked: list[str] = []
    if facts.bought_target_met:
        worked.append("The merchant's target for packets bought by customers was met.")
    if facts.returned_limit_met:
        worked.append("Returned packets stayed within the merchant's maximum.")
    if request.shops_asking_another_batch:
        worked.append(
            f"{request.shops_asking_another_batch} shops were recorded as asking for another batch."
        )
    if facts.cash_check_met is True:
        worked.append("The money result stayed within the amount the merchant said was okay.")
    attention = list(facts.data_gaps)
    if not facts.bought_target_met:
        attention.append("The percentage bought by customers was below the merchant's target.")
    if not facts.returned_limit_met:
        attention.append("The percentage returned was above the merchant's maximum.")
    if facts.cash_check_met is False:
        attention.append(
            "The test lost more money than the amount the merchant said was okay."
        )
    if facts.packets_damaged:
        attention.append(
            f"{facts.packets_damaged} damaged packets need a packaging, handling, or delivery check."
        )
    if not worked:
        worked.append("The pilot produced measured evidence that can guide a safer next decision.")

    return PilotReviewNarrative(
        summary=(
            f"The deterministic pilot outcome is {facts.outcome.value.replace('_', ' ')}. "
            "This result compares merchant-entered measurements with merchant-defined checks; "
            "it does not validate demand across the city."
        ),
        what_worked=worked[:5],
        what_needs_attention=attention[:5],
        next_experiment=next_steps[facts.outcome],
        do_not_conclude=[
            f"Do not conclude that {request.city} has city-wide demand from this limited pilot.",
            "Do not treat search visibility, a retailer's participation, or one successful shop as a sales forecast.",
        ],
    )


def build_pilot_review_prompt(
    request: PilotReviewRequest,
    facts: PilotDecisionFacts,
) -> str:
    merchant_payload = request.model_dump(mode="json", exclude={"research_context"})
    research_context = [item[:500] for item in request.research_context]
    return f"""
You are MarketSarthi's post-pilot explanation assistant for a small Indian merchant.

The deterministic facts and outcome below are authoritative. Do not recalculate, replace, upgrade,
or downgrade the outcome. Your job is only to explain the supplied facts in simple English and
propose exactly one bounded next experiment.

Rules:
- Use only the supplied merchant measurements, merchant notes, and research context.
- Never invent sales, customer feedback, retailer agreement, causes, market size, demand, or future performance.
- Explain the money check in everyday language: money received minus test costs that were already used up. Do not call it accounting profit, margin, ROI, or long-term viability.
- The merchant may describe one planned change from a previous round. You may compare recorded rounds, but never claim that this change caused the result.
- Clearly separate an observed number from a possible explanation in merchant notes.
- A search result or article is context, not proof that it caused the pilot result.
- Do not call the city validated, successful, high-potential, or ready for full expansion.
- Keep what_worked and what_needs_attention short and specific.
- next_experiment must change or test a bounded action, not recommend a city-wide launch.
- do_not_conclude must include at least one warning against generalizing from this pilot.

Product: {request.product_name}
Pilot city: {request.city}

Authoritative deterministic facts:
{facts.model_dump_json(indent=2)}

Merchant-entered pilot record:
{json.dumps(merchant_payload, indent=2)}

Earlier research context (not proof of demand or causation):
{json.dumps(research_context, indent=2)}
""".strip()


class PilotReviewService:
    def __init__(
        self,
        settings: Settings,
        llm: StructuredLanguageModel | None = None,
    ):
        self.settings = settings
        self.llm = llm or LanguageModelClient(settings)

    async def review(self, request: PilotReviewRequest) -> PilotReviewResponse:
        facts = calculate_pilot_facts(request)
        warnings = [
            "The outcome is calculated from merchant-entered results and is not a city-demand score."
        ]
        try:
            review, model_used = await self.llm.generate_structured(
                build_pilot_review_prompt(request, facts),
                PilotReviewNarrative,
            )
            narrative_for_safety_check = " ".join(
                [
                    review.summary,
                    *review.what_worked,
                    *review.what_needs_attention,
                    review.next_experiment,
                ]
            ).lower()
            unsafe_phrases = (
                "city is validated",
                "market is validated",
                "proves demand",
                "guaranteed success",
                "guarantees success",
                "full rollout",
                "full expansion",
                "will succeed",
            )
            if any(phrase in narrative_for_safety_check for phrase in unsafe_phrases):
                raise LanguageModelError(
                    "AI explanation contained a prohibited market-success claim"
                )
        except (LanguageModelError, ServiceNotConfiguredError, httpx.HTTPError) as exc:
            detail = str(exc).strip() or type(exc).__name__
            review = build_fallback_pilot_review(request, facts)
            model_used = "local-rule-review"
            warnings.append(
                f"AI explanation unavailable ({detail}); deterministic facts and a local next step were preserved."
            )
        return PilotReviewResponse(
            facts=facts,
            review=review,
            model_used=model_used,
            warnings=warnings,
        )
