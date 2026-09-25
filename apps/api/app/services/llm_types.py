from typing import Protocol, TypeVar

from pydantic import BaseModel

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class LanguageModelError(RuntimeError):
    """Raised when no configured language model can return validated output."""


class LanguageModelTemporaryError(LanguageModelError):
    """Raised after retryable provider failures have been exhausted."""


class StructuredLanguageModel(Protocol):
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[ResponseModel],
    ) -> tuple[ResponseModel, str]: ...
