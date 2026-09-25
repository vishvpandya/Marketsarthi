# MarketSarthi

MarketSarthi is an evidence-first regional expansion copilot for Indian MSME and D2C merchants. It combines live market signals from SerpApi with DeepSeek V4.1 Flash synthesis to help a merchant compare cities, understand customer expectations, and design a small, measurable launch pilot.

It does **not** promise that a product will succeed. Every recommendation must expose its evidence, confidence, contradictions, and missing information.

## How MarketSarthi works

1. The merchant describes the product, business background, constraints, price range, and candidate cities.
2. The configured language model creates an editable research brief. The merchant reviews it before any live research begins.
3. MarketSarthi previews a bounded research plan, then uses SerpApi to collect product, price, local-shop, review, Trends, Search, and News observations.
4. Deterministic application rules normalize evidence, separate direct products from alternatives, expose failed searches, and calculate research coverage without treating it as demand.
5. DeepSeek—or Gemini when configured as a fallback—explains the evidence. Provider failure never destroys the collected observations.
6. The merchant reviews a decision summary, contacts possible shops, runs a small pilot, records measured results, and decides whether another bounded test is justified.

## Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| Web application | Next.js, React, TypeScript, plain CSS | Merchant inputs, evidence views, Copilot, pilot tracking, browser-local persistence and backup |
| API | FastAPI, Python, Pydantic | Validation, query planning, evidence normalization, deterministic calculations and provider orchestration |
| Search evidence | SerpApi | Google Shopping, Maps, Maps Reviews, Trends, Search and News results |
| Primary language model | DeepSeek V4.1 Flash | Research briefs, evidence-bound explanations, decision actions and pilot explanations |
| Optional fallback | Gemini | Structured generation when the primary provider is unavailable |
| Optional classifier | TypeSafe Jev | Confidence-gated classification of normalized Shopping results only |
| Local development | `uv`, npm, VS Code tasks | Reproducible Python and JavaScript setup on Windows |

## Repository guide

All Markdown files listed below are intentionally safe to publish. They contain documentation or coding-assistant guidance, not credentials.

| Path | What it contains | Who should read it |
|---|---|---|
| `README.md` | Public product overview, setup instructions, project map and safety rules | Everyone; start here |
| `PROJECT_CONTEXT.md` | Detailed living source of truth, current workflow, evidence rules, architecture decisions, limitations and dated change log | Developers and coding assistants continuing the project |
| `AGENTS.md` | Repository-level instructions requiring coding assistants to preserve documentation, secrets and evidence-safe claims | AI-assisted contributors |
| `docs/ARCHITECTURE.md` | Compact system data flow, trust boundary, API surface and external integrations | Technical reviewers and contributors |
| `docs/DAY_01.md` | Historical foundation plan and original vertical-slice definition | Contributors who want project history |
| `apps/web/AGENTS.md` | Next.js-generated compatibility guidance for coding assistants working in the web application | AI-assisted frontend contributors |
| `apps/web/CLAUDE.md` | Pointer applying the web agent guidance to compatible coding tools | AI-assisted frontend contributors |
| `.env.example` | Environment-variable names and safe defaults with every secret value blank | Developers configuring a local or deployed environment |
| `.gitignore` | Excludes real environment files, dependencies, caches, databases and generated metadata | Contributors reviewing repository safety |
| `.gitattributes` | Cross-platform text line-ending policy and binary-file declarations | Contributors using Windows, macOS or Linux |
| `.vscode/` | Shared editor settings, recommended extensions and runnable development tasks | VS Code users |
| `package.json` | Root commands for starting, testing, linting and building both applications | Developers running the monorepo |
| `apps/api/` | FastAPI source, provider clients, schemas, tests and Python lockfile | Backend contributors |
| `apps/api/app/main.py` | FastAPI application creation, middleware and router registration | Backend contributors |
| `apps/api/app/routers/` | HTTP health and research endpoints | API reviewers |
| `apps/api/app/schemas/research.py` | Typed contracts for merchants, plans, evidence, summaries, Copilot and pilots | Frontend and backend contributors |
| `apps/api/app/services/research.py` | Query planning, evidence collection, normalization, refresh and decision orchestration | Core research-engine contributors |
| `apps/api/app/services/copilot.py` | Copilot routing, evidence selection, source validation and safety checks | Copilot contributors |
| `apps/api/app/services/serpapi.py` | Bounded SerpApi client, retries and cache behavior | Search-integration contributors |
| `apps/api/tests/` | Automated backend behavior and safety coverage | Contributors verifying changes |
| `apps/web/` | Next.js application, dependency lockfile and frontend configuration | Frontend contributors |
| `apps/web/app/page.tsx` | Merchant workflow, result tabs, Copilot UI, persistence, backup and pilot workspace | Frontend contributors |
| `apps/web/app/globals.css` | Visual system and responsive layout | Frontend and design contributors |
| `data/.gitkeep` | Keeps the empty local-data directory in Git; generated databases remain ignored | Contributors running locally |

