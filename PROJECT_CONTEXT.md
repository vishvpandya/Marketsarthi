# MarketSarthi project context

> Living source of truth for developers and AI tools. Read this file before making changes and update it after every material project change. Never place API-key values in this file.

Last updated: 2026-09-25

## Product in one sentence

MarketSarthi is an evidence-first regional-expansion copilot that helps Indian MSME and D2C merchants turn their product facts and business story into a transparent, source-linked market hypothesis and a small, low-risk pilot.

## Problem being solved

Small merchants often want to enter a new city but cannot afford conventional market research. Public search data can reveal comparable products, prices, possible local channels, and customer language, but it cannot guarantee demand or success. MarketSarthi organizes those signals, exposes gaps and contradictions, and recommends what the merchant should test next.

The running demo uses a family-run roasted methi khakhra business in Bolpur considering Kolkata. The architecture must remain useful for other products and regions; khakhra-specific query expansion is an explicit product-aware rule, not a global assumption.

## Evidence contract

- Never promise that a product or city will succeed.
- Separate merchant-provided context from externally observed evidence.
- Link every market observation to its source when available.
- Separate direct competitors, alternative competitors, and uncertain matches.
- Treat Google Maps businesses as potential channels, not competitors.
- Call a Maps lead “verified” only when a product-filtered Maps Reviews search returns a matching review; even then, current stock requires direct confirmation.
- Recommend a bounded pilot before large production or distribution commitments.

## Current user workflow

