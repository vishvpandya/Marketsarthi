<div align="center">

🚀 MarketSarthi

Evidence-first regional expansion copilot for Indian MSMEs & D2C brands

Research → Compare → Verify → Pilot → Measure → Learn







</div>

🧭 What is MarketSarthi?

MarketSarthi is an evidence-first market expansion copilot designed for Indian MSMEs and D2C merchants.

A merchant can enter a product, business context, pricing, pack size, constraints and candidate cities. MarketSarthi then:

creates an editable AI research brief

plans bounded market research

collects evidence from multiple public sources

normalizes and scopes the evidence

optionally uses TypeSafe Jev for Shopping classification

applies deterministic rules before AI synthesis

explains the evidence using an LLM

helps the merchant identify potential retail channels

supports a small real-world pilot

measures the pilot using deterministic calculations

saves pilot rounds and helps define the next experiment

MarketSarthi does not claim that a city will succeed. It helps a merchant make the next experiment more informed, measurable and transparent.

🔄 Complete Product Workflow

flowchart TD

    A["👤 Merchant Input<br/>Product • Category • Price • Pack Size<br/>Business Story • Constraints • Candidate Cities"]
        --> B["🧠 AI Research Brief<br/>DeepSeek V4.1 Flash"]

    B --> C{"✏️ Merchant Reviews Brief"}

    C -->|Edit| B
    C -->|Approve| D["📋 Research Plan Preview<br/>No Paid API Calls"]

    D --> E["🔎 Start Live Research"]

    subgraph EVIDENCE["SerpApi — Evidence Collection"]
        direction TB

        E --> S1["🛒 Google Shopping<br/>Products • Brands • Prices • Packs"]

        E --> S2["📍 Google Maps<br/>Potential Local Shops"]

        E --> S3["💬 Maps Reviews<br/>Product Mentions • Customer Voice"]

        E --> S4["📈 Google Trends<br/>Relative Interest • City Comparison"]

        E --> S5["🔎 Google Search<br/>Sellers • Distributors • Events • Schemes"]

        E --> S6["📰 Google News<br/>Market • Retail • Policy • Supply"]
    end

    S1 --> N["⚙️ Evidence Processing<br/>Normalize • Deduplicate • Scope • Timestamp"]
    S2 --> N
    S3 --> N
    S4 --> N
    S5 --> N
    S6 --> N

    N --> J{"🧩 TypeSafe Jev<br/>Configured?"}

    J -->|Yes + High Confidence| JC["Jev Shopping Classification<br/>Direct • Alternative • Uncertain"]
    J -->|No / Low Confidence / Failed| FC["Existing Classification Path"]

    JC --> SC["📊 Deterministic City Evidence Scorecard"]
    FC --> SC

    SC --> AI["🤖 Evidence-Bound AI Synthesis<br/>DeepSeek Primary • Gemini Fallback"]

    AI --> R["📦 Results & Pilot Workspace"]

    R --> O["📌 Decision Overview<br/>Observed • Unknown • Next Action • Limits"]
    R --> EV["🔗 Evidence & Sources<br/>Plan • Tool Trace • Evidence Ledger"]
    R --> CP["💬 MarketSarthi Copilot<br/>Answers from Saved Evidence"]

    R --> RF{"🔄 Need New Evidence?"}

    RF -->|Yes| REF["🎯 Targeted Refresh<br/>Shopping • Maps/Reviews • Trends<br/>Search • News"]
    REF --> E

    RF -->|No| CITY["🏙️ Choose Researched City"]

    CITY --> P["🧪 Plan Small Pilot<br/>Duration • Quantity • Shops<br/>Test Price • Merchant Thresholds"]

    P --> SH["🏪 Select Potential Shops<br/>Google Maps Leads"]

    SH --> OUT["📞 Merchant Outreach<br/>Not Contacted → Contacted<br/>Interested → Confirmed / Declined"]

    OUT --> TEST["🚀 Run Real-World Pilot"]

    TEST --> MEAS["📝 Record Results<br/>Bought • Returned • Damaged<br/>Missing • Still at Shop"]

    MEAS --> REVIEW["🧮 Deterministic Pilot Review"]

    REVIEW --> EX["💡 AI / Local Explanation<br/>AI Cannot Change Calculated Outcome"]

    EX --> SUM["📋 Final Decision Summary<br/>Observed • Unknown • Next Step<br/>What Not to Conclude"]

    SUM --> SAVE["💾 Save Pilot Round"]

    SAVE --> HISTORY["📚 Pilot History<br/>Up to 12 Saved Rounds"]

    HISTORY --> COMP["📊 Compare Latest Two Rounds<br/>Measured Changes Only"]

    COMP --> CHANGE["🔧 Choose Main Planned Change<br/>Repeat • Price • Pack • Product<br/>Shop Type • Display • Other"]

    CHANGE --> NEXT["🧪 Start Next Bounded Test"]

    NEXT --> P

    SUM --> REPORT["📄 Download Markdown Pilot Report<br/>Evidence • Sources • Pilot Results"]

    R --> BACKUP["💾 JSON Workspace Backup"]
    BACKUP --> RESTORE["♻️ Validated Workspace Restore"]
    RESTORE --> R

    CP --> ROUTE["🧭 Deterministic Intent Routing"]

    ROUTE --> ANSWER["💬 Evidence-First Answer<br/>Whitelisted Sources + Check Time"]

    ANSWER --> GUIDE["⏱️ Refresh Guidance When Evidence Is Old"]
    GUIDE --> REF

