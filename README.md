<div align="center">
MarketSarthi

Evidence-first regional expansion copilot for Indian MSMEs and D2C
merchants

Research → Compare → Verify → Pilot → Measure → Learn

</div>
# MarketSarthi

Evidence-first regional expansion copilot for Indian MSMEs and D2C
merchants.

Research → Compare → Verify → Pilot → Measure → Learn

Quick Navigation

System Workflow

Architecture at a Glance

Evidence Sources

Evidence → Decision Design

TypeSafe Jev Integration

City Evidence Scorecard

MarketSarthi Copilot

Pilot Workflow

Technology Stack

Repository Architecture

Run Locally

Security

MarketSarthi helps a merchant turn product facts and business context
into a transparent, source-linked market hypothesis and a small,
measurable real-world pilot.

It does not promise that a product or city will succeed. Instead, it
collects public market signals, separates evidence from assumptions,
exposes research gaps and contradictions, and helps the merchant decide
what to test next.

Core idea:

Research → Understand → Verify → Pilot → Measure → Learn

System Workflow

The complete product journey is shown below. GitHub renders the
following Mermaid diagrams directly from the fenced mermaid blocks.

flowchart TD
    A["Merchant Input<br/>Product • Category • Price • Pack Size<br/>Business Story • Constraints • Candidate Cities"] --> B["AI Research Brief<br/>DeepSeek V4.1 Flash"]
    B --> C{"Merchant Reviews Brief"}
    C -->|Edit| B
    C -->|Approve| D["Research Plan Preview<br/>No Paid API Calls"]
    D --> E["Start Live Research"]

    subgraph EVIDENCE["Live Evidence Collection — SerpApi"]
        direction TB
        E --> S1["Google Shopping<br/>Products • Brands • Prices • Packs"]
        E --> S2["Google Maps<br/>Potential Local Shops"]
        E --> S3["Google Maps Reviews<br/>Product Mentions • Customer Voice"]
        E --> S4["Google Trends<br/>12-Month Interest • City Comparison"]
        E --> S5["Google Search<br/>Sellers • Distributors • Events • Schemes"]
        E --> S6["Google News<br/>Market • Events • Retail • Policy • Supply"]
    end

    S1 --> N["Evidence Processing<br/>Normalize • Deduplicate • Scope • Timestamp"]
    S2 --> N
    S3 --> N
    S4 --> N
    S5 --> N
    S6 --> N
    N --> J{"TypeSafe Jev<br/>Configured?"}
    J -->|High Confidence| JC["Shopping Classification<br/>Direct • Alternative • Uncertain"]
    J -->|Unavailable / Low Confidence / Failed| FC["Keep Existing Classification"]
    JC --> SC["Deterministic City Evidence Scorecard"]
    FC --> SC
    SC --> AI["Evidence-Bound AI Synthesis<br/>DeepSeek Primary • Gemini Fallback"]
    AI --> R["Results & Pilot Workspace"]

    R --> O["Decision Overview<br/>Observed • Unknown • Next Action • Limits"]
    R --> EV["Evidence & Sources<br/>Plan • Tool Trace • Evidence Ledger"]
    R --> CP["MarketSarthi Copilot<br/>Answers from Saved Evidence"]
    R --> RF{"Need New Evidence?"}
    RF -->|Yes| REF["Targeted Refresh<br/>Shopping • Maps/Reviews • Trends<br/>Search • News"]
    REF --> E
    RF -->|No| CITY["Choose Researched City"]
    CITY --> P["Plan Small Pilot<br/>Duration • Quantity • Shops<br/>Test Price • Merchant Thresholds"]
    P --> SH["Select Potential Shops<br/>Google Maps Leads"]
    SH --> OUT["Merchant Outreach<br/>Not Contacted → Contacted<br/>Interested → Confirmed / Declined"]
    OUT --> TEST["Run Real-World Pilot"]
    TEST --> MEAS["Record Results<br/>Bought • Returned • Damaged<br/>Missing • Still at Shop"]
    MEAS --> REVIEW["Deterministic Pilot Review"]
    REVIEW --> EX["AI / Local Explanation<br/>AI Cannot Change Calculated Outcome"]
    EX --> SUM["Final Decision Summary<br/>Observed • Unknown • Next Step<br/>What Not to Conclude"]
    SUM --> SAVE["Save Pilot Round"]
    SAVE --> HISTORY["Pilot History<br/>Up to 12 Saved Rounds"]
    HISTORY --> COMP["Compare Latest Two Rounds<br/>Measured Changes Only"]
    COMP --> CHANGE["Choose Main Planned Change<br/>Repeat • Price • Pack • Product<br/>Shop Type • Display • Other"]
    CHANGE --> NEXT["Start Next Bounded Test"]
    NEXT --> P
    SUM --> REPORT["Download Markdown Pilot Report<br/>Evidence • Sources • Pilot Results"]
    R --> BACKUP["JSON Workspace Backup"]
    BACKUP --> RESTORE["Validated Workspace Restore"]
    RESTORE --> R
    CP --> ROUTE["Deterministic Intent Routing"]
    ROUTE --> ANSWER["Evidence-First Answer<br/>Whitelisted Sources + Check Time"]
    ANSWER --> GUIDE["Refresh Guidance When Evidence Is Old"]
    GUIDE --> REF