1. The merchant enters product, category, current market, candidate cities, price range, pack size, differentiators, constraints, business background, and expansion goal.
2. DeepSeek V4.1 Flash in explicit non-thinking mode drafts a research brief while preserving facts, goals, assumptions, and open questions. Gemini is an optional provider fallback. If all configured AI providers are unavailable, MarketSarthi creates a clearly labeled, editable local template from merchant-entered facts so the workflow is not blocked.
3. The merchant edits and approves the brief.
4. Preview mode generates the research plan without calling paid APIs. The frontend keeps the merchant in the **Prepare research** workspace, shows a compact plan summary, and enables **Start live research** only when the plan matches the currently approved brief.
5. The frontend has two merchant-facing workspaces without changing routes or backend contracts: **Prepare research** contains business details, the editable AI brief, plan preview, and a collapsible Research Plan control; completed live research opens **Results & pilot**. A fresh page load or browser refresh always starts in **Prepare research**, even when a completed result has been restored, so the merchant sees the intended first step; the saved result remains available through **Results & pilot** without repeating paid research. Results are split into **Decision overview**, **Evidence & sources**, and **Plan a small test** tabs so the merchant does not have to interpret one very long page. In live results, **Evidence & sources** is the single place for the research plan and supporting detail; the redundant result-header Research details control is reserved for plan preview only. The plan first shows plain-English business questions, their target region, planned call count, engines, and live answer status. Switching tabs only changes presentation and preserves every existing result, refresh, evidence, pilot, export, backup, and Copilot action.
6. Live analysis runs the bounded query plan and displays each SerpApi call, its parent business question, result count, success/no-result/failure status, and error note in a collapsible tool trace. Failed calls are never hidden. A transient SerpApi read timeout receives one short-backoff retry; an explicit provider message saying that no results were returned is classified as `no_results`, not as a failure.
7. Shopping evidence is normalized and classified as direct, alternative, or uncertain. When `TYPESAFE_API_KEY` is configured, the optional TypeSafe Jev layer evaluates all Shopping listings as typed parallel Choice questions. Only classifications meeting the configured confidence threshold replace the existing label; missing, low-confidence, invalid, or failed Jev answers preserve MarketSarthi's existing deterministic/LLM classification path. Jev never searches the web, changes prices, decides market success, or replaces SerpApi, DeepSeek, or Gemini.
8. Maps evidence is deduplicated, kept as potential retail channels, and a bounded review-verification pass checks up to three leads for product mentions.
9. Product-filtered review excerpts become source-linked Customer Voice evidence with deterministic topic tags. They are bounded named-business observations, not city-wide sentiment.
10. Google Search collects and deduplicates results from six human-style angles covering product visibility, buying language, sellers/distributors, brand/price pages, announced trade events, and official associations or schemes. At most 12 organic-result pages are retained per candidate city. A result is labeled city-specific only when its title, snippet, or displayed URL clearly mentions that city; otherwise it remains wider online evidence.
11. Google Trends performs one India-wide 12-month time-series call and one India-wide city-comparison call for the product core term. Values are relative 0–100 search-interest scores, not search volume, buyer intent, demand, market size, or sales.
12. Every evidence item carries a scope: `city_local`, `india_wide_online`, or `business_review`.
13. Google News uses twelve human-style angles for each candidate city: exact product, product type, city and India-wide category context, announced festivals and trade events, retailer and distributor changes, competitor launches, regulation/MSME support, and supply or customer-context changes. Articles are reported context, not proof of demand, sentiment, business impact, or future sales.
14. A deterministic City Evidence Scorecard compares research coverage, product benchmarks, local channels, verified mentions, price-band position, evidence gaps, and the safest next action. It does not require an AI model and is explicitly not a probability-of-success score. Trends, web, and news evidence are shown separately and are supplied to the configured model; they do not currently alter the deterministic scorecard.
15. DeepSeek V4.1 Flash (`deepseek-flash`) is the primary synthesis path and runs with thinking explicitly disabled. Gemini remains an optional fallback provider. Evidence-only output occurs only after every configured provider has a real quota, availability, network, or validation failure.
16. Merchant-facing category names, scorecard messages, evidence gaps, and AI answers use plain English with short explanations. Technical enum and schema names remain internal so API contracts stay stable.
17. Identical SerpApi requests can reuse a one-hour process-local cache. Cache reuse is shown in the live tool trace and avoids another network request; provider failures are not cached.
18. When two or more candidate cities are supplied, a deterministic comparison table shows the same evidence dimensions side by side without ranking the cities or predicting success.
19. After live analysis, the merchant can choose a researched city and define a small shop pilot using their own duration, quantity, shop count, test price, sell-through target, and maximum return rate. Actual results remain optional until the test is completed.
20. MarketSarthi calculates sell-through and return rates only from merchant-entered results, checks them against merchant-defined thresholds, and exports a source-linked Markdown pilot report. Meeting those checks supports another bounded test; it is not validation of city-wide demand.
21. The merchant can shortlist named Google Maps leads from the chosen city for pilot outreach. Leads with product-specific review evidence are visibly separated from unverified potential shops, and every selection remains an outreach candidate until the merchant confirms current stock, fit, terms, and willingness to participate.
22. The frontend automatically saves the current merchant form, approved brief, completed research response, pilot draft, and selected shop IDs in versioned browser-local storage. The latest workspace restores after refresh without repeating paid research calls. API keys and server environment variables are never included.
23. For each shortlisted shop, the merchant can record an outreach state—Not contacted, Contacted, Interested, Confirmed, or Not participating—and free-text notes. These are explicitly merchant-entered operational facts, not SerpApi or AI conclusions, and they appear in the pilot export.
24. Confirmed shops receive optional shop-by-shop measurement cards using plain language: packets given, bought, returned, damaged, missing, still at the shop, whether the shop wants another batch, and learning notes. MarketSarthi requires every packet at each completed shop to be explained, totals all categories, and copies them into the overall pilot result only after an explicit merchant action.
25. When the completed totals are entered, a post-pilot review calculates one outcome with deterministic rules before any AI call. The configured AI provider may explain those fixed facts and propose one bounded next experiment, but it cannot change the outcome. If the provider is unavailable, a local rule-based explanation keeps the review usable.
26. The merchant may optionally add a simple pilot money check: cash actually received, costs already spent and not recoverable, and the highest test loss they accept. MarketSarthi calculates the cash result and uses that merchant-defined limit in the post-pilot outcome without calling it accounting profit, ROI, margin, or a forecast.
27. After review, the merchant can explicitly save the completed pilot as a historical round and start another round while keeping the current city, plan, and shop shortlist. The latest two saved rounds are compared only on measured changes; MarketSarthi does not infer what caused those changes.
28. From the second round onward, the merchant records one main planned change—repeat the same test, price, pack size, product/recipe, shop type, display/message, or another change—and explains it briefly. The change is passed to the review model and saved with the round, but differences between rounds are never presented as proof that the change caused the result.
29. The merchant can download the complete browser workspace as a versioned MarketSarthi JSON backup and restore it later. Restore validates the app/version marker and core data shape, rejects secret-like fields and unsafe URL protocols, enforces a 5 MB limit, and asks for confirmation before replacing the current browser workspace.
30. Every live observation shows when it was checked for the report. The result header shows whether all evidence was checked together or only some sections were updated. Staleness uses the oldest preserved evidence after a targeted refresh, and the Markdown pilot report records both newest and oldest check times plus timestamps beside source links. A check time is not a source publication date or a guarantee that the listing, price, article, or shop detail is still current.
31. The merchant can remove an individual saved pilot round after a confirmation that names its city and saved date. Removal changes only browser-local history, automatically updates latest-round comparison and later exports, and leaves the current research, form, and active pilot untouched.
32. Completed pilot totals now capture damaged packets, missing packets, and packets still at shops as separate merchant-entered counts rather than hiding them in notes. All five outcome counts must be entered, including explicit zeros. The deterministic review pauses when stock is missing, still at shops, or unexplained; recorded damage produces a corrective small-retest outcome even when the merchant's sales and return checks were met.
33. Each confirmed shop now uses the same five-way packet breakdown as the overall pilot. The **Use these totals** action remains disabled until every shop's given packets equal bought plus returned plus damaged plus missing plus still-at-shop counts. Copying is explicit, and the backend independently rejects impossible rows or a mismatch between shop totals and overall totals.
34. After live analysis, the merchant can refresh only Shopping, Maps with Reviews, Trends, Web Search, or News. A targeted refresh bypasses the process-local SerpApi cache, replaces evidence and tool runs only for the selected engine group, preserves all other research and pilot state, and clears the old final summary so it cannot describe stale evidence. **Refresh everything** performs the same cache-bypassing update for all five groups without resetting the merchant workspace.
35. The merchant explicitly creates or updates a four-part final decision summary after completing the desired refreshes: what was observed, what remains unknown, what to do next, and what not to conclude. Observations, gaps, and safety warnings are deterministic; the configured AI may write only the simple next actions. Unsafe success claims or provider failure fall back to the deterministic local summary. The summary is saved with the workspace and included in the Markdown pilot report.
36. A floating **MarketSarthi Copilot** answers merchant questions from the current browser workspace. It can explain saved prices, city findings, shop leads, review observations, Trends, web pages, news, evidence gaps, and next steps. It answers from saved evidence first, attaches only server-whitelisted source links, states the relevant evidence check time, and then guides the merchant to the correct targeted refresh when newer evidence is wanted. It never starts SerpApi calls, clicks refresh controls, changes merchant data, or claims current prices, demand, sales, stock, retailer agreement, or success. The configured AI may receive the question, up to eight recent messages, merchant context, compact pilot counts, deterministic summaries, and up to twelve relevant evidence observations; if it is unavailable or unsafe, a deterministic local workspace guide answers instead. Up to 30 chat messages and an explicitly shared preferred name are stored in the browser workspace and JSON backup. Name introduction, recall, and greetings are handled locally without consuming an AI call. Evidence UUIDs remain internal: the model returns citations through a structured field, server-side source whitelisting creates the visible source cards, and final answer text is sanitized so raw evidence or source IDs are never shown to merchants.

### Workspace Copilot

The Copilot endpoint performs deterministic intent routing before any model call. Price questions prioritize direct Google Shopping evidence; distribution and shop questions prioritize Maps and Maps Reviews; customer-language questions prioritize review excerpts; and Trends, Web Search, and News questions stay within their matching evidence surfaces. General city and next-step questions use city scorecards and the final decision summary when available.

The service creates an authoritative local draft, selects a bounded evidence set by engine, city, and question overlap, and asks the configured language model only to make that draft clearer. Refresh guidance and evidence dates are appended by application code. Returned source IDs must match the server-selected evidence set; unknown IDs are discarded. Unsupported currency values and prohibited market-success language cause the complete AI answer to be replaced by the local draft. A greeting is handled locally without consuming an AI request. If merchant details changed after research, the Copilot warns that a new full live analysis is required before applying the old evidence to the changed product or region.

