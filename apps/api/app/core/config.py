from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_name: str = "MarketSarthi API"
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    llm_provider: Literal["deepseek", "gemini"] = "deepseek"
    llm_fallback_provider: Literal["deepseek", "gemini"] | None = "gemini"

    deepseek_api_key: SecretStr | None = None
    deepseek_model: str = "deepseek-flash"
    deepseek_base_url: str = "https://api.deepseek.com"

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str | None = "gemini-3.6-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    serpapi_key: SecretStr | None = None
    serpapi_base_url: str = "https://serpapi.com/search.json"
    serpapi_cache_ttl_seconds: float = Field(default=3600.0, ge=0, le=86_400)
    serpapi_cache_max_entries: int = Field(default=512, ge=1, le=5_000)

    typesafe_api_key: SecretStr | None = None
    typesafe_default_model: str = "jev-latest"
    typesafe_base_url: str = "https://api.typesafe.ai"
    jev_classification_min_confidence: float = Field(default=0.65, ge=0, le=1)

    request_timeout_seconds: float = 30.0
    database_url: str = "sqlite:///./data/marketsarthi.db"
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", Path.cwd() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.get_secret_value().strip())

    @property
    def has_deepseek(self) -> bool:
        return bool(self.deepseek_api_key and self.deepseek_api_key.get_secret_value().strip())

    @property
    def has_llm(self) -> bool:
        configured = {
            "deepseek": self.has_deepseek,
            "gemini": self.has_gemini,
        }
        if configured[self.llm_provider]:
            return True
        return bool(
            self.llm_fallback_provider
            and configured[self.llm_fallback_provider]
        )

    @property
    def primary_llm_model(self) -> str:
        return self.deepseek_model if self.llm_provider == "deepseek" else self.gemini_model

    @property
    def has_serpapi(self) -> bool:
        return bool(self.serpapi_key and self.serpapi_key.get_secret_value().strip())

    @property
    def has_typesafe(self) -> bool:
        return bool(
            self.typesafe_api_key
            and self.typesafe_api_key.get_secret_value().strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