Generated folders and machine-specific output—such as `.env`, `node_modules`, `.venv`, `.next`, `*.egg-info`, `*.tsbuildinfo`, caches and local databases—must never be committed.

## Current capabilities

- Secure, validated environment configuration
- FastAPI backend with health and readiness endpoints
- Typed merchant, research-plan, evidence, and report contracts
- Query-plan preview that works without paid API calls
- Live evidence research using Google Shopping, Maps, Maps Reviews, Trends, Search and News through SerpApi
- Product-first Google Shopping fallback ladder with India-wide recovery when city-localized search is empty
- Visible SerpApi tool trace showing engine, query, scope, status and result count
- Visible evidence check times, including an old-research warning after seven days and timestamps in downloaded pilot reports
- One bounded retry for transient SerpApi read timeouts, with true no-result responses kept separate from failures
- Merchant background and expansion-goal capture
- DeepSeek-generated, merchant-editable research briefs with facts and assumptions separated
- Direct, alternative, and uncertain competitor grouping with visible reasons
- Optional TypeSafe Jev classification for Shopping evidence, with confidence gating, visible provenance, and automatic fallback to the existing classifier
- Google Maps businesses presented as potential retail channels, never assumed competitors
- Clickable SerpApi engine tabs that separate Google Shopping and Google Maps research queries
- Wider, product-aware Maps channel discovery with deduplication and bounded review verification
- AI-independent City Evidence Scorecard with price-band signals, evidence gaps, and next actions
- Editable local-template brief fallback when all configured AI providers are exhausted
- Explicit city-local, India-wide online, and named-business review evidence scopes
- Source-linked Customer Voice excerpts with bounded, deterministic topic tags
- Google Trends evidence for 12-month relative interest and returned city comparisons
- Localized Google Search evidence with conservative city-specific labeling
- An 18-angle Google Search and Google News investigation covering product, category, events, channels, competition, policy, schemes, supply, and customer context
- Coverage-aware News execution with URL deduplication, at least six attempted angles, and conservative city labeling
- Human-style business questions with multiple bounded query wordings and transparent answer status
- Adaptive Shopping fallbacks plus six fixed Search angles for availability, channels, brands, prices, events, and official support pages
- One-hour process-local SerpApi response cache with visible cache reuse and configurable limits
- Targeted cache-bypassing refresh for Shopping, Maps with Reviews, Trends, Web Search, or News while preserving the rest of the workspace
- Merchant-triggered final decision summary with deterministic facts and gaps, AI-written next actions, and a local fallback
- Floating workspace-aware Copilot that answers from saved evidence, cites matching sources and check times, and guides the merchant to the correct refresh control without triggering paid searches
- Browser-persistent Copilot preferred-name memory with internal evidence IDs hidden from merchant-facing answers
- Research-aware Copilot quick questions that use the current city or offer a bounded comparison when several cities were researched
- Deterministic Copilot fallback for greetings, evidence questions, and next-step guidance when the configured AI is unavailable or unsafe
- Transparent multi-city evidence comparison without a hidden demand or success score
- Merchant-controlled shop-pilot planning with editable quantities, price, duration, and success checks
- Merchant-approved outreach shortlists built from source-linked Google Maps leads, with verified review mentions separated from unconfirmed shops
- Merchant-entered retailer outreach tracking with per-shop status and contact notes
- Shop-by-shop pilot measurement for confirmed retailers with validated placement, sales, returns and continuation records
- Per-shop bought, returned, damaged, missing and still-at-shop reconciliation with one-click copying into overall pilot totals
- Deterministic post-pilot review that checks stock accounting, merchant-defined targets, and retailer continuation before assigning a bounded next action
- AI explanation of the fixed pilot outcome with a local rule-based fallback when providers are unavailable
- Optional merchant-entered pilot cash check with a deterministic acceptable-loss comparison and explicit non-accounting caveats
- Browser-local history for up to 12 completed pilot rounds, with a non-causal comparison of the latest two tests
- Merchant-controlled removal of mistaken or duplicate saved pilot rounds, with confirmation before deletion
- One-main-change tracking for repeated rounds so merchants can document what they intentionally varied without turning correlation into causation
- Versioned JSON workspace backup and validated restore without exporting API keys
- Separate planned and actual units so measured rates use the real pilot denominator
- Optional actual-result entry with transparent sell-through and return-rate calculations
- Plain-language packet tracking for products given to shops, bought by customers, returned, damaged, missing, or still at a shop
- Full stock reconciliation that pauses recommendations for missing or unfinished counts and requests a corrective retest when damage is recorded
- Downloadable, source-linked Markdown pilot reports without invented forecasts
- Browser-local workspace autosave that restores completed research and pilot drafts after refresh without storing API keys
- Plain-English merchant labels and short explanations while preserving technical evidence details
- Multipack price normalization per pack and per 100 g when listing data allows it
- DeepSeek V4.1 Flash non-thinking synthesis with validated JSON output and optional Gemini fallback
- Next.js research workspace with the khakhra example preloaded
- Two clear frontend workspaces: prepare the research first, then review the decision, evidence, and pilot in focused tabs
- Backend tests for configuration, validation, and preview generation