## Search strategy

### Google Shopping via SerpApi

The product-benchmark mission asks, “Which similar products, brands, prices and pack sizes are visible?” Its product-first fallback ladder moves from exact SKU wording to safer broad product wording. For the demo it is:

1. `Roasted methi khakhra 200 g` — localized to the candidate city.
2. `Roasted methi khakhra` — India-wide online market.
3. `khakhra 200 g`.
4. `khakhra`.
5. `khakra` — spelling fallback.

The ladder stops when it has at least 12 unique product results or six direct matches. Alternative snacks are not used as direct-price benchmarks. Multipacks are normalized per pack and, where weight is detectable, per 100 g. The localized first query is labeled `city_local`; results recovered without a location are labeled `india_wide_online` and must not be presented as city-specific evidence.

### Google Maps via SerpApi

The local-selling-options mission asks, “Which shops in the target city could already sell or test this product?” For khakhra, discovery deliberately widens across five bounded search angles:

1. `khakhra shop`
2. `khakhra store`
3. `Gujarati snacks shop`
4. `namkeen shop`
5. `farsan shop`

For other products, the generic ladder uses the product core, category, and category-store wording rather than food-specific terms. Results from all Maps queries are combined and deduplicated by `data_id`, `place_id`, or normalized title and address.

Up to three discovered businesses with a Maps `data_id` are checked through the SerpApi Google Maps Reviews engine using the product core as the review query. A returned match changes the lead from `potential` to `verified_product_mention`; it does not prove present inventory. Up to three usable excerpts per checked business are retained as `business_review` evidence, clipped to 280 characters, source-linked when possible, and tagged only for mentioned topics such as taste, oil/health, price/value, packaging/freshness, or availability/variety. Topic presence is not treated as sentiment or prevalence.

### Google Trends via SerpApi

Each live run makes two India-wide calls for the product core term:

1. `TIMESERIES` over `today 12-m` compares an early window with a recent window and reports the peak returned period.
2. `GEO_MAP_0` with `region=CITY` looks for candidate cities and also retains the five highest returned city rows.

Trend evidence always uses `india_wide_online` scope. A missing candidate city means that the returned data did not contain a usable row; it is not evidence of zero demand. Trend values are normalized within the returned Google Trends result and must never be described as absolute search counts, buyers, demand, market size, revenue, or predicted sales.

### Google Search via SerpApi

Each candidate city gets six bounded Google Search angles: the merchant's full product name, `where to buy <product core>`, combined seller/distributor wording, brand/price wording, upcoming category exhibitions or trade fairs, and category associations or government/MSME schemes. These investigate product availability, possible channels, competitive positioning, official event pages, organizers, registration pages, associations, schemes, and notices.

Results from all six Search angles are deduplicated by source URL, and at most 12 unique pages per city are retained. Each tool call remains visible even when it times out or returns no results. City scope still requires the city name to appear in the returned title, snippet, or displayed URL. A localized search alone is not enough to claim that a page or business is local, official, accurate, or evidence of demand.

### Bounded human-style query planning

Every planned query carries a plain-English `research_question`. The wider-web and news event investigation contains exactly 18 visible angles per candidate city: six Google Search angles and twelve Google News angles. This lets the system reason across product, category, geography, events, channels, competition, policy, support, supply, and customer context instead of treating one literal phrase as the entire market. The planner is deterministic and product-aware so preview mode remains free and no LLM can create unlimited calls or invent product claims. The configured AI provider receives the resulting evidence for synthesis but does not bypass the approved plan.

The live UI derives a transparent question status from real calls:

- `Planned` before live execution.
- `Answered` when a query returns usable results.
- `Answered with gaps` when useful results exist alongside a failed or empty query.
- `Not answered` when attempted queries return no usable results.
- `Not needed` when an unexecuted fallback was skipped after an earlier query met its evidence stop condition.

### SerpApi response cache

Successful responses and normalized no-result responses are cached in memory for identical search parameters. The default lifetime is 3,600 seconds with a maximum of 512 entries. Cache keys include the endpoint, search parameters, and a non-reversible hash of the configured SerpApi account key; raw secret values are never stored in cache keys or documentation. Each cached payload is copied before reuse so research normalization cannot mutate the stored entry. Provider failures are not cached.

The cache is process-local: restarting the API clears it, and separate API processes do not share it. A live tool-run item sets `cache_hit=true` and displays “reused from local cache” when the network call was avoided. `SERPAPI_CACHE_TTL_SECONDS=0` disables local caching. Merchant-triggered targeted refreshes deliberately bypass this cache so the selected evidence group is requested from SerpApi again.

Evidence timestamps record when an observation is normalized into the current report. When the tool trace shows a cache hit, the underlying successful provider response can be up to the configured cache lifetime old (one hour by default). The timestamp is not the source's publication or last-updated date, and the interface asks merchants to rerun research older than seven days before making a new commitment.

### Cross-city comparison rubric

The comparison appears only when at least two candidate cities are analyzed and preserves the merchant's city order; it does not select a winner. It displays raw counts for same-product listings, possible shops, shops with product mentions, city-specific web pages, city-specific recent articles, returned Google Trends city score, and price-range position.

The `evidence_coverage_percent` measures completion of six checks, with one equal check for each of the following:

1. At least three same-product listings.
2. At least one usable same-product price.
3. At least five local shops to check.
4. At least one shop with a product-specific review mention.
5. At least one city-specific web result.
6. A returned Google Trends row for the candidate city.

News article counts are displayed as context but do not increase the coverage percentage. A higher percentage means fewer research gaps, not stronger demand, a better market, or a higher chance of success. A Trends value of 100 means the highest relative interest inside that returned comparison, not 100 searches or 100% demand.

### Merchant pilot workspace

The pilot workspace appears only after live analysis. The merchant chooses one of the researched cities and enters the operational plan: duration in days, units placed, participating shops, test price, target sell-through percentage, and maximum acceptable return percentage. MarketSarthi does not generate hidden quantities, financial projections, or a recommended success threshold.