🏗️ Architecture at a Glance

The complete workflow above explains the product journey.

This smaller diagram explains the technical pipeline.

flowchart LR

    A["👤 Merchant"]
        --> B["🟦 MarketSarthi"]

    B --> C["🧠 AI Research Brief"]

    C --> D["🔎 SerpApi<br/>6 Evidence Engines"]

    D --> E["⚙️ Evidence Processing<br/>Normalize • Deduplicate • Scope"]

    E --> F["🧩 TypeSafe Jev<br/>Optional Shopping Classification"]

    F --> G["📊 Deterministic Rules<br/>Scorecard • Validation • Pilot Outcome"]

    G --> H{"🤖 AI Synthesis"}

    H -->|Primary| I["DeepSeek V4.1 Flash"]
    H -->|Fallback| J["Gemini"]

    I --> K["📦 Results"]
    J --> K

    K --> L["🧪 Small Real-World Pilot"]

    L --> M["📈 Measured Results"]

    M --> G

🎯 Why MarketSarthi?

Traditional market research can be expensive and difficult for small businesses.

MarketSarthi focuses on a simpler loop:

Collect Evidence
      ↓
Understand What Is Known
      ↓
Identify What Is Missing
      ↓
Run a Small Test
      ↓
Measure What Actually Happened
      ↓
Choose the Next Experiment

The important distinction is:

AI explains evidence
        ≠
AI predicts guaranteed success

🔎 Evidence Sources

MarketSarthi uses six SerpApi research surfaces:

Source

What MarketSarthi Uses It For

🛒 Google Shopping

Products, brands, prices, packs and positioning

📍 Google Maps

Potential local retail channels

💬 Google Maps Reviews

Product-specific review mentions

📈 Google Trends

Relative search interest over time and by city

🔎 Google Search

Sellers, distributors, events, schemes and source pages

📰 Google News

Market, retail, policy, supply and customer context

Evidence scopes

Each evidence item is assigned a scope:

city_local

india_wide_online

business_review

This prevents the system from treating every search result as city-specific evidence.

🧩 TypeSafe Jev Integration

TypeSafe Jev is part of the MarketSarthi pipeline.

It is used specifically for Google Shopping classification after Shopping results have been retrieved and normalized.

flowchart LR

    A["Google Shopping<br/>SerpApi Results"]
        --> B["Normalize Listings"]

    B --> C{"TypeSafe Jev<br/>Configured?"}

    C -->|Yes| D["Jev Typed Classification"]

    D --> E{"Confidence ≥ Threshold?"}

    E -->|Yes| F["Use Jev Classification"]
    E -->|No| G["Keep Existing Classification"]

    C -->|No| G

    F --> H["Direct / Alternative / Uncertain"]
    G --> H

    H --> I["Deterministic Scorecard"]

Jev's role

Jev:

classifies Google Shopping evidence

provides typed structured classification

uses a confidence threshold

falls back when unavailable or uncertain

does not search the web

does not replace SerpApi

does not change prices

does not classify Maps, Trends, Search or News

does not decide whether a city will succeed

Current default confidence threshold: 0.65

📊 Deterministic Evidence Scorecard

MarketSarthi calculates research coverage using deterministic rules.

The six checks are:

At least 3 same-product listings

At least 1 usable same-product price

At least 5 local shops to check

At least 1 shop with a product-specific review mention

At least 1 city-specific web result

A returned Google Trends row for the candidate city

Evidence coverage means research completeness. It is not a demand score, success probability or market ranking.

🧪 Small Real-World Pilot

Research is only the beginning.

