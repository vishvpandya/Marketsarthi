from dataclasses import dataclass
from uuid import UUID

from typesafe_sdk import AsyncTypeSafeClient, Choice

from app.core.config import Settings
from app.schemas.research import CompetitorType, EvidenceItem, EvidenceType, MerchantResearchRequest


class JevClassificationError(RuntimeError):
    """Raised when the optional Jev classification call cannot be used safely."""


@dataclass(frozen=True)
class JevShoppingClassification:
    evidence_id: UUID
    competitor_type: CompetitorType
    confidence: float


class JevClient:
    """Optional TypeSafe Jev adapter for fast, typed Shopping classification."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def classify_shopping(
        self,
        request: MerchantResearchRequest,
        evidence: list[EvidenceItem],
    ) -> list[JevShoppingClassification]:
        shopping = [item for item in evidence if item.evidence_type == EvidenceType.SHOPPING]
        if not shopping:
            return []
        if not self.settings.has_typesafe or self.settings.typesafe_api_key is None:
            raise JevClassificationError("TYPESAFE_API_KEY is not configured")

        listings = {f"listing_{index}": item.title for index, item in enumerate(shopping)}
        questions = {
            key: Choice(
                instructions=(
                    f"Classify {key} relative to the merchant's product. Choose only one label."
                ),
                criteria={
                    CompetitorType.DIRECT.value: (
                        "The listing is the same product type as the merchant's product. Flavour, "
                        "brand, pack size, or formulation may differ."
                    ),
                    CompetitorType.ALTERNATIVE.value: (
                        "The listing is a different product type but could serve a similar customer "
                        "need or shopping occasion."
                    ),
                    CompetitorType.UNCERTAIN.value: (
                        "The title is irrelevant, ambiguous, incomplete, or does not provide enough "
                        "information for either of the other labels."
                    ),
                },
            )
            for key in listings
        }
        state = {
            "merchant_product": request.product_name,
            "merchant_category": request.category,
            "instruction_context": (
                "Classify product-listing titles only. Do not infer demand, quality, sales, or "
                "whether the merchant should enter a city."
            ),
            "listings": listings,
        }

        try:
            async with AsyncTypeSafeClient(
                api_key=self.settings.typesafe_api_key.get_secret_value(),
                base_url=self.settings.typesafe_base_url,
                model=self.settings.typesafe_default_model,
                timeout=min(self.settings.request_timeout_seconds, 10.0),
            ) as client:
                response = await client.system_one(state=state, questions=questions)
        except Exception as exc:  # The feature is optional; callers always retain a safe fallback.
            detail = str(exc).strip() or type(exc).__name__
            raise JevClassificationError(detail) from exc

        classifications: list[JevShoppingClassification] = []
        for index, item in enumerate(shopping):
            answer = response.choices.get(f"listing_{index}")
            if answer is None:
                continue
            try:
                competitor_type = CompetitorType(answer.choice)
                confidence = float(answer.confidence)
            except (TypeError, ValueError) as exc:
                raise JevClassificationError("Jev returned an invalid Shopping classification") from exc
            classifications.append(
                JevShoppingClassification(
                    evidence_id=item.id,
                    competitor_type=competitor_type,
                    confidence=confidence,
                )
            )
        return classifications