The workspace also shows the chosen city's deduplicated Google Maps leads. The merchant may add named businesses to an outreach shortlist, with product-review-verified leads clearly separated from other possible shops. Selection means only “contact this business”; it never means that the business currently stocks the product, has agreed to participate, or is a proven distribution channel. A shortlist may contain fewer names than the planned shop count when some participants are still to be confirmed, but it cannot exceed the planned count when exporting the report.

The pilot interface keeps its numbered workflow continuous. **Contact the selected shops** remains visible as step 3 even before a shop is selected and shows a short instruction explaining that outreach statuses and notes will appear there after selection. The totals step therefore follows as step 4 instead of appearing to jump directly from step 2 to step 4.

Numbered steps and circular count badges are fixed-size, non-shrinking UI elements. Long headlines, descriptions, and responsive layouts wrap around them without compressing the circles into ovals, keeping the same visual language across preparation, principles, results, evidence, and pilot sections.

Each selected shop has a merchant-controlled outreach tracker with five states: `not_contacted`, `contacted`, `interested`, `confirmed`, and `declined`. A confirmed status represents only the merchant's own record that the retailer agreed to this bounded pilot; it is never inferred from Maps, reviews, Search, or an AI model. Per-shop contact notes and an aggregate count of waiting, interested, confirmed, and declined leads are visible. Removing a shop from the shortlist removes its outreach record.

For every shop marked `confirmed`, the merchant may separately record packets given, bought, returned, damaged, missing, still at that shop, whether the shop wants another batch, and shop-level learning notes. Each completed row requires non-negative whole numbers and must fully explain the packets given to that shop. The interface totals every category, but it never silently overwrites the overall result; **Use these totals** is an explicit merchant action. The backend also compares every shop-category total with the submitted overall totals before assigning an outcome.

After running the real-world test, the merchant may enter or review packets given to all shops, packets customers bought, unsold packets returned, shops asking for another batch, and qualitative learning notes. The browser computes:

- `sell-through = units sold / actual units placed × 100`
- `return rate = units returned / actual units placed × 100`

Planned units and actual placed units remain separate so a short shipment or changed allocation cannot silently distort the measured rates.

Merchant-facing labels deliberately avoid terms such as “units placed,” “sell-through,” and “return rate.” The interface instead explains the same calculations as the percentage of given packets bought by customers and the percentage returned. Bought, returned, damaged, missing, and still-at-shop counts are entered separately, and the interface shows whether any packets remain unexplained.

“Merchant-defined checks met” appears only when sell-through reaches the merchant's own target and the return rate stays at or below the merchant's own maximum. It does not mean that the city is validated or that future sales are likely. The downloadable Markdown report contains the plan, selected outreach shops and their status, measured results, a city evidence snapshot, safe operating checks, and up to 15 source links from the completed research.

The **Review pilot** action sends only the merchant-entered pilot results, optional shop measurements, notes, and a bounded evidence summary to `/api/v1/research/pilot-review`. MarketSarthi computes the percentages, data gaps, threshold checks, reasons, and outcome on the server before asking an AI provider for a plain-English explanation. The model is not allowed to change those calculated facts or outcome, invent customer feedback, claim city-wide demand, or recommend a full rollout.

The merchant may complete an optional money check before review. `net cash result = money received during the test − merchant-entered non-recoverable test costs`. Returned stock that can still be sold should not be counted as non-recoverable. All three fields—money received, non-recoverable costs, and maximum acceptable test loss—must be supplied together. This deliberately simple signal does not include tax, inventory valuation, working capital, depreciation, unpaid invoices, or other accounting treatment and therefore must never be described as profit, margin, ROI, or long-term viability.

The deterministic review rejects packet counts that exceed the number given to shops. Missing packets, packets still at shops, unexplained stock, or conflicting shop totals pause the next test. Damaged stock requires a corrective small retest even when the merchant's percentage checks pass. The deterministic outcomes are:

- `investigate_before_next_test` when packets are not fully accounted for or entered shop totals conflict with the aggregate totals.
- `continue_small_test` when both merchant-defined percentage checks are met, the optional money check is within its merchant-defined limit, and at least one shop asks for another batch.
- `investigate_before_next_test` when both percentage checks are met but no shop asks for another batch, because the signals conflict.
- `modify_and_retest` when only some checks are met, including when the product checks pass but an entered money check exceeds the merchant's accepted test loss.
- `stop_and_review` when neither percentage check is met and the stock data is complete.

These are experiment-management outcomes, not market-success grades. Shop-by-shop entries remain optional: when they are absent, the review exposes that limitation but can still use complete overall totals. Every response includes what the pilot does not prove. Unsafe AI market-success language is rejected in favor of the local explanation. If every configured AI provider fails, the API returns the same deterministic facts and outcome with a `local-rule-review` explanation and a visible warning. The pilot review is saved in browser-local workspace state and included in later Markdown report downloads; changing any pilot input clears the stale review.

Once a pilot has a completed review, **Save this pilot round** stores an immutable summary of the merchant-entered measurements, deterministic outcome, AI or local explanation, and next experiment. **Start next round** clears only measured results, money entries, shop measurements, and learning notes; it keeps the city, operational plan, selected shops, and outreach records so the merchant can run the next bounded test. Up to 12 rounds are retained in newest-first order in the same browser-local workspace. The UI compares the newest two saved rounds using percentage-point changes in packets bought and returned plus the simple money difference when both rounds contain it. These deltas are observations only and never causal claims or market forecasts. Up to five saved-round summaries are included in the Markdown report.

The first saved pilot is labeled as the first recorded round. Starting the next round clears the previous measurement fields and requires the merchant to select one main planned change and describe it in simple language before review. “Repeat the same test” is available when the purpose is replication rather than modification. The planned-change record is included in the AI prompt, saved history, latest-versus-previous display, and Markdown report. It documents experimental intent only: MarketSarthi never claims the selected change caused an observed improvement or decline.

The current workspace is autosaved under the versioned `marketsarthi:workspace:v1` key in the browser's local storage, including the completed research response, shop outreach records, shop-level pilot measurements, current review, and up to 12 saved pilot rounds, so a refresh does not require another paid live run. This is single-browser convenience, not account-backed persistence: it does not synchronize across devices, browsers, users, or private sessions and can be removed with **Start new workspace** or normal browser-data controls. No API-key value is sent to or stored by this mechanism.

