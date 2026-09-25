import httpx

from app.core.config import Settings
from app.services.serpapi import SerpApiClient, clear_serpapi_cache


async def test_shopping_request_is_localized_and_authenticated() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["engine"] == "google_shopping"
        assert params["location"] == "Kolkata"
        assert params["gl"] == "in"
        assert params["api_key"] == "test-serp-key"
        return httpx.Response(200, json={"shopping_results": []})

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.shopping("roasted khakhra 200 g", "Kolkata")

    assert response == {"shopping_results": []}


async def test_maps_reviews_uses_listing_data_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["engine"] == "google_maps_reviews"
        assert params["data_id"] == "test-data-id"
        assert params["sort_by"] == "qualityScore"
        assert params["query"] == "khakhra"
        return httpx.Response(200, json={"reviews": []})

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.maps_reviews("test-data-id", query="khakhra")

    assert response == {"reviews": []}


async def test_shopping_can_use_india_wide_scope_without_location() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["engine"] == "google_shopping"
        assert "location" not in params
        assert params["gl"] == "in"
        return httpx.Response(200, json={"shopping_results": []})

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.shopping("khakhra")

    assert response == {"shopping_results": []}


async def test_trends_requests_time_series_for_india() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["engine"] == "google_trends"
        assert params["q"] == "khakhra"
        assert params["geo"] == "IN"
        assert params["data_type"] == "TIMESERIES"
        assert params["date"] == "today 12-m"
        assert params["tz"] == "-330"
        return httpx.Response(200, json={"interest_over_time": {"timeline_data": []}})

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.trends("khakhra")

    assert response == {"interest_over_time": {"timeline_data": []}}


async def test_trends_by_region_requests_city_comparison() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["engine"] == "google_trends"
        assert params["data_type"] == "GEO_MAP_0"
        assert params["region"] == "CITY"
        assert params["include_low_search_volume"] == "true"
        return httpx.Response(200, json={"interest_by_region": []})

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.trends_by_region("khakhra")

    assert response == {"interest_by_region": []}


async def test_web_search_is_localized_to_candidate_city() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["engine"] == "google"
        assert params["q"] == "Roasted methi khakhra Kolkata"
        assert params["location"] == "Kolkata"
        assert params["gl"] == "in"
        assert params["num"] == "10"
        return httpx.Response(200, json={"organic_results": []})

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.web("Roasted methi khakhra", "Kolkata")

    assert response == {"organic_results": []}


async def test_google_news_uses_visible_bounded_query() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["engine"] == "google_news"
        assert params["q"] == "khakhra Kolkata"
        assert params["gl"] == "in"
        assert params["hl"] == "en"
        return httpx.Response(200, json={"news_results": []})

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.news("khakhra Kolkata")

    assert response == {"news_results": []}


async def test_no_results_provider_message_becomes_empty_search() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "search_metadata": {"status": "Success"},
                "error": "Google News hasn't returned any results for this query.",
            },
        )

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.news("rare product Kolkata")

    assert response == {"search_metadata": {"status": "Success"}}


async def test_read_timeout_is_retried_once() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout("temporary timeout", request=request)
        return httpx.Response(200, json={"organic_results": []})

    settings = Settings(serpapi_key="test-serp-key", _env_file=None)
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    response = await client.web("khakhra", "Kolkata")

    assert response == {"organic_results": []}
    assert attempts == 2


async def test_identical_search_reuses_process_local_cache() -> None:
    clear_serpapi_cache()
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200,
            json={"organic_results": [{"title": "Cached result"}]},
        )

    settings = Settings(
        serpapi_key="test-serp-key",
        serpapi_cache_ttl_seconds=3600,
        _env_file=None,
    )
    client = SerpApiClient(settings, transport=httpx.MockTransport(handler))

    first = await client.web("cache test product", "Kolkata")
    second = await client.web("cache test product", "Kolkata")

    assert attempts == 1
    assert "_marketsarthi_cache_hit" not in first
    assert second["_marketsarthi_cache_hit"] is True
    assert second["organic_results"] == [{"title": "Cached result"}]
    clear_serpapi_cache()
