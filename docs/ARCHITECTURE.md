# MarketSarthi architecture

## Product boundary

MarketSarthi is a decision-support system, not a sales forecaster. It converts public market signals into a transparent expansion hypothesis and pilot plan.

## Data flow

```text
Merchant profile
      |
      v
Product-first query planner
      |
      v
SerpApi Google Shopping fallback ladder ----> direct-product evidence
      |                                               |
      +---- SerpApi Google Maps ----------------> potential channels
                                                      |
                                                      v
                     normalizers + optional Jev Shopping classification
                                      + tool trace + evidence ledger
                                                      |
                                                      v
                                  DeepSeek evidence synthesis
                                   (Gemini optional fallback)
                                                      |
                                                      v
                           cited recommendation + confidence + caveats
```

TypeSafe Jev is an optional post-retrieval classifier. It receives the merchant product/category and normalized Shopping titles, returns only typed direct/alternative/uncertain choices with confidence, and cannot create searches or merchant-facing prose. MarketSarthi applies only answers above its configured threshold. Any unavailable or low-confidence answer keeps the existing classification, so Jev can be disabled by removing `TYPESAFE_API_KEY`.

The Next.js interface presents this flow in two local UI workspaces. **Prepare research** contains merchant input, brief approval, and non-paid plan preview. A completed live analysis opens **Results & pilot**, whose Overview, Evidence, and Pilot tabs selectively present the same in-memory response and browser-local workspace. These tabs do not change API order, schemas, evidence, or pilot state.

## Trust rules

1. SerpApi results are observations, not conclusions.
2. Every externally sourced claim carries a URL and retrieval time.
3. The configured AI provider receives normalized evidence rather than unbounded raw responses.
4. Scores are calculated in application code and explained by the AI provider.
5. Missing evidence lowers confidence; it is never silently replaced by model knowledge.
6. A failed LLM call does not destroy collected evidence.
7. Retrieval timestamps mean when an observation was normalized into the report, not when its source was published or last updated. A cache hit may reuse a provider response within the configured cache lifetime.

## Current API surface

| Endpoint | Purpose | External cost |
|---|---|---:|
| `GET /api/v1/health/live` | Process liveness | None |
| `GET /api/v1/health/ready` | Credential readiness | None |
| `POST /api/v1/research/brief` | Generate an editable merchant research brief | DeepSeek; optional Gemini fallback |
| `POST /api/v1/research/preview` | Validate input and inspect the query plan | None |
| `POST /api/v1/research/analyze` | Live research and optional synthesis | SerpApi + DeepSeek; optional Gemini fallback |
| `POST /api/v1/research/refresh` | Refresh selected evidence engines without resetting other research or pilot state | SerpApi for selected groups only |
| `POST /api/v1/research/decision-summary` | Deterministic facts and gaps with optional AI-written next actions | DeepSeek; optional Gemini or local-rule fallback |
| `POST /api/v1/research/copilot` | Answer from the supplied workspace, whitelist matching sources, and guide the relevant refresh | DeepSeek; optional Gemini or local workspace fallback; no SerpApi call |
| `POST /api/v1/research/pilot-review` | Deterministic pilot and optional cash checks, followed by a bounded explanation | DeepSeek; optional Gemini or local-rule fallback |

## Planned SerpApi expansion

| Phase | Engine | Signal |
|---|---|---|
| Day 1 | `google_shopping` | price, rating, product positioning |
| Day 1 | `google_maps` | potential local sellers and retail channels |
| Day 2 | `google_maps_reviews` | complaints, expectations, product attributes |
| Day 2 | `google_trends` | demand direction and geographic comparison |
| Day 3 | `google` | supporting market evidence and discovery |
| Day 3 | `google_news` | recent category or regulatory events |
