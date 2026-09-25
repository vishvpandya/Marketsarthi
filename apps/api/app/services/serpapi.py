import asyncio
import copy
import hashlib
import json
import threading
import time
from collections import OrderedDict
from typing import Any

import httpx

from app.core.config import Settings


class ServiceNotConfiguredError(RuntimeError):
    """Raised when an external service credential is missing."""


class SerpApiError(RuntimeError):
    """Raised when SerpApi returns an unusable response."""


_CACHE_LOCK = threading.Lock()
_RESPONSE_CACHE: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()


def clear_serpapi_cache() -> None:
    """Clear process-local public search responses, primarily for tests and operations."""
    with _CACHE_LOCK:
        _RESPONSE_CACHE.clear()


class SerpApiClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport
        self.bypass_cache = False

    def _cache_key(self, parameters: dict[str, Any]) -> str:
        api_key = self.settings.serpapi_key.get_secret_value()
        account_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
        transport_scope = str(id(self.transport)) if self.transport is not None else "default"
        key_payload = {
            "account": account_hash,
            "base_url": self.settings.serpapi_base_url,
            "parameters": parameters,
            "transport": transport_scope,
        }
        encoded = json.dumps(key_payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _cached_response(self, cache_key: str) -> dict[str, Any] | None:
        ttl = self.settings.serpapi_cache_ttl_seconds
        if ttl <= 0:
            return None
        now = time.monotonic()
        with _CACHE_LOCK:
            cached = _RESPONSE_CACHE.get(cache_key)
            if cached is None:
                return None
            stored_at, payload = cached
            if now - stored_at > ttl:
                del _RESPONSE_CACHE[cache_key]
                return None
            _RESPONSE_CACHE.move_to_end(cache_key)
            response = copy.deepcopy(payload)
        response["_marketsarthi_cache_hit"] = True
        return response

    def _store_response(self, cache_key: str, payload: dict[str, Any]) -> None:
        if self.settings.serpapi_cache_ttl_seconds <= 0:
            return
        clean_payload = copy.deepcopy(payload)
        clean_payload.pop("_marketsarthi_cache_hit", None)
        with _CACHE_LOCK:
            _RESPONSE_CACHE[cache_key] = (time.monotonic(), clean_payload)
            _RESPONSE_CACHE.move_to_end(cache_key)
            while len(_RESPONSE_CACHE) > self.settings.serpapi_cache_max_entries:
                _RESPONSE_CACHE.popitem(last=False)

    async def _search(self, **parameters: Any) -> dict[str, Any]:
        if not self.settings.has_serpapi:
            raise ServiceNotConfiguredError("SERPAPI_KEY is not configured")

        search_parameters = {
            **parameters,
            "output": "json",
        }
        cache_key = self._cache_key(search_parameters)
        cached = None if self.bypass_cache else self._cached_response(cache_key)
        if cached is not None:
            return cached

        params = {
            **parameters,
            "api_key": self.settings.serpapi_key.get_secret_value(),
            "output": "json",
        }
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            for attempt in range(2):
                try:
                    response = await client.get(self.settings.serpapi_base_url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    break
                except httpx.ReadTimeout:
                    if attempt == 1:
                        raise
                    await asyncio.sleep(0.25)

        if payload.get("error"):
            error = str(payload["error"])
            normalized_error = error.lower()
            no_results_markers = (
                "hasn't returned any results",
                "has not returned any results",
                "no results found",
            )
            if any(marker in normalized_error for marker in no_results_markers):
                payload = {key: value for key, value in payload.items() if key != "error"}
                self._store_response(cache_key, payload)
                return payload
            raise SerpApiError(error)
        self._store_response(cache_key, payload)
        return payload

    async def shopping(self, query: str, city: str | None = None) -> dict[str, Any]:
        parameters: dict[str, Any] = {
            "engine": "google_shopping",
            "q": query,
            "gl": "in",
            "hl": "en",
        }
        if city:
            parameters["location"] = city
        return await self._search(
            **parameters,
        )

    async def maps(self, query: str, city: str) -> dict[str, Any]:
        return await self._search(
            engine="google_maps",
            type="search",
            q=f"{query} in {city}",
            gl="in",
            hl="en",
        )

    async def maps_reviews(
        self,
        data_id: str,
        query: str | None = None,
        sort_by: str = "qualityScore",
    ) -> dict[str, Any]:
        parameters: dict[str, Any] = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "sort_by": sort_by,
            "hl": "en",
        }
        if query:
            parameters["query"] = query
        return await self._search(**parameters)

    async def trends(self, query: str, geo: str = "IN") -> dict[str, Any]:
        return await self._search(
            engine="google_trends",
            q=query,
            geo=geo,
            data_type="TIMESERIES",
            date="today 12-m",
            tz="-330",
            hl="en",
        )

    async def trends_by_region(
        self,
        query: str,
        geo: str = "IN",
        region: str = "CITY",
    ) -> dict[str, Any]:
        return await self._search(
            engine="google_trends",
            q=query,
            geo=geo,
            data_type="GEO_MAP_0",
            region=region,
            include_low_search_volume="true",
            hl="en",
        )

    async def web(self, query: str, city: str) -> dict[str, Any]:
        return await self._search(
            engine="google",
            q=f"{query} {city}",
            location=city,
            gl="in",
            hl="en",
            num=10,
        )

    async def news(self, query: str) -> dict[str, Any]:
        return await self._search(
            engine="google_news",
            q=query,
            gl="in",
            hl="en",
        )