After reviewing the evidence, the merchant can select a researched city and create a bounded pilot.

The merchant controls:

test duration

planned quantity

participating shops

test price

target percentage bought

maximum acceptable return percentage

Shop outreach

Not Contacted
      ↓
Contacted
      ↓
Interested
      ↓
Confirmed / Declined

A confirmed shop means the merchant recorded that the retailer agreed to the bounded test.

It does not mean permanent distribution or proven demand.

Shop measurements

The merchant can record:

Packets given

Packets bought

Packets returned

Packets damaged

Packets missing

Packets still at the shop

Whether the shop wants another batch

Learning notes

Every packet must be accounted for.

Packets Given
      =
Bought
+ Returned
+ Damaged
+ Missing
+ Still at Shop

🧮 Deterministic Pilot Review

The pilot outcome is calculated from actual merchant-entered measurements.

Percentage bought

Packets bought
÷
Actual packets given
× 100

Percentage returned

Packets returned
÷
Actual packets given
× 100

Possible experiment outcomes include:

Outcome

Meaning

continue_small_test

Merchant-defined checks are met and at least one shop asks for another batch

modify_and_retest

Some checks are met or the optional money check exceeds the accepted test loss

investigate_before_next_test

Data is incomplete/conflicting or the signals require investigation

stop_and_review

Defined checks are not met and stock data is complete

These are pilot-management outcomes, not market-success predictions.

💬 MarketSarthi Copilot

The Copilot answers questions from the current saved workspace.

It does not automatically start a new paid search.

flowchart TD

    Q["💬 Merchant Question"]
        --> R["🧭 Deterministic Intent Routing"]

    R --> P["Price Questions"]
    R --> S["Shop / Distribution Questions"]
    R --> V["Customer Language / Reviews"]
    R --> T["Trends / Search / News"]
    R --> G["General City / Next Steps"]

    P --> EP["Shopping Evidence"]
    S --> ES["Maps + Reviews"]
    V --> EV["Review Evidence"]
    T --> ET["Matching Evidence"]
    G --> EG["Scorecard + Summary"]

    EP --> A["Evidence-First Answer"]
    ES --> A
    EV --> A
    ET --> A
    EG --> A

    A --> W["Whitelisted Sources + Check Time"]

    W --> F{"Need New Evidence?"}

    F -->|Yes| REF["Guide Merchant to Targeted Refresh"]
    F -->|No| END["Answer"]

🔄 Targeted Refresh

Evidence changes over time.

Instead of rerunning everything, MarketSarthi can refresh a selected evidence group:

Shopping

Maps + Reviews

Trends

Search

News

A targeted refresh:

bypasses the local cache

reruns only the selected evidence group

preserves the rest of the workspace

preserves pilot information

clears stale synthesis

💾 Workspace Persistence

MarketSarthi stores the current workspace in browser-local storage.

It preserves:

merchant information

approved brief

research results

pilot draft

shop shortlist

outreach records

shop measurements

current review

Copilot history

saved pilot rounds

JSON Backup

The workspace can also be exported as a versioned JSON backup.

Restore validates:

workspace version

core structure

file size

secret-like fields

stored URL protocols

API keys are never exported.

🛠️ Technology Stack

Layer

Technology

Frontend

Next.js • React • TypeScript • CSS

Backend

FastAPI • Python • Pydantic • HTTPX

Market Research

SerpApi

Primary LLM

DeepSeek V4.1 Flash

Fallback LLM

Gemini

Optional Classifier

TypeSafe Jev

Python Environment

uv

Frontend Package Manager

npm

Development

VS Code Tasks

🗂️ Project Architecture

MarketSarthi/
│
├── apps/
│   │
│   ├── api/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   │
│   │   │   ├── routers/
│   │   │   │   └── research.py
│   │   │   │
│   │   │   ├── schemas/
│   │   │   │   └── research.py
│   │   │   │
│   │   │   └── services/
│   │   │       ├── research.py
│   │   │       ├── copilot.py
│   │   │       ├── serpapi.py
│   │   │       ├── deepseek.py
│   │   │       ├── gemini.py
│   │   │       ├── llm.py
│   │   │       ├── jev.py
│   │   │       └── pilot_review.py
│   │   │
│   │   └── tests/
│   │
│   └── web/
│       └── app/
│           ├── page.tsx
│           └── globals.css
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── DAY_01.md
│
├── PROJECT_CONTEXT.md
├── AGENTS.md
├── .env.example
├── .gitignore
├── .gitattributes
├── package.json
└── README.md

📁 Important Files

File

Purpose

apps/api/app/services/research.py

