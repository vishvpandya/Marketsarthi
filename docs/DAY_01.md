# Day 1 — Foundation and vertical slice

## Goal

Finish the day with a runnable product path from merchant input to a research plan and, when keys are configured, live Shopping and Maps evidence plus a Gemini-generated brief.

## Three-to-six-hour schedule

### Hour 1 — Foundation

- Confirm repository and runtime versions.
- Create the web/API monorepo structure.
- Add secure environment handling and startup validation.
- Add health and readiness endpoints.

### Hour 2 — Domain contract

- Model the merchant profile, SKU, city targets, constraints, research plan, evidence item, and analysis result.
- Add validation for realistic prices, city count, and required fields.
- Define exactly what is evidence and what is an inference.

### Hours 3–4 — First vertical slice

- Generate a deterministic research plan.
- Call Google Shopping and Google Maps through SerpApi.
- Normalize their different response shapes into evidence cards.
- Ask Gemini 3.8 Flash to produce an evidence-bound brief.
- Continue to return evidence if Gemini is unavailable.

### Hours 5–6 — Interface and verification

- Build the merchant input workspace and analysis-state UI.
- Connect it to preview and live-analysis endpoints.
- Run backend tests and a frontend production build.
- Document commands, missing credentials, and Day 2 scope.

## Definition of done

- `GET /api/v1/health/live` returns successfully.
- `GET /api/v1/health/ready` explains which external services are configured.
- `POST /api/v1/research/preview` produces queries without consuming credits.
- `POST /api/v1/research/analyze` returns Shopping and Maps evidence when SerpApi is configured.
- Gemini synthesis is evidence-only and never hides its source URLs.
- No secret is present in source control or browser code.
- Tests and the frontend production build pass.

## Day 2 entry criteria

Day 2 starts only after the two live integrations pass. It adds Maps Reviews, Trends, evidence quality scoring, caching, and the first transparent city-ranking formula.