Architecture at a Glance

This smaller diagram shows the main technical path behind the product.

flowchart LR
    A["Merchant"] --> B["MarketSarthi"]
    B --> C["AI Research Brief"]
    C --> D["SerpApi<br/>6 Evidence Engines"]
    D --> E["Evidence Processing<br/>Normalize • Deduplicate • Scope"]
    E --> F["TypeSafe Jev<br/>Optional Shopping Classification"]
    F --> G["Deterministic Rules<br/>Scorecard • Validation • Pilot Outcome"]
    G --> H{"AI Synthesis"}
    H --> I["DeepSeek V4.1 Flash<br/>Primary"]
    H --> J["Gemini<br/>Optional Fallback"]
    I --> K["Results"]
    J --> K
    K --> L["Small Real-World Pilot"]
    L --> M["Measured Results"]
    M --> G

What is MarketSarthi?

Small merchants often want to enter a new city but cannot afford
conventional market research.

MarketSarthi organizes publicly observable signals into a research
workflow. It can collect:

Similar products, brands, prices and pack sizes

Potential local retail channels

Product-specific review mentions

Relative Google Trends interest

Seller, distributor and event information

Recent market, retail, policy and supply context

The system then separates those observations by evidence scope,
highlights gaps and contradictions, and helps the merchant design a
bounded pilot.

The running demonstration uses a family-run roasted methi khakhra
business in Bolpur considering Kolkata. The architecture is product- and
region-aware, so the same workflow can be used for other products and
candidate markets.

What MarketSarthi Does Not Do

MarketSarthi does not:

Promise market success

Treat Google Trends as demand or sales

Treat news coverage as proof of demand

Treat Maps businesses as confirmed distributors

Treat a review mention as proof of current stock

Treat an evidence-coverage percentage as a success probability

Let an AI model override deterministic pilot calculations

Turn a successful small pilot into proof of city-wide demand

The product is designed around evidence, uncertainty and controlled
experimentation.

How It Works

Prepare

The merchant enters the product, category, current market, candidate
cities, price range, pack size, differentiators, business background and
expansion goal.

Build the research brief

DeepSeek V4.1 Flash creates an editable research brief. Gemini can be
configured as a fallback. If configured AI providers are unavailable,
MarketSarthi can create an editable local template from the merchant's
information.

The merchant reviews and approves the brief before live research.

Preview the research plan

Preview mode shows the planned business questions, regions, engines and
call budget without using paid search calls.

Run live research

SerpApi collects bounded evidence through:

Google Shopping

Google Maps

Google Maps Reviews

Google Trends

Google Search

Google News

Every planned query has a business question and an execution status.

Process and explain the evidence

MarketSarthi normalizes and deduplicates results, records evidence scope
and check time, separates direct/alternative/uncertain Shopping matches,
and calculates deterministic city evidence coverage.

TypeSafe Jev is optional and confidence-gated for Shopping
classification only.

DeepSeek is the primary synthesis path. Gemini can be used as a
fallback. AI explains the collected evidence but does not replace
deterministic application rules.

Test instead of guessing

After research, the merchant can select a researched city, choose
potential shops, track outreach and run a small pilot.

