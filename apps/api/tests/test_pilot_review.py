import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.research import (
    PilotOutcome,
    PilotReviewNarrative,
    PilotReviewRequest,
)
from app.services.llm_types import LanguageModelError
from app.services.pilot_review import PilotReviewService, calculate_pilot_facts


def pilot_request(**overrides: object) -> PilotReviewRequest:
    payload: dict[str, object] = {
        "product_name": "Roasted methi khakhra",
        "city": "Kolkata",
        "planned_packets": 60,
        "actual_packets_given": 60,
        "packets_bought": 54,
        "packets_returned": 6,
        "target_bought_percent": 60,
        "maximum_returned_percent": 10,
        "shops_planned": 3,
        "shops_asking_another_batch": 2,
        "shop_results": [
            {
                "shop_name": "Shop A",
                "packets_given": 30,
                "packets_bought": 27,
                "packets_returned": 3,
                "wants_another_batch": True,
                "notes": "Asked for another small batch.",
            },
            {
                "shop_name": "Shop B",
                "packets_given": 30,
                "packets_bought": 27,
                "packets_returned": 3,
                "wants_another_batch": True,
            },
        ],
        "merchant_notes": "Customers at one shop asked about a smaller pack.",
        "research_context": ["Google Shopping showed comparable online products."],
    }
    payload.update(overrides)
    return PilotReviewRequest.model_validate(payload)


def test_pilot_facts_continue_only_when_checks_and_retailer_signal_are_present() -> None:
    facts = calculate_pilot_facts(pilot_request())

    assert facts.outcome == PilotOutcome.CONTINUE_SMALL_TEST
    assert facts.bought_percent == 90
    assert facts.returned_percent == 10
    assert facts.merchant_checks_met is True
    assert facts.data_gaps == []


def test_pilot_facts_investigate_when_shop_totals_conflict() -> None:
    request = pilot_request(
        shop_results=[
            {
                "shop_name": "Shop A",
                "packets_given": 20,
                "packets_bought": 15,
                "packets_returned": 5,
            }
        ]
    )

    facts = calculate_pilot_facts(request)

    assert facts.outcome == PilotOutcome.INVESTIGATE_BEFORE_NEXT_TEST
    assert any("do not match" in gap for gap in facts.data_gaps)


def test_pilot_facts_accept_matching_full_shop_stock_breakdown() -> None:
    request = pilot_request(
        packets_bought=50,
        packets_returned=5,
        packets_damaged=2,
        packets_missing=0,
        packets_still_at_shops=3,
        shop_results=[
            {
                "shop_name": "Shop A",
                "packets_given": 60,
                "packets_bought": 50,
                "packets_returned": 5,
                "packets_damaged": 2,
                "packets_missing": 0,
                "packets_still_at_shop": 3,
            }
        ],
    )

    facts = calculate_pilot_facts(request)

    assert facts.packets_unaccounted_for == 0
    assert not any("shop-by-shop totals do not match" in gap for gap in facts.data_gaps)


def test_shop_measurement_rejects_impossible_full_stock_breakdown() -> None:
    with pytest.raises(ValidationError):
        pilot_request(
            shop_results=[
                {
                    "shop_name": "Shop A",
                    "packets_given": 20,
                    "packets_bought": 15,
                    "packets_returned": 2,
                    "packets_damaged": 2,
                    "packets_missing": 1,
                    "packets_still_at_shop": 1,
                }
            ]
        )


def test_pilot_facts_allow_aggregate_only_review_with_visible_limitation() -> None:
    facts = calculate_pilot_facts(pilot_request(shop_results=[]))

    assert facts.outcome == PilotOutcome.CONTINUE_SMALL_TEST
    assert any("No complete shop-by-shop" in gap for gap in facts.data_gaps)


def test_pilot_request_rejects_impossible_packet_totals() -> None:
    with pytest.raises(ValidationError):
        pilot_request(packets_bought=58, packets_returned=8)


def test_pilot_request_rejects_impossible_full_stock_breakdown() -> None:
    with pytest.raises(ValidationError):
        pilot_request(
            packets_bought=50,
            packets_returned=5,
            packets_damaged=2,
            packets_missing=2,
            packets_still_at_shops=2,
        )