**Download backup** exports that complete workspace to a human-readable `.json` file with an explicit `MarketSarthi` marker, backup version, and export timestamp. API keys and server environment variables are not part of frontend state and are never exported. Because business background, notes, retailer outreach, and pilot results are included, the UI tells the merchant to keep the backup private. **Restore backup** accepts only files up to 5 MB, validates the version and minimum workspace structure, rejects common secret-field names and non-HTTP(S) stored URLs, and asks for confirmation before replacing local storage. The page reloads only after a successful write. Markdown pilot reports remain presentation documents and are not importable as workspace backups.

### Google News via SerpApi

Each candidate city receives twelve visible news questions:

1. Full merchant product around the city.
2. Broader product type around the city.
3. Wider category changes in the city.
4. Product developments across India.
5. Category developments across India.
6. Publicly announced festivals or relevant events.
7. Publicly announced exhibitions, trade fairs, or expos.
8. Retailer or supermarket expansion.
9. Distributor or wholesale-network changes.
10. Competitor launches and brand expansion.
11. Regulation, government notices, FSSAI context, and MSME schemes.
12. Raw-material, supply, input-price, or customer-context changes.

The raw `when:12m` search operator is no longer shown or required. Article dates remain visible and the configured AI provider must distinguish past reporting, ongoing changes, and publicly announced future events. Results are deduplicated by article URL and capped at 18 evidence items per city. At least six news angles run; after that, the remaining angles can stop when 12 unique articles have already been collected. Sparse research continues through all twelve angles. Grouped Google News stories are flattened into source-linked article evidence. An article is labeled city-specific only when its title or snippet clearly names the target city; otherwise it remains wider reported context. Article count and tone must never become demand, sentiment, market-size, impact, or sales claims.

## SerpApi surfaces currently used

| Engine | Purpose | UI label |
| --- | --- | --- |
| `google_shopping` | Product, seller, price, pack, rating, and positioning evidence | SerpApi · Google Shopping |
| `google_maps` | Wider local channel discovery | SerpApi · Google Maps |
| `google_maps_reviews` | Product-specific review verification for a bounded set of leads | SerpApi · Google Maps Reviews |
| `google_trends` | India-wide interest over time and relative interest by city | SerpApi · Google Trends |
| `google` | Source-linked web pages found for each product-and-city search | SerpApi · Google Search |
| `google_news` | Reported or announced product, category, event, channel, policy, supply, and customer-context changes | SerpApi · Google News |

For one candidate city, a live analysis plans a maximum of five Shopping calls, five Maps calls, three Maps Reviews checks, six Google Search calls, twelve Google News calls, and two Google Trends calls: at most 33 SerpApi calls. Shopping can stop early after its product-evidence threshold. News runs at least six angles and can stop after that when 12 unique articles have already been collected; sparse evidence causes all twelve news angles to run. Trends runs once per overall request, not once per candidate city. Maps and Search use fixed bounded angles because they answer different market questions rather than acting only as spelling fallbacks.

## Architecture

- Frontend: Next.js App Router, React, TypeScript, plain CSS in `apps/web`.
- Backend: FastAPI, Pydantic, HTTPX, Python 3.11+ in `apps/api`.
- Package/environment management: `uv` for Python and npm for the web app.
- External reasoning: DeepSeek V4.1 Flash configured by `DEEPSEEK_MODEL` is primary and runs in non-thinking JSON mode; Gemini can remain an optional provider fallback.
- Optional fast classification: TypeSafe Jev configured by `TYPESAFE_API_KEY` classifies Google Shopping evidence only; it is confidence-gated and fails back to the existing path.
- External evidence: SerpApi configured by `SERPAPI_KEY`.

Important backend files:

- `apps/api/app/schemas/research.py` — request, plan, evidence, tool-run, and synthesis contracts.
- `apps/api/app/services/research.py` — query planning, normalization, verification, summaries, and orchestration.
- `apps/api/app/services/copilot.py` — workspace-question routing, evidence selection, deterministic answers, AI wording, source whitelisting, and refresh guidance.
- `apps/api/app/services/serpapi.py` — SerpApi engine adapter.
- `apps/api/app/services/deepseek.py` — DeepSeek non-thinking structured-output adapter.
- `apps/api/app/services/llm.py` — primary/fallback language-model router.
- `apps/api/app/services/gemini.py` — optional Gemini fallback adapter.
- `apps/api/app/services/jev.py` — optional TypeSafe Jev adapter for typed, confidence-gated Shopping classification.
- `apps/api/app/services/pilot_review.py` — deterministic post-pilot calculations, AI explanation prompt, and local fallback.
- `apps/api/app/routers/research.py` — `/brief`, `/preview`, `/analyze`, `/refresh`, `/decision-summary`, `/copilot`, and `/pilot-review` endpoints.

Important frontend files:

- `apps/web/app/page.tsx` — merchant form, brief editor, research and evidence views, browser-local workspace persistence, and the merchant pilot workflow.
- `apps/web/app/globals.css` — visual system and responsive behavior.

## API endpoints

- `POST /api/v1/research/brief` — generate the editable AI research brief through the configured provider chain.
- `POST /api/v1/research/preview` — return a plan only; no AI-provider or SerpApi credits are used.
- `POST /api/v1/research/analyze` — collect live evidence and attempt synthesis.
- `POST /api/v1/research/refresh` — bypass the local cache and replace only the merchant-selected evidence groups while preserving all other research.
- `POST /api/v1/research/decision-summary` — calculate evidence-safe observations and gaps, then optionally use the configured AI for simple next actions.
- `POST /api/v1/research/copilot` — answer a question from the supplied browser workspace and return whitelisted evidence sources plus optional refresh guidance; it performs no SerpApi search.
- `POST /api/v1/research/pilot-review` — calculate a post-pilot outcome and return an AI or local-rule explanation.
- `GET /health` and readiness routes — application health checks.

## Environment variables

Required for the full live workflow:

- `SERPAPI_KEY`
- `DEEPSEEK_API_KEY`