The merchant records actual results. MarketSarthi calculates the pilot
outcome using deterministic rules and can ask the configured AI to
explain the fixed result and propose one bounded next experiment.

Evidence Sources

Source                              What it provides

Google Shopping                     Products, brands, prices, packs,
ratings and positioning

Google Maps                         Potential local retail channels

Google Maps Reviews                 Bounded product-specific review
mentions

Google Trends                       Relative search interest over time
and by returned city

Google Search                       Sellers, distributors, events,
official pages and schemes

All six surfaces are accessed through SerpApi.

Evidence Scopes

Every evidence item is assigned one of three scopes:

city_local

india_wide_online

business_review

A city-specific label requires the city to appear clearly in the title,
snippet or displayed URL where applicable.

Evidence → Decision Design

MarketSarthi deliberately separates retrieval, deterministic logic and
AI explanation.

flowchart TD
    A["External Evidence"] --> B["Normalize + Deduplicate"]
    B --> C["Deterministic Rules"]
    C --> D["AI Explanation"]
    D --> E["Merchant Decision"]

This means the language model is not responsible for deciding whether
the city will succeed.

For example:

Google Trends = relative search interest NOT Google Trends = number of
buyers

Likewise:

Evidence coverage = research completeness NOT Evidence coverage =
probability of success

And:

Pilot checks met = merchant-defined experiment criteria NOT Pilot checks
met = city-wide market validation

TypeSafe Jev Integration

Jev is an optional classification layer for Google Shopping evidence.

flowchart TD
    A["SerpApi Shopping Results"] --> B["Normalization"]
    B --> C["Jev Classification"]
    C --> D{"Confidence Check"}
    D -->|High confidence| E["Use Jev decision"]
    D -->|Low / Failed| F["Keep existing classification"]

Jev:

Does not search the web

Does not replace SerpApi

Does not change prices

Does not decide market success

Does not classify Maps, Trends, Search or News

Only replaces an existing Shopping label when the configured confidence
threshold is met

The current default confidence threshold is 0.65.

City Evidence Scorecard

The deterministic scorecard compares research coverage across cities
without ranking them by predicted success.

The coverage checks include:

At least three same-product listings

At least one usable same-product price

At least five local shops to check

At least one shop with a product-specific review mention

At least one city-specific web result

A returned Google Trends row for the candidate city

A higher coverage percentage means fewer research gaps. It does not mean
stronger demand, a better market or a higher probability of success.

When multiple cities are researched, MarketSarthi preserves the
merchant's city order and shows the same evidence dimensions side by
side.

Research Budget

MarketSarthi intentionally uses bounded query planning.

For one candidate city, the maximum planned SerpApi usage is:

Engine                                  Maximum calls

Google Shopping                                     5
Google Maps                                         5
Google Maps Reviews                                 3
Google Search                                       6
Google News                                        12
Google Trends                      2 overall requests
Worst-case one-city budget                 33

Some research groups can stop early when their evidence threshold is
already satisfied.

Identical successful SerpApi requests can also reuse a process-local
cache for up to one hour by default. Merchant-triggered targeted
refreshes bypass that cache.

MarketSarthi Copilot

The floating Copilot answers questions from the current saved workspace.

It does not start a new SerpApi search.

The Copilot uses deterministic intent routing:

Merchant Question ↓ Intent Routing ↓
┌────────────┬────────────┬─────────────┐ ↓ ↓ ↓ ↓ Prices Shops Reviews
Trends/Search/News ↓ ↓ ↓ ↓ Shopping Maps Customer Matching Evidence +
Reviews Voice Evidence   | | /   | | /
└─────┴──────────┴───────────┘ ↓ Evidence-First Answer ↓ Whitelisted
Source Links + Check Time

The Copilot can explain:

Saved prices

City findings

Shop leads

Review observations

Trends

Web evidence

News

Evidence gaps

Next steps

If newer evidence is needed, it guides the merchant to the appropriate
targeted refresh instead of silently performing a paid search.

The Pilot Workflow

Research is only the beginning.

After live research, the merchant can choose a researched city and
define a small test.

Pilot Plan

The merchant controls:

Test duration

Planned quantity

Participating shops

Test price

Target percentage of packets bought

Maximum acceptable returned percentage

MarketSarthi does not invent these values.

Shop Outreach

Potential Google Maps leads can be shortlisted for outreach.