def test_pilot_facts_pause_when_packets_are_missing_or_still_at_shops() -> None:
    facts = calculate_pilot_facts(
        pilot_request(
            packets_bought=50,
            packets_returned=5,
            packets_missing=2,
            packets_still_at_shops=3,
        )
    )

    assert facts.packets_unaccounted_for == 0
    assert facts.outcome == PilotOutcome.INVESTIGATE_BEFORE_NEXT_TEST
    assert any("recorded as missing" in gap for gap in facts.data_gaps)
    assert any("still at shops" in gap for gap in facts.data_gaps)


def test_pilot_facts_request_retest_when_damage_is_recorded() -> None:
    facts = calculate_pilot_facts(
        pilot_request(
            packets_bought=52,
            packets_returned=6,
            packets_damaged=2,
            shop_results=[],
        )
    )

    assert facts.packets_unaccounted_for == 0
    assert facts.outcome == PilotOutcome.MODIFY_AND_RETEST
    assert any("damaged" in reason for reason in facts.reasons)


def test_pilot_request_requires_complete_money_check() -> None:
    with pytest.raises(ValidationError):
        pilot_request(money_received_inr=5_000)


def test_pilot_money_check_can_require_modification_despite_sales_checks() -> None:
    facts = calculate_pilot_facts(
        pilot_request(
            money_received_inr=4_000,
            nonrecoverable_costs_inr=5_000,
            maximum_acceptable_loss_inr=500,
        )
    )

    assert facts.net_cash_result_inr == -1_000
    assert facts.cash_check_met is False
    assert facts.merchant_checks_met is False
    assert facts.outcome == PilotOutcome.MODIFY_AND_RETEST


async def test_pilot_review_uses_validated_ai_explanation() -> None:
    class WorkingModel:
        async def generate_structured(self, prompt: str, response_model: type[PilotReviewNarrative]):
            assert "authoritative" in prompt.lower()
            assert "change_from_previous_round" in prompt
            assert "changed from" in prompt
            return response_model(
                summary="The merchant's checks were met in this limited measured pilot.",
                what_worked=["Measured customer purchases reached the merchant's target."],
                what_needs_attention=["Results cover only the participating shops."],
                next_experiment="Repeat the same small test in two similar shops before increasing production.",
                do_not_conclude=["Do not treat this as proof of demand across Kolkata."],
            ), "test-model"

    service = PilotReviewService(
        Settings(_env_file=None),
        llm=WorkingModel(),  # type: ignore[arg-type]
    )

    response = await service.review(
        pilot_request(change_from_previous_round="Price: changed from ₹150 to ₹140")
    )

    assert response.facts.outcome == PilotOutcome.CONTINUE_SMALL_TEST
    assert response.model_used == "test-model"
    assert "two similar shops" in response.review.next_experiment


async def test_pilot_review_preserves_facts_when_ai_is_unavailable() -> None:
    class FailingModel:
        async def generate_structured(self, prompt: str, response_model: type[PilotReviewNarrative]):
            raise LanguageModelError("quota unavailable")

    service = PilotReviewService(
        Settings(_env_file=None),
        llm=FailingModel(),  # type: ignore[arg-type]
    )

    response = await service.review(pilot_request())

    assert response.facts.outcome == PilotOutcome.CONTINUE_SMALL_TEST
    assert response.model_used == "local-rule-review"
    assert any("quota unavailable" in warning for warning in response.warnings)


async def test_pilot_review_rejects_unsafe_ai_market_claim() -> None:
    class UnsafeModel:
        async def generate_structured(self, prompt: str, response_model: type[PilotReviewNarrative]):
            return response_model(
                summary="This city is validated and the merchant can now grow confidently.",
                what_worked=["The merchant recorded completed totals."],
                what_needs_attention=[],
                next_experiment="Run another bounded test in two similar shops before producing more.",
                do_not_conclude=["Do not generalize from one participating shop."],
            ), "unsafe-test-model"

    service = PilotReviewService(
        Settings(_env_file=None),
        llm=UnsafeModel(),  # type: ignore[arg-type]
    )

    response = await service.review(pilot_request())

    assert response.model_used == "local-rule-review"
    assert "city is validated" not in response.review.summary.lower()
    assert any("prohibited market-success claim" in warning for warning in response.warnings)