Research planning, evidence collection, normalization and refresh

apps/api/app/services/copilot.py

Copilot routing and evidence selection

apps/api/app/services/serpapi.py

SerpApi integration, retries and cache

apps/api/app/services/deepseek.py

DeepSeek structured-output adapter

apps/api/app/services/gemini.py

Gemini fallback adapter

apps/api/app/services/jev.py

TypeSafe Jev integration

apps/api/app/services/pilot_review.py

Deterministic pilot calculations

apps/api/app/routers/research.py

Research, refresh, Copilot and pilot endpoints

apps/web/app/page.tsx

Main merchant workflow and UI

apps/web/app/globals.css

Frontend styling

PROJECT_CONTEXT.md

Detailed project source of truth

🚀 Run MarketSarthi

Prerequisites

Python 3.11+

uv

Node.js / npm

VS Code recommended

Environment Variables

Copy:

.env.example

to:

.env

Required for full live research:

SERPAPI_KEY=
DEEPSEEK_API_KEY=

Optional:

GEMINI_API_KEY=
TYPESAFE_API_KEY=

[!IMPORTANT]
Never commit real API keys or put them inside frontend code.

⚡ Quickest Way — VS Code

For a judge or someone opening the repository for the first time:

1. Open the repository root in VS Code

Open the MarketSarthi repository, not only apps/web or apps/api.

2. Open Command Palette

Press:

Ctrl + Shift + P

Search:

Tasks: Run Task

Select:

MarketSarthi: Start Full Stack

3. Open the application

http://localhost:3000

FastAPI docs:

http://localhost:8000/docs

Available VS Code tasks

MarketSarthi: Start API
MarketSarthi: Start Web
MarketSarthi: Start Full Stack

💻 Terminal Setup

Install backend dependencies

uv --cache-dir apps/api/.uv-cache sync --project apps/api --extra dev

Install frontend dependencies

npm --prefix apps/web install

Start API

npm run dev:api

Start Web

Open another terminal:

npm run dev:web

Then visit:

http://localhost:3000

🎬 Judge / Demo Flow

Once the application is running:

Merchant Input
      ↓
Generate AI Research Brief
      ↓
Edit / Approve Brief
      ↓
Preview Research Plan
      ↓
Start Live Research
      ↓
Inspect Evidence + Tool Trace
      ↓
Review Decision Overview
      ↓
Choose Researched City
      ↓
Plan Small Pilot
      ↓
Select Potential Shops
      ↓
Record Outreach
      ↓
Enter Pilot Results
      ↓
Review Deterministic Outcome
      ↓
Save Pilot Round
      ↓
Define Next Bounded Experiment

🧪 Verification

Run:

npm run test:api
npm run lint:api
npm run lint:web
npm run build:web

If Windows locks the normal .next directory:

$env:MARKETSARTHI_NEXT_DIST_DIR = ".next-build-check"
npm run build:web

🔐 Security

Never commit .env

Never put API keys in frontend code

Never use NEXT_PUBLIC_ for secret values

.env.example contains variable names only

Browser backups do not contain API keys

Restore rejects secret-like fields

Restore rejects unsafe URL protocols

Merchant business notes and pilot data should be treated as private workspace data

If a credential is exposed, rotate it immediately.

⚠️ Current Limitations

MarketSarthi is intentionally transparent about its boundaries:

Maps review mentions may be old and are not current-stock proof.

Search availability varies by query, location and time.

Google Trends is relative interest, not sales or demand.

Search snippets can be incomplete or stale.

Google News can contain older or loosely related coverage.

SerpApi caching is process-local.

Authentication and server/database persistence are not currently active.

Workspace persistence is browser-local and does not synchronize across devices.

Pilot measurements depend on merchant-entered observations.

The optional money check is a simple test-level cash snapshot, not accounting.

Copilot history is browser-local.

Jev currently classifies Google Shopping evidence only.

Jev does not replace SerpApi retrieval.

The Jev confidence threshold should be evaluated before wider routing.

Evidence coverage must not be reused as a demand or market-potential score.

📚 Documentation

For the detailed technical state of the project:

PROJECT_CONTEXT.md

docs/ARCHITECTURE.md

docs/DAY_01.md

AGENTS.md

🌟 Project Philosophy

Evidence first.
Deterministic where facts matter.
AI where explanation helps.
Small experiments before large commitments.

Research with evidence. Test with discipline. Learn from reality.

<div align="center">

Built by Vishv Pandya

Generative AI • Agentic AI • Market Research • Evidence-Based Decision Systems

</div>