Each shop has a merchant-controlled status:

flowchart LR
    A["Not contacted"] --> B["Contacted"] --> C["Interested"]
    C --> D["Confirmed"]
    C --> E["Declined"]

A confirmed status means the merchant recorded that the retailer agreed
to the bounded pilot. It is not inferred from Maps, reviews or AI.

Shop-Level Measurements

For confirmed shops, the merchant can record:

Packets given

Packets bought

Packets returned

Packets damaged

Packets missing

Packets still at the shop

Whether the shop wants another batch

Learning notes

Every packet must be accounted for.

Deterministic Pilot Review

MarketSarthi calculates the measured pilot percentages from actual
merchant-entered results.

Packets bought ÷ Actual packets given × 100

and:

Packets returned ÷ Actual packets given × 100

The application checks the merchant's own thresholds.

Possible deterministic outcomes are:

Outcome Meaning

continue_small_test Merchant-defined percentage checks and optional
money check are met, with at least one shop asking for another batch

modify_and_retest Some checks are met, or the optional money check
exceeds the accepted test loss

investigate_before_next_test Stock is incomplete/conflicting, or
percentage checks pass without a shop asking for another batch

These are experiment-management outcomes, not market-success grades.

AI can explain the calculated outcome, but it cannot change the
underlying facts or outcome.

Optional Money Check

The merchant can optionally enter:

Money received during the test

Test costs already spent and not recoverable

Maximum acceptable test loss

MarketSarthi calculates:

Cash result = Money received − Non-recoverable test costs

This is intentionally a simple test-level cash check.

It is not presented as:

Accounting profit

ROI

Margin

Unit economics

Long-term viability

A forecast

Repeated Pilot Rounds

After a completed review, the merchant can save the round.

Up to 12 rounds are retained in the browser workspace.

From the second round onward, the merchant records one main planned
change:

Repeat the same test

Price

Pack size

Product / recipe

Shop type

Display / message

Another change

MarketSarthi compares the latest two rounds using measured changes.

It does not claim that the selected change caused the difference.

flowchart TD
    A["Round 1"] --> B["Measure"] --> C["Review"] --> D["Choose Planned Change"]
    D --> E["Round 2"] --> F["Measure"] --> G["Compare Observed Changes"] --> H["Choose Next Test"]
    H --> E

Results, Refresh and Evidence Freshness

After live research, the merchant can refresh only the evidence group
that needs updating:

Shopping

Maps + Reviews

Trends

Web Search

News

A targeted refresh:

Bypasses the local cache

Re-runs only the selected evidence group

Preserves the rest of the workspace

Clears stale final synthesis

Keeps the pilot and merchant workspace intact

Refresh everything updates all five groups without resetting the
workspace.

Every live observation has a check time.

A check time means when MarketSarthi observed the evidence. It is not
the source publication date and does not guarantee that a price,
listing, article or shop detail is still current.

Workspace Persistence

MarketSarthi saves the current workspace in browser-local storage.

Saved state includes:

Merchant form

Approved brief

Research results

Pilot draft

Shop shortlist

Outreach records

Shop measurements

Current review

Copilot history

Saved pilot rounds

This means a browser refresh does not automatically require another paid
research run.

JSON Backup

The complete workspace can be exported as a versioned JSON backup.

Restore validates:

MarketSarthi/version marker

Core workspace structure

File size

Secret-like fields

Stored URL protocols

API keys and server environment variables are never exported.

Browser-local storage is not account-backed persistence and does not
synchronize across devices or users.

Technology Stack

Layer                   Technology              Role

Frontend                Next.js, React,         Merchant workflow,
TypeScript, CSS         research views, Copilot
and pilot workspace

Backend                 FastAPI, Python,        API contracts,
Pydantic, HTTPX         planning, evidence
processing and
deterministic logic

Market evidence         SerpApi                 Shopping, Maps,
Reviews, Trends, Search
and News

Primary LLM             DeepSeek V4.1 Flash     Research briefs and
evidence-bound
synthesis

Fallback LLM            Gemini                  Optional
structured-generation
fallback

Optional classifier     TypeSafe Jev            Confidence-gated
Shopping classification

Python environment      uv                      Dependency and
environment management

Repository Architecture