Common optional configuration:

- `LLM_PROVIDER`
- `LLM_FALLBACK_PROVIDER`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_BASE_URL`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_FALLBACK_MODEL`
- `NEXT_PUBLIC_API_BASE_URL`
- `MARKETSARTHI_NEXT_DIST_DIR` (optional local frontend build-output folder)
- `FRONTEND_URL`
- `REQUEST_TIMEOUT_SECONDS`
- `SERPAPI_CACHE_TTL_SECONDS`
- `SERPAPI_CACHE_MAX_ENTRIES`
- `TYPESAFE_API_KEY` (optional; leaving it empty disables Jev)
- `TYPESAFE_DEFAULT_MODEL` (defaults to `jev-latest`)
- `TYPESAFE_BASE_URL`
- `JEV_CLASSIFICATION_MIN_CONFIDENCE` (defaults to `0.65`)

Secrets belong in the root `.env`, never in frontend source, screenshots, commits, or this context file.

## Windows and VS Code commands

From the repository root:

```powershell
uv --cache-dir apps/api/.uv-cache sync --project apps/api --extra dev
npm --prefix apps/web install
npm run dev:api
npm run dev:web
```

Open `http://localhost:3000`; FastAPI docs are at `http://localhost:8000/docs`.

Verification commands:

```powershell
npm run test:api
npm run lint:api
npm run lint:web
npm run build:web
```

If a running Windows preview or OneDrive locks the normal `.next` folder, production-build verification may use a temporary output folder without stopping the preview:

```powershell
$env:MARKETSARTHI_NEXT_DIST_DIR = ".next-build-check"
npm run build:web
```

The temporary generated folder is not application data and may be removed after verification.

VS Code users can also select **Terminal → Run Task** and choose a `MarketSarthi` task.

## Current limitations and next work

- A review mention can be old, is limited to a named business, and is not current-stock proof.
- Maps review verification is intentionally capped to control SerpApi usage.
- Search-result availability varies by query, place, and time.
- Google Trends may return no usable data for low-volume terms, and its relative scale cannot be compared with sales or population.
- Google Search snippets can be incomplete or stale and are leads for source inspection, not verified facts.
- Google News may return loosely related, duplicated, or old-looking coverage; every article remains a source to inspect rather than a verified market fact.
- The cache is process-local rather than persistent or shared across deployed API workers.
- Multilingual review analysis, server/database persistence, and authentication are not yet active.
- The latest workspace is saved only in the current browser. It does not synchronize across devices or users, and a downloaded report cannot yet be imported back into the app.
- JSON backup and restore provides manual portability, but there is still no automatic cloud synchronization, user account, merge operation, or recovery if both the browser data and backup file are lost.
- Saved pilot history is limited to 12 rounds in the current browser and has no server backup or cross-device synchronization. Individual rounds can be removed locally after confirmation.
- Post-pilot review trusts merchant-entered counts and notes. It detects arithmetic gaps and shop-total conflicts but cannot independently verify sales, returns, retailer intent, damaged stock, or missing packets.
- Copilot conversations are browser-local and limited to 30 messages. The configured AI can receive the current question, up to eight recent messages, merchant context, compact pilot status, summaries, and selected evidence; merchants should not enter confidential customer, banking, identity, or secret information.
- The optional money check is a merchant-entered cash snapshot, not accounting profit or unit economics. It does not value reusable returned inventory or independently verify receipts and expenses.
- A future market-potential model must not reuse evidence coverage or pilot completion as a demand score.
- Jev currently classifies Google Shopping listings only. It does not reduce SerpApi retrieval time, and its confidence threshold needs evaluation against real MarketSarthi examples before wider routing or decision-summary use.

## Change log

### 2026-09-25

- Prepared the repository for a clean public GitHub release with an LF line-ending policy, ignored generated Python package metadata and TypeScript build state, and a public README repository guide explaining every important documentation, configuration, application and test area.
- Standardized circular step and count badges across the frontend so long text and narrow layouts cannot compress them into oval shapes; long result headings now wrap without deforming their step marker.
- Made every page load start in **Prepare research** while preserving any restored completed result behind the enabled **Results & pilot** navigation.
- Removed the redundant Research details dropdown from completed live results; **Evidence & sources** now owns the live research plan and supporting detail, while the dropdown remains available for plan preview.
- Kept the pilot workflow visibly sequential by always showing step 3 with an instructional empty state before shops are selected.
- Added an optional TypeSafe Jev integration after SerpApi normalization for fast, typed Google Shopping classification while preserving SerpApi as the evidence source and DeepSeek/Gemini as the explanation layer.
- Added confidence-gated Jev decisions, automatic fallback to existing labels, visible model/confidence provenance in the evidence ledger, readiness reporting, environment configuration, and mocked integration coverage.
- Added the official `typesafe-sdk` dependency and kept the entire Jev feature removable by deleting its key or service adapter without changing the live-research contract.
- Replaced the Copilot welcome text and quick questions that were hard-coded to Kolkata with prompts derived from the current completed research: setup guidance before research, a city-specific question for one city, and a real comparison prompt for multiple cities.
- Added deterministic multi-city Copilot comparison handling so the quick comparison reports each researched city's same-product listings, shop leads, and evidence coverage without turning those figures into demand or success claims.
- Added persistent Copilot preferred-name memory to browser autosave and workspace backups, with deterministic introduction, recall, and personalized greeting responses that do not spend an AI call; existing workspaces recover the name from saved user messages when possible.
- Prevented internal evidence/source UUIDs from appearing in Copilot prose through stronger model instructions plus server and browser sanitization; old saved chat bubbles are cleaned on display while validated source cards remain available.
- Deduplicated identical provider warnings before returning research and targeted-refresh responses, preserving the first occurrence and its display order.
- Added a frontend warning-deduplication guard so restored older workspaces cannot trigger duplicate React keys or repeat the same merchant-facing timeout message.
- Kept every individual failed query visible in the SerpApi tool trace; only the repeated summary warnings are collapsed.

### 2026-09-24