## Quick start

1. Copy `.env.example` to `.env` and add your private keys.
2. Synchronize the API environment with `uv`:

   ```powershell
   uv --cache-dir apps/api/.uv-cache sync --project apps/api --extra dev
   ```

3. Install the web dependencies:

   ```powershell
   npm --prefix apps/web install
   ```

4. Start the API:

   ```powershell
   npm run dev:api
   ```

5. Start the web app in a second terminal:

   ```powershell
   npm run dev:web
   ```

Open `http://localhost:3000`. API documentation is available at `http://localhost:8000/docs`.

## VS Code on Windows

Open the repository folder itself, not only `apps/web` or `apps/api`:

```powershell
code "C:\Users\vishw\OneDrive\Documents\ChatGPT\SerpAI Hackathon"
```

The committed VS Code settings select `apps/api/.venv/Scripts/python.exe`, enable pytest, and recommend the Python, Ruff, and ESLint extensions.

Use **Terminal → New Terminal** for a PowerShell terminal. The most useful commands are:

```powershell
npm run dev:api
npm run dev:web
npm run test:api
npm run lint:api
npm run lint:web
npm run build:web
```

Alternatively, use **Terminal → Run Task** and select `MarketSarthi: Start API`, `MarketSarthi: Start Web`, or `MarketSarthi: Start Full Stack`.

## Security

- Never put DeepSeek, Gemini or SerpApi keys in `apps/web`.
- Never prefix secret values with `NEXT_PUBLIC_`.
- The committed `.env.example` contains names only, never credentials.
- If a credential is accidentally committed or shared, rotate it immediately.

Start with `PROJECT_CONTEXT.md` for the living product and technical state. Historical detail is in `docs/DAY_01.md` and `docs/ARCHITECTURE.md`.