flowchart TB
    ROOT["MarketSarthi"]
    ROOT --> APPS["apps/"]
    ROOT --> DOCS["docs/"]
    ROOT --> ROOTFILES["Root Configuration & Docs"]

    APPS --> API["api/"]
    APPS --> WEB["web/"]
    API --> APIAPP["app/"]
    API --> TESTS["tests/"]
    APIAPP --> ROUTERS["routers/"]
    APIAPP --> SCHEMAS["schemas/"]
    APIAPP --> SERVICES["services/"]

    ROUTERS --> R1["research.py"]
    SCHEMAS --> S1["research.py"]
    SERVICES --> SR["research.py"]
    SERVICES --> CP["copilot.py"]
    SERVICES --> SP["serpapi.py"]
    SERVICES --> DS["deepseek.py"]
    SERVICES --> GE["gemini.py"]
    SERVICES --> LLM["llm.py"]
    SERVICES --> JV["jev.py"]
    SERVICES --> PR["pilot_review.py"]

    WEB --> WEBAPP["app/"]
    WEBAPP --> PAGE["page.tsx"]
    WEBAPP --> CSS["globals.css"]

    DOCS --> AD["ARCHITECTURE.md"]
    DOCS --> D1["DAY_01.md"]

    ROOTFILES --> PC["PROJECT_CONTEXT.md"]
    ROOTFILES --> AG["AGENTS.md"]
    ROOTFILES --> ENV[".env.example"]
    ROOTFILES --> GI[".gitignore"]
    ROOTFILES --> GA[".gitattributes"]
    ROOTFILES --> PKG["package.json"]
    ROOTFILES --> RD["README.md"]

Important Backend Files

File                                      Purpose

apps/api/app/services/research.py       Query planning, evidence
collection, normalization, refresh
and orchestration

apps/api/app/services/copilot.py        Copilot routing, evidence selection
and source validation

apps/api/app/services/serpapi.py        SerpApi integration, retries and
caching

apps/api/app/services/deepseek.py       DeepSeek structured-output adapter

apps/api/app/services/gemini.py         Optional Gemini fallback

apps/api/app/services/jev.py            Optional TypeSafe Jev integration

Important Frontend Files

File                                Purpose

apps/web/app/page.tsx             Merchant workflow, results,
Copilot, persistence and pilot
workspace

apps/web/app/globals.css          Visual system and responsive layout

API Endpoints

Endpoint                                   Purpose

POST /api/v1/research/brief              Generate editable research brief

POST /api/v1/research/preview            Generate research plan without paid
search calls

POST /api/v1/research/analyze            Run live evidence research

POST /api/v1/research/refresh            Refresh selected evidence groups

POST /api/v1/research/decision-summary   Generate evidence-safe final
summary

POST /api/v1/research/copilot            Answer from supplied workspace
evidence

POST /api/v1/research/pilot-review       Calculate and explain pilot outcome

GET /health                              Application health

Readiness routes                           Provider/configuration readiness

Run MarketSarthi Locally

Prerequisites

You need:

Python 3.11+

uv

Node.js / npm

VS Code recommended for the quickest local run

1. Configure Environment Variables

Copy .env.example to .env:

cp .env.example .env

Required for the full live workflow:

SERPAPI_KEY=
DEEPSEEK_API_KEY=

Optional:

GEMINI_API_KEY=
TYPESAFE_API_KEY=

Do not put real keys in:

apps/web

frontend source code

screenshots

commits

README files

Quickest Way: VS Code

If you are a judge or a new contributor, you can use the committed VS
Code tasks.

Step 1 --- Open the repository

Open the repository root in VS Code.

Do not open only apps/web or apps/api.

Step 2 --- Open Command Palette

Press:

Ctrl + Shift + P

Search:

Tasks: Run Task

Then select:

MarketSarthi: Start Full Stack

This starts the frontend and backend development workflow.

Step 3 --- Open the application

Open:

http://localhost:3000

FastAPI documentation:

http://localhost:8000/docs

Other available VS Code tasks

MarketSarthi: Start API MarketSarthi: Start Web MarketSarthi: Start Full
Stack

This is the recommended path for a quick project demonstration.

Terminal Setup

If you prefer the terminal:

Install the API environment

uv --cache-dir apps/api/.uv-cache sync --project apps/api --extra dev
npm --prefix apps/web install
npm run dev:api