- Reorganized the existing frontend into two clear workspaces: **Prepare research** for merchant details, brief approval, and plan preview; and **Results & pilot** for completed live research.
- Split the completed-research workspace into Decision overview, Evidence & sources, and Plan a small test tabs while preserving all APIs, evidence, refresh, pilot, export, backup, and Copilot behavior.
- Enforced the visible brief → preview → live-research order in the UI and added a compact plan summary plus navigation back to saved results.
- Added a floating, workspace-aware MarketSarthi Copilot that answers from saved research, returns source links and check times, and guides merchants to the appropriate targeted refresh without running it automatically.
- Added deterministic Copilot intent routing and local answers for greetings, prices, shops, reviews, Trends, Search, News, city summaries, and next steps, with configured-AI wording only when it passes evidence and safety checks.
- Added browser persistence and backup for up to 30 Copilot messages, an eight-message model-history limit, context-change warnings, source-ID whitelisting, unsafe-claim fallback, responsive chat UI, and backend coverage.
- Added targeted, cache-bypassing refresh controls for Shopping, Maps with Reviews, Trends, Web Search, and News, plus a refresh-all action that preserves unselected evidence and the merchant's pilot workspace.
- Added a merchant-triggered final decision summary with deterministic observations, unknowns, and safety limits; the AI is restricted to simple next actions and a local fallback remains available.
- Added mixed-age evidence messaging after selective refresh and included the final summary plus newest/oldest evidence check times in Markdown pilot reports.
- Extended confirmed-shop measurement to bought, returned, damaged, missing, and still-at-shop packet counts with full per-shop reconciliation.
- Expanded **Use these totals**, report export, browser persistence, AI review context, and backend conflict detection to cover every shop-level stock category.
- Added separate merchant-entered counts for damaged packets, missing packets, and packets still at shops across the UI, API, deterministic facts, AI context, saved rounds, and Markdown reports.
- Added full five-way stock reconciliation: missing, unfinished, or unexplained stock pauses the next recommendation, while recorded damage produces a bounded corrective-retest outcome.
- Added confirmed, merchant-controlled removal of individual saved pilot rounds while preserving the active research and pilot workspace.
- Made round removal automatically update browser persistence, latest-two-round comparison, backup contents, and future Markdown exports.
- Added visible evidence check times to the result header and every evidence item, with a plain-English warning when restored research is older than seven days.
- Added evidence check times and their limitations to downloaded pilot reports, while distinguishing check time from source publication time and cache age.
- Added complete browser-workspace JSON backup and restore controls covering research, pilot drafts, outreach, reviews, and saved pilot rounds without exporting API keys.
- Added a 5 MB import limit, MarketSarthi/version and core-shape validation, secret-field and unsafe-URL rejection, replacement confirmation, and clear privacy/error messages.
- Added a one-main-change record for repeated pilot rounds with plain options for replication, price, pack size, product/recipe, shop type, display/message, and another change.
- Added the merchant's planned change to AI review context, saved history, latest-round comparison, and Markdown export while explicitly prohibiting causal claims.
- Added an optional `MARKETSARTHI_NEXT_DIST_DIR` build-output override so production builds can be verified without stopping a Windows preview that locks `.next`.
- Added explicit pilot-round saving, a next-round reset that keeps the plan and shortlist, and a browser-local history of up to 12 completed rounds.
- Added a latest-versus-previous comparison for packets bought, packets returned, and simple test-money changes without making causal or future-performance claims.
- Added saved-round summaries to Markdown exports and made workspace clearing explicitly include pilot history.
- Replaced merchant-facing money-check terms such as “non-recoverable costs,” “cash result,” and “accepted loss limit” with everyday questions and explanations about money received, test costs already used up, and how much loss is okay.
- Kept the API field names and deterministic calculation unchanged while simplifying the UI, AI explanation wording, validation errors, review cards, and Markdown export.
- Added an optional, plain-language pilot money check using cash received, non-recoverable test costs, and a merchant-defined acceptable-loss limit.
- Added deterministic cash-result calculation and integrated the optional check into post-pilot outcomes without presenting it as profit, margin, ROI, unit economics, or a forecast.
- Added money-check validation, browser persistence, review cards, Markdown export, AI prompt safeguards, and backend tests.
- Added a post-pilot decision review with deterministic percentages, data-gap checks, merchant-threshold checks, reasons, and four bounded experiment outcomes.
- Restricted AI to explaining the calculated outcome and proposing one small next experiment; AI cannot override facts or claim market validation, demand, or likely sales.
- Added a local rule-based explanation fallback so DeepSeek or Gemini quota and availability failures do not block the merchant's pilot review.
- Kept shop-by-shop measurement optional, exposed its absence as a limitation, and reject unsafe AI market-success language before it reaches the merchant.
- Added the **Review pilot** interface, plain-language result cards, unresolved-packet visibility, browser persistence, and post-pilot content in the Markdown export.
- Added `/api/v1/research/pilot-review`, typed schemas, aggregate and per-shop validation, and backend tests for clean, conflicting, invalid, AI-success, and AI-fallback cases.
- Replaced technical pilot-result labels with simple merchant language across shop cards, totals, validation messages, calculated outcomes, and Markdown exports.
- Added clear explanations for packets given to shops, packets customers bought, unsold packets returned, and shops asking for another batch.
- Added a visible reminder to account for packets that are damaged, missing, or still at a shop without changing the underlying calculation fields.
- Added shop-by-shop measurement for confirmed retailers with actual placement, sales, returns, continuation intent, and learning notes.
- Added per-shop validation, transparent totals, explicit merchant-controlled application to the overall result, browser autosave, and report export.
- Separated planned units from actual units placed and now calculates sell-through and return rate using the actual denominator.
- Added a merchant-entered retailer outreach tracker for every shortlisted Maps lead with not-contacted, contacted, interested, confirmed, and declined states.
- Added per-shop contact notes, visible outreach totals, browser-local persistence, and outreach details in the Markdown pilot report.
- Kept outreach status separate from search evidence: MarketSarthi never infers retailer interest, confirmation, current stock, or participation.
- Added versioned browser-local autosave and refresh restoration for the merchant form, approved brief, research evidence, pilot draft, and shop shortlist.
- Added visible saving/restored/unavailable status plus a user-controlled **Start new workspace** action, without storing API keys.
- Preserved completed live research across refreshes so a browser reload does not automatically require another paid SerpApi or AI-provider run.
- Added DeepSeek V4.1 Flash as the default language-model provider using the official `deepseek-flash` model identifier, JSON output mode, and explicit non-thinking mode.
- Added a provider-independent structured-generation router with optional Gemini fallback and the existing local/evidence-only final fallback.
- Added DeepSeek configuration, readiness reporting, mocked API-contract tests, and merchant-facing provider labels without exposing secret values.
- Connected the pilot workspace to live Google Maps evidence with a merchant-approved shop outreach shortlist for the selected city.
- Kept product-review-verified businesses separate from unconfirmed potential shops and repeated current-stock and participation caveats in the UI and export.
- Added selected shop names, observations, status, and source links to the Markdown pilot report without claiming retailer agreement or product availability.

