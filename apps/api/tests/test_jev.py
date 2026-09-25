from types import SimpleNamespace
from typing import ClassVar, Self

import pytest

from app.core.config import Settings
from app.schemas.research import (
    CompetitorType,
    EvidenceItem,
    EvidenceScope,
    EvidenceType,
    MerchantResearchRequest,
)
from app.services.jev import JevClient


class FakeAsyncTypeSafeClient:
    constructor_kwargs: ClassVar[dict[str, object]] = {}

    def __init__(self, **kwargs: object):
        type(self).constructor_kwargs = kwargs

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def system_one(self, *, state: object, questions: dict[str, object]) -> object:
        assert state
        assert set(questions) == {"listing_0"}
        return SimpleNamespace(
            choices={
                "listing_0": SimpleNamespace(
                    choice=CompetitorType.DIRECT.value,
                    confidence=0.91,
                )
            }
        )


@pytest.mark.asyncio
async def test_jev_client_returns_typed_shopping_classification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.jev.AsyncTypeSafeClient", FakeAsyncTypeSafeClient)
    settings = Settings(typesafe_api_key="test-key", _env_file=None)
    request = MerchantResearchRequest(
        product_name="Handmade neem soap",
        category="Natural personal care",
        current_city="Mysuru",
        target_cities=["Bengaluru"],
        price_min_inr=120,
        price_max_inr=170,
    )
    evidence = [
        EvidenceItem(
            evidence_type=EvidenceType.SHOPPING,
            city="Bengaluru",
            title="Handmade neem soap 100 g",
            observation="Seller: Example",
            source_name="Example",
            evidence_scope=EvidenceScope.INDIA_WIDE_ONLINE,
        )
    ]

    classifications = await JevClient(settings).classify_shopping(request, evidence)

    assert len(classifications) == 1
    assert classifications[0].evidence_id == evidence[0].id
    assert classifications[0].competitor_type == CompetitorType.DIRECT
    assert classifications[0].confidence == 0.91
    assert FakeAsyncTypeSafeClient.constructor_kwargs["model"] == "jev-latest"