Open a second terminal for the web application:

npm run dev:web

Then open:

http://localhost:3000

Verification

Before submitting changes, run:

npm run test:api
npm run lint:api
npm run lint:web
npm run build:web

If a Windows preview process locks the normal .next directory,
production-build verification can use:

$env = ".next-build-check" npm run build

Judge / Demo Flow

Once the application is running:

flowchart TD
    A["1. Enter merchant + product information"] --> B["2. Generate research brief"] --> C["3. Review / edit / approve"] --> D["4. Preview research plan"] --> E["5. Start live research"]
    E --> F["6. Inspect evidence + tool trace"] --> G["7. Review decision overview"] --> H["8. Choose a researched city"] --> I["9. Plan a small pilot"]
    I --> J["10. Select potential shops"] --> K["11. Record outreach"] --> L["12. Enter pilot measurements"] --> M["13. Review deterministic outcome"]
    M --> N["14. Save the pilot round"] --> O["15. Define the next bounded experiment"]

Security

Never commit .env.

Never place API keys in frontend code.

Never use NEXT_PUBLIC_ for secret values.

.env.example contains variable names only.

Browser backups do not contain API keys.

Workspace restore rejects secret-like fields and unsafe URL protocols.

Merchant business notes, retailer outreach and pilot results should be
treated as private workspace data.

If a credential is accidentally exposed, rotate it immediately.

Current Limitations

MarketSarthi is intentionally transparent about what its evidence can
and cannot establish.

Google Maps review mentions may be old and are not current-stock proof.

Review verification is bounded to control SerpApi usage.

Search availability varies by query, location and time.

Google Trends may return no usable data for low-volume terms.

Trends values are relative and cannot be compared directly with sales or
population.

Search snippets can be incomplete or stale.

Google News can contain loosely related or older coverage.

The SerpApi cache is process-local.

Authentication and server/database persistence are not currently active.

Workspace persistence is browser-local and does not synchronize across
devices.

Saved pilot history is limited to 12 rounds.

Pilot measurements depend on merchant-entered observations.

The optional money check is a simple test-level cash snapshot, not
accounting.

Copilot conversations are browser-local and limited to 30 messages.

Jev currently classifies Google Shopping evidence only.

Jev does not reduce SerpApi retrieval time.

The Jev confidence threshold requires further evaluation before wider
routing.

A future market-potential model must not reuse evidence coverage or
pilot completion as a demand score.

Project Documentation

For the detailed living technical state of the project, read:

PROJECT_CONTEXT.md

It contains:

Current product workflow

Evidence contract

Search strategy

Query planning

Pilot rules

Copilot behavior

API contracts

Environment configuration

Current limitations

Dated change history

Additional documentation:

docs/ARCHITECTURE.md docs/DAY_01.md AGENTS.md

Repository Guide

<details>

<summary>

Open repository guide

</summary>

Path                                Purpose

README.md                         Public project overview and
quick-start guide

PROJECT_CONTEXT.md                Detailed living product and
technical source of truth

AGENTS.md                         Repository instructions for
AI-assisted development

docs/ARCHITECTURE.md              Architecture and integration
documentation

docs/DAY_01.md                    Historical foundation plan

.env.example                      Safe environment-variable template

.vscode/                          VS Code settings and runnable
development tasks

package.json                      Root development commands

apps/api/                         FastAPI backend

apps/web/                         Next.js frontend

apps/api/tests/                   Backend tests

Generated folders and secrets such as .env, node_modules, .venv, .next,
caches and local databases should not be committed.

</details>

Project Highlights

flowchart TD
    A["Evidence-first regional expansion research"] --> B["Six SerpApi evidence surfaces"] --> C["Deterministic safeguards"] --> D["Optional confidence-gated Jev"]
    D --> E["Evidence-bound AI synthesis"] --> F["Merchant-controlled real-world pilot"] --> G["Deterministic pilot review"] --> H["Measured next experiment"]

The central design principle is simple:

MarketSarthi does not try to predict the market with certainty. It helps
a merchant make the next test more informed, measurable and transparent.

Author

Vishv Pandya

Built as a hands-on exploration of:

Generative AI • Agentic AI • Market Research • LLM Applications •
Evidence-Based Decision Systems