### 2026-09-23

- Added a merchant-controlled pilot workspace after live analysis with editable duration, units, shops, test price, sell-through target, and maximum return rate.
- Added optional actual-result entry, deterministic sell-through and return-rate calculations, and a threshold check that never claims city-wide validation.
- Added a downloadable Markdown pilot report containing the merchant's plan, measured results, safe operating checks, city evidence snapshot, and source links.
- Added a configurable one-hour process-local SerpApi response cache with bounded entries, defensive payload copies, and no caching of provider failures.
- Added visible `cache_hit` status to the live tool trace so repeated demonstrations show when a network request was avoided.
- Added a multi-city comparison table covering product listings, shops, verified mentions, city web pages, recent city articles, Trends rows, price position, and evidence coverage.
- Defined the six-check evidence-coverage rubric explicitly and kept News counts and Trends score magnitude out of the coverage percentage.
- Preserved merchant city order and prohibited treating evidence coverage as market potential, demand, ranking, or probability of success.
- Added one bounded retry with short backoff for transient SerpApi read timeouts.
- Reclassified SerpApi's explicit “hasn't returned any results” response as a normal empty result so query widening continues without a false failure warning.
- Fixed duplicate React keys for the two Google Trends plan cards by including tool and stage identity.
- Replaced the two-query News fallback with an 18-angle human-style Search and News investigation bundle per candidate city.
- Added explicit questions for events, exhibitions, retailer/distributor changes, competitor launches, regulation, FSSAI context, MSME schemes, supply changes, and customer context.
- Removed the merchant-visible `when:12m` operator and now communicates article dates and past/ongoing/announced-event meaning in plain English.
- Added coverage-aware News stopping: at least six angles run, all twelve run when evidence is sparse, and later angles can stop after 12 unique articles.
- Raised the one-city worst-case SerpApi budget to 33 calls and documented the trade-off explicitly.
- Activated SerpApi Google News with a visible product-first query and category fallback for each candidate city.
- Added grouped-story flattening, URL deduplication, an eight-article evidence cap, and early stopping after five unique articles.
- Added a plain-English Recent news and market changes accordion plus Google News plan and live-tool-trace labels.
- Added conservative city-scope detection and Gemini rules preventing news coverage from becoming demand, sentiment, impact, market-size, sales, or prediction claims.
- Updated the maximum one-city live-analysis budget from 20 to 22 SerpApi calls.

### 2026-09-22

- Added a bounded, product-aware query planner that organizes SerpApi calls around human business questions instead of showing only literal keyword fallbacks.
- Expanded each city from one Google Search phrase to five distinct availability, seller, distribution, brand, and price search angles, with URL deduplication and a 12-page evidence cap.
- Added the parent business question to every planned query and every live tool-run record while preserving visible failures, timeouts, empty results, and sources.
- Added merchant-facing question cards with planned/answered/answered-with-gaps/not-answered/not-needed status derived from real tool outcomes.
- Kept preview mode deterministic and free; Gemini synthesizes the approved evidence but cannot create uncontrolled SerpApi calls.
- Activated SerpApi Google Trends with separate 12-month time-series and city-level relative-interest evidence.
- Activated localized SerpApi Google Search with source-linked organic results and conservative city-scope detection.
- Added plain-English Trends and web-evidence accordions, research-plan entries, and live tool-trace visibility.
- Added Gemini safeguards preventing relative Trends scores or web-result visibility from becoming demand, sales, market-size, or official-source claims.
- Documented the maximum SerpApi call budget and kept Trends and web evidence outside the deterministic City Evidence Scorecard for now.
- Rewrote merchant-facing evidence labels, scorecard messages, research-plan explanations, fallback copy, and Gemini language rules in plain English without changing the technical data contracts.
- Added explicit evidence provenance scopes: candidate-city, India-wide online benchmark, and named-business review.
- Added a Customer Voice evidence group sourced from product-filtered SerpApi Google Maps Reviews excerpts.
- Added deterministic topic tags without claiming sentiment, prevalence, demand, or current inventory.
- Enriched Gemini synthesis input with scoped Shopping, Maps, and Customer Voice evidence while preserving Gemini as the primary reasoning path.

### 2026-09-21

- Added the living project-context file and repository instruction requiring future updates.
- Replaced the always-visible research output with merchant-friendly nested accordions: Research Plan, per-engine searches, Live Tool Trace, Evidence Ledger, and exclusive evidence categories.
- Added accessible expanded-state and controlled-panel relationships to every dropdown control.
- Expanded khakhra Maps discovery to product shops, Gujarati snack shops, namkeen shops, and farsan shops.
- Added Maps result deduplication and bounded product-filtered review verification.
- Split local evidence into verified product mentions and unverified potential channels.
- Preserved visible SerpApi provider and engine labels in the research plan, live tool trace, and evidence ledger.
- Improved synthesis-failure warnings so preserved evidence is accompanied by an actionable error type.
- Added graceful brief-generation degradation: exhausted Gemini 429/5xx retries now produce an editable local-template brief and visible warning instead of blocking Preview and Live Analysis.
- Added a Gemini-independent City Evidence Scorecard with per-city product benchmarks, channel counts, verified mentions, price-band signal, evidence gaps, and a bounded next action.
- Earlier work added merchant-background capture, Gemini brief generation/editing, product-first Shopping fallbacks, direct/alternative competitor separation, normalized pricing, and evidence-safe synthesis.
