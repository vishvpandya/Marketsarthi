"use client";

import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";

type CompetitorType = "direct" | "alternative" | "uncertain";

type EvidenceItem = {
  id: string;
  evidence_type: string;
  city: string;
  title: string;
  observation: string;
  source_name: string;
  source_url?: string;
  provider: string;
  engine?: string;
  evidence_scope: "city_local" | "india_wide_online" | "business_review";
  competitor_type?: CompetitorType;
  channel_status?: "potential" | "verified_product_mention";
  classification_reason?: string;
  classification_source?: string;
  classification_confidence?: number;
  retrieved_at?: string;
  metrics: Record<string, unknown>;
};

type ResearchResponse = {
  mode: string;
  request_id: string;
  plan: {
    product_summary: string;
    approved_brief?: string;
    queries: Array<{
      provider: string;
      research_question: string;
      tool: string;
      engine: string;
      stage: string;
      city: string;
      query: string;
      purpose: string;
      fallback_rank?: number;
    }>;
    limitations: string[];
  };
  city_summaries: Array<{
    city: string;
    shopping_results: number;
    local_channels: number;
    direct_competitors: number;
    alternative_competitors: number;
    uncertain_competitors: number;
    observed_price_min?: number;
    observed_price_median?: number;
    observed_price_max?: number;
    direct_price_per_100g_median?: number;
    verified_local_channels: number;
    city_specific_web_results: number;
    city_specific_news_results: number;
    trend_interest_score?: number;
    evidence_dimensions_met: number;
    evidence_dimensions_total: number;
    evidence_coverage_percent: number;
    coverage_level: "limited" | "developing" | "pilot_ready";
    price_band_signal: "below_observed" | "overlaps_observed" | "above_observed" | "unknown";
    evidence_gaps: string[];
    next_action: string;
  }>;
  tool_runs: Array<{
    provider: string;
    research_question: string;
    engine: string;
    tool: string;
    stage: string;
    city: string;
    scope: string;
    query: string;
    status: "success" | "no_results" | "failed";
    result_count: number;
    cache_hit: boolean;
    note?: string;
  }>;
  evidence: EvidenceItem[];
  synthesis?: {
    headline: string;
    recommendation: string;
    product_changes: string[];
    risks: string[];
    next_experiments: string[];
    confidence: string;
  };
  decision_summary?: DecisionSummaryContent | null;
  decision_model_used?: string | null;
  decision_warnings?: string[];
  classification_model_used?: string | null;
  classification_items_applied?: number;
  classification_items_skipped?: number;
  warnings: string[];
};

type DecisionSummaryContent = {
  observed: string[];
  unknowns: string[];
  next_actions: string[];
  do_not_conclude: string[];
};

type DecisionSummaryResponse = {
  summary: DecisionSummaryContent;
  model_used: string;
  warnings: string[];
};

type RefreshSection = "shopping" | "maps_reviews" | "trends" | "web_search" | "news";
type AppView = "prepare" | "results";
type ResultsTab = "overview" | "evidence" | "pilot";

type CopilotSource = {
  evidence_id: string;
  title: string;
  source_url: string;
  source_name: string;
  engine?: string;
  city: string;
  checked_at: string;
};

type CopilotResponse = {
  answer: string;
  preferred_name?: string | null;
  sources: CopilotSource[];
  suggested_refresh?: RefreshSection | null;
  refresh_instruction?: string | null;
  model_used: string;
  warnings: string[];
};

type CopilotMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: CopilotSource[];
  suggested_refresh?: RefreshSection | null;
  model_used?: string;
  warnings?: string[];
};

type BriefDetails = {
  business_facts: string[];
  merchant_goals: string[];
  constraints: string[];
  assumptions: string[];
  open_questions: string[];
};

type BriefResponse = {
  brief: BriefDetails & { research_brief: string };
  model_used: string;
  warnings: string[];
};

type PilotReviewResponse = {
  facts: {
    outcome: "continue_small_test" | "modify_and_retest" | "investigate_before_next_test" | "stop_and_review";
    bought_percent: number;
    returned_percent: number;
    bought_target_met: boolean;
    returned_limit_met: boolean;
    merchant_checks_met: boolean;
    planned_packets: number;
    actual_packets_given: number;
    packets_bought: number;
    packets_returned: number;
    packets_damaged?: number;
    packets_missing?: number;
    packets_still_at_shops?: number;
    packets_unaccounted_for: number;
    shops_planned: number;
    shops_asking_another_batch: number;
    money_received_inr?: number | null;
    nonrecoverable_costs_inr?: number | null;
    maximum_acceptable_loss_inr?: number | null;
    net_cash_result_inr?: number | null;
    cash_check_met?: boolean | null;
    reasons: string[];
    data_gaps: string[];
  };
  review: {
    summary: string;
    what_worked: string[];
    what_needs_attention: string[];
    next_experiment: string;
    do_not_conclude: string[];
  };
  model_used: string;
  warnings: string[];
};

type PilotForm = {
  city: string;
  duration_days: string;
  units_planned: string;
  shops_planned: string;
  test_price_inr: string;
  target_sell_through_percent: string;
  max_return_percent: string;
  actual_units_placed: string;
  units_sold: string;
  units_returned: string;
  units_damaged: string;
  units_missing: string;
  units_still_at_shops: string;
  shops_willing_to_continue: string;
  money_received_inr: string;
  nonrecoverable_costs_inr: string;
  maximum_acceptable_loss_inr: string;
  experiment_change_type: PilotChangeType;
  experiment_change_description: string;
  learning_notes: string;
};

type PilotChangeType = "" | "first_round" | "repeat_same" | "price" | "pack_size" | "product" | "shop_type" | "display_message" | "other";

type OutreachStatus = "not_contacted" | "contacted" | "interested" | "confirmed" | "declined";

type PilotShopOutreach = {
  status: OutreachStatus;
  notes: string;
};

type ContinuationDecision = "not_recorded" | "yes" | "no";

type ShopPilotResult = {
  units_placed: string;
  units_sold: string;
  units_returned: string;
  units_damaged: string;
  units_missing: string;
  units_still_at_shop: string;
  continuation: ContinuationDecision;
  notes: string;
};

type PilotRound = {
  id: string;
  signature: string;
  saved_at: string;
  product_name: string;
  city: string;
  duration_days: number;
  test_price_inr: number;
  actual_packets_given: number;
  packets_bought: number;
  packets_returned: number;
  packets_damaged?: number;
  packets_missing?: number;
  packets_still_at_shops?: number;
  shops_asking_another_batch: number;
  bought_percent: number;
  returned_percent: number;
  net_cash_result_inr: number | null;
  outcome: PilotReviewResponse["facts"]["outcome"];
  summary: string;
  next_experiment: string;
  learning_notes: string;
  experiment_change_type?: PilotChangeType;
  experiment_change_description?: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const REFRESH_SECTIONS: Array<{ value: RefreshSection; label: string; detail: string }> = [
  { value: "shopping", label: "Shopping", detail: "Products and prices" },
  { value: "maps_reviews", label: "Maps + Reviews", detail: "Shops and product mentions" },
  { value: "trends", label: "Trends", detail: "Relative search interest" },
  { value: "web_search", label: "Web Search", detail: "Market pages and sellers" },
  { value: "news", label: "News", detail: "Recent reported changes" },
];

function engineLabel(engine?: string) {
  if (engine === "google_shopping") return "Google Shopping";
  if (engine === "google_maps") return "Google Maps";
  if (engine === "google_maps_reviews") return "Google Maps Reviews";
  if (engine === "google_trends") return "Google Trends";
  if (engine === "google") return "Google Search";
  if (engine === "google_news") return "Google News";
  return engine?.replaceAll("_", " ") ?? "Search";
}

function scopeLabel(scope: EvidenceItem["evidence_scope"], engine?: string) {
  if (engine === "google_trends") return "Search data for India";
  if (engine === "google_news" && scope === "city_local") return "Article mentions the target city";
  if (engine === "google_news") return "Wider reported context";
  if (scope === "city_local") return "Found in the target city";
  if (scope === "india_wide_online") return "Found online across India";
  return "Review from this shop";
}

function formatEvidenceTimestamp(value?: string) {
  if (!value) return "Time not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Time not available";
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(date);
}

function coverageLabel(level: string) {
  if (level === "pilot_ready") return "Enough evidence to plan a small test";
  if (level === "developing") return "Some useful evidence found";
  return "We need more information";
}

function priceSignalLabel(signal: string) {
  if (signal === "overlaps_observed") return "Your price is within the range of similar online products";
  if (signal === "below_observed") return "Your price is lower than the similar online products we found";
  if (signal === "above_observed") return "Your price is higher than the similar online products we found";
  return "We do not have enough prices to compare yet";
}

function shortPriceSignalLabel(signal: string) {
  if (signal === "overlaps_observed") return "Within observed range";
  if (signal === "below_observed") return "Below observed range";
  if (signal === "above_observed") return "Above observed range";
  return "Not enough price data";
}

function queryStepLabel(engine: string) {
  if (engine === "google_shopping") return "Product search";
  if (engine === "google_maps") return "Shop search";
  if (engine === "google_news") return "News angle";
  if (engine === "google") return "Web search";
  return "Search";
}

const initialForm = {
  product_name: "Roasted methi khakhra",
  category: "Packaged healthy snacks",
  current_city: "Bolpur, West Bengal",
  target_cities: "Kolkata",
  price_min_inr: "120",
  price_max_inr: "180",
  pack_size: "200 g",
  differentiators: "Low oil, roasted, travel friendly",
  constraints: "Small production capacity",
  business_background:
    "This is my father's family-run khakhra business in Bolpur. I want to help him expand carefully into a larger market.",
  expansion_goal:
    "Test Kolkata with a low-risk pilot before investing in larger production or distribution.",
};

const initialPilotForm: PilotForm = {
  city: "",
  duration_days: "",
  units_planned: "",
  shops_planned: "",
  test_price_inr: "",
  target_sell_through_percent: "",
  max_return_percent: "",
  actual_units_placed: "",
  units_sold: "",
  units_returned: "",
  units_damaged: "",
  units_missing: "",
  units_still_at_shops: "",
  shops_willing_to_continue: "",
  money_received_inr: "",
  nonrecoverable_costs_inr: "",
  maximum_acceptable_loss_inr: "",
  experiment_change_type: "first_round",
  experiment_change_description: "First recorded pilot round.",
  learning_notes: "",
};

type PersistedWorkspace = {
  schema_version: 1;
  saved_at: string;
  form: typeof initialForm;
  research_brief: string;
  brief_details: BriefDetails | null;
  brief_model: string | null;
  brief_warnings: string[];
  brief_stale: boolean;
  result: ResearchResponse | null;
  pilot_form: PilotForm;
  selected_pilot_shop_ids: string[];
  pilot_shop_outreach?: Record<string, PilotShopOutreach>;
  shop_pilot_results?: Record<string, ShopPilotResult>;
  pilot_review?: PilotReviewResponse | null;
  pilot_history?: PilotRound[];
  copilot_messages?: CopilotMessage[];
  copilot_preferred_name?: string | null;
};

type WorkspaceBackup = {
  app: "MarketSarthi";
  backup_version: 1;
  exported_at: string;
  workspace: PersistedWorkspace;
};

const WORKSPACE_STORAGE_KEY = "marketsarthi:workspace:v1";
const MAX_BACKUP_BYTES = 5_000_000;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function backupContainsForbiddenData(value: unknown) {
  const forbiddenKeys = new Set([
    "api_key",
    "serpapi_key",
    "deepseek_api_key",
    "gemini_api_key",
    "authorization",
    "access_token",
    "refresh_token",
    "password",
  ]);
  const pending: unknown[] = [value];
  while (pending.length > 0) {
    const current = pending.pop();
    if (Array.isArray(current)) {
      pending.push(...current);
      continue;
    }
    if (!isRecord(current)) continue;
    for (const [key, nested] of Object.entries(current)) {
      if (forbiddenKeys.has(key.toLowerCase())) return true;
      if (key.toLowerCase().endsWith("_url") && typeof nested === "string") {
        try {
          const protocol = new URL(nested).protocol;
          if (protocol !== "http:" && protocol !== "https:") return true;
        } catch {
          return true;
        }
      }
      pending.push(nested);
    }
  }
  return false;
}

function isPilotRoundBackup(value: unknown): value is PilotRound {
  if (!isRecord(value)) return false;
  const outcomeValues = new Set([
    "continue_small_test",
    "modify_and_retest",
    "investigate_before_next_test",
    "stop_and_review",
  ]);
  const requiredStrings = [
    "id",
    "signature",
    "saved_at",
    "product_name",
    "city",
    "summary",
    "next_experiment",
    "learning_notes",
  ];
  const requiredNumbers = [
    "duration_days",
    "test_price_inr",
    "actual_packets_given",
    "packets_bought",
    "packets_returned",
    "shops_asking_another_batch",
    "bought_percent",
    "returned_percent",
  ];
  return requiredStrings.every((key) => typeof value[key] === "string")
    && requiredNumbers.every((key) => typeof value[key] === "number" && Number.isFinite(value[key]))
    && typeof value.outcome === "string"
    && outcomeValues.has(value.outcome)
    && (value.net_cash_result_inr === null
      || (typeof value.net_cash_result_inr === "number" && Number.isFinite(value.net_cash_result_inr)))
    && (value.experiment_change_type === undefined || typeof value.experiment_change_type === "string")
    && (value.experiment_change_description === undefined || typeof value.experiment_change_description === "string");
}

function validateWorkspaceBackup(value: unknown): PersistedWorkspace | null {
  if (!isRecord(value) || value.app !== "MarketSarthi" || value.backup_version !== 1) {
    return null;
  }
  const workspace = value.workspace;
  if (!isRecord(workspace) || workspace.schema_version !== 1) return null;
  const workspaceForm = workspace.form;
  const workspacePilotForm = workspace.pilot_form;
  if (!isRecord(workspaceForm) || !isRecord(workspacePilotForm)) return null;
  if (!Object.keys(initialForm).every((key) => typeof workspaceForm[key] === "string")) return null;
  if (!Object.values(workspacePilotForm).every((item) => typeof item === "string")) return null;
  if (!Array.isArray(workspace.selected_pilot_shop_ids)) return null;
  if (!workspace.selected_pilot_shop_ids.every((item) => typeof item === "string")) return null;
  if (workspace.pilot_history !== undefined) {
    if (!Array.isArray(workspace.pilot_history)) return null;
    if (!workspace.pilot_history.every(isPilotRoundBackup)) return null;
  }
  if (workspace.copilot_messages !== undefined) {
    if (!Array.isArray(workspace.copilot_messages)) return null;
    if (!workspace.copilot_messages.every((message) => (
      isRecord(message)
      && typeof message.id === "string"
      && (message.role === "user" || message.role === "assistant")
      && typeof message.content === "string"
    ))) return null;
  }
  if (
    workspace.copilot_preferred_name !== undefined
    && workspace.copilot_preferred_name !== null
    && typeof workspace.copilot_preferred_name !== "string"
  ) return null;
  if (workspace.result !== null && workspace.result !== undefined) {
    if (!isRecord(workspace.result) || !isRecord(workspace.result.plan)) return null;
    if (!Array.isArray(workspace.result.plan.queries)) return null;
    if (!Array.isArray(workspace.result.city_summaries)) return null;
    if (!Array.isArray(workspace.result.tool_runs)) return null;
    if (!Array.isArray(workspace.result.evidence)) return null;
  }
  if (backupContainsForbiddenData(value)) return null;
  return workspace as unknown as PersistedWorkspace;
}

function optionalNumber(value: string) {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function extractPreferredName(value: string) {
  const match = value.trim().match(
    /\b(?:my name is|call me)\s+([a-z][a-z'’-]*(?:\s+[a-z][a-z'’-]*){0,2})(?:[.!?,]|$)/i,
  );
  if (!match) return null;
  const name = match[1].trim().slice(0, 60);
  return name === name.toLowerCase()
    ? name.replace(/\b[a-z]/g, (letter) => letter.toUpperCase())
    : name;
}

function sanitizeCopilotContent(value: string) {
  return value
    .replace(/^\s*(?:[-*]\s*)?(?:evidence|source)\s*ids?\s*:.*(?:\r?\n|$)/gim, "")
    .replace(/\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b/gim, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function safeFilenamePart(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "city";
}

function outreachStatusLabel(status: OutreachStatus) {
  if (status === "contacted") return "Contacted — waiting for reply";
  if (status === "interested") return "Interested — discussing terms";
  if (status === "confirmed") return "Confirmed for this pilot";
  if (status === "declined") return "Not participating";
  return "Not contacted yet";
}

function pilotOutcomeLabel(outcome: PilotReviewResponse["facts"]["outcome"]) {
  if (outcome === "continue_small_test") return "Continue with another small test";
  if (outcome === "modify_and_retest") return "Change one thing and test again";
  if (outcome === "stop_and_review") return "Pause and review before placing more stock";
  return "Resolve the gaps before the next test";
}

function pilotChangeLabel(changeType: PilotChangeType | undefined) {
  if (changeType === "repeat_same") return "Repeat the same test";
  if (changeType === "price") return "Price";
  if (changeType === "pack_size") return "Pack size";
  if (changeType === "product") return "Product or recipe";
  if (changeType === "shop_type") return "Type of shop";
  if (changeType === "display_message") return "Display or sales message";
  if (changeType === "other") return "Another change";
  return "First recorded round";
}

function pilotRoundSignature(productName: string, pilotForm: PilotForm) {
  return JSON.stringify({ productName, ...pilotForm });
}

function EvidenceGroup({
  groupKey,
  title,
  description,
  items,
  tone,
  isOpen,
  onToggle,
}: {
  groupKey: string;
  title: string;
  description: string;
  items: EvidenceItem[];
  tone: string;
  isOpen: boolean;
  onToggle: (groupKey: string) => void;
}) {
  if (items.length === 0) return null;

  const contentId = `evidence-${groupKey}`;

  return (
    <section className={`evidence-group ${tone} ${isOpen ? "open" : ""}`}>
      <button
        className="evidence-group-heading"
        type="button"
        aria-expanded={isOpen}
        aria-controls={contentId}
        onClick={() => onToggle(groupKey)}
      >
        <div>
          <h4>{title}</h4>
          <p>{description}</p>
        </div>
        <span className="accordion-meta"><b>{items.length}</b><i aria-hidden="true">⌄</i></span>
      </button>
      {isOpen && <div className="evidence-list" id={contentId}>
        {items.slice(0, 12).map((item) => (
          <article key={item.id}>
            <span className="evidence-origin">
              <strong>{item.provider} · {engineLabel(item.engine)}</strong>
              <small>{scopeLabel(item.evidence_scope, item.engine)}</small>
            </span>
            <div>
              <h5>{item.title}</h5>
              <p>{item.observation}</p>
              {Array.isArray(item.metrics.themes) && item.metrics.themes.length > 0 && (
                <div className="theme-tags">
                  {(item.metrics.themes as string[]).map((theme) => (
                    <span key={theme}>{theme.replaceAll("_", " ")}</span>
                  ))}
                </div>
              )}
              {item.classification_reason && (
                <small className="classification-reason">Why: {item.classification_reason}</small>
              )}
              {item.classification_source && (
                <small className="classification-source">
                  Classified by {item.classification_source}
                  {typeof item.classification_confidence === "number"
                    ? ` · ${Math.round(item.classification_confidence * 100)}% confidence`
                    : ""}
                </small>
              )}
              <small className="evidence-time">Checked for this report: {formatEvidenceTimestamp(item.retrieved_at)}</small>
            </div>
            {item.source_url && (
              <a href={item.source_url} target="_blank" rel="noreferrer">
                Source ↗
              </a>
            )}
          </article>
        ))}
      </div>}
    </section>
  );
}

export default function Home() {
  const [appView, setAppView] = useState<AppView>("prepare");
  const [resultsTab, setResultsTab] = useState<ResultsTab>("overview");
  const [form, setForm] = useState(initialForm);
  const [researchBrief, setResearchBrief] = useState("");
  const [briefDetails, setBriefDetails] = useState<BriefDetails | null>(null);
  const [briefModel, setBriefModel] = useState<string | null>(null);
  const [briefWarnings, setBriefWarnings] = useState<string[]>([]);
  const [briefStale, setBriefStale] = useState(false);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [freshnessClock] = useState(() => Date.now());
  const [planOpen, setPlanOpen] = useState(true);
  const [openPlanEngine, setOpenPlanEngine] = useState<string | null>("google_shopping");
  const [toolTraceOpen, setToolTraceOpen] = useState(false);
  const [comparisonOpen, setComparisonOpen] = useState(true);
  const [scorecardOpen, setScorecardOpen] = useState(true);
  const [evidenceLedgerOpen, setEvidenceLedgerOpen] = useState(true);
  const [openEvidenceGroup, setOpenEvidenceGroup] = useState<string | null>("direct");
  const [pilotForm, setPilotForm] = useState<PilotForm>(initialPilotForm);
  const [pilotError, setPilotError] = useState<string | null>(null);
  const [selectedPilotShopIds, setSelectedPilotShopIds] = useState<string[]>([]);
  const [pilotShopOutreach, setPilotShopOutreach] = useState<Record<string, PilotShopOutreach>>({});
  const [shopPilotResults, setShopPilotResults] = useState<Record<string, ShopPilotResult>>({});
  const [pilotReview, setPilotReview] = useState<PilotReviewResponse | null>(null);
  const [pilotReviewLoading, setPilotReviewLoading] = useState(false);
  const [pilotReviewError, setPilotReviewError] = useState<string | null>(null);
  const [pilotHistory, setPilotHistory] = useState<PilotRound[]>([]);
  const [pilotHistoryMessage, setPilotHistoryMessage] = useState<string | null>(null);
  const [backupMessage, setBackupMessage] = useState<string | null>(null);
  const backupInputRef = useRef<HTMLInputElement>(null);
  const [storageReady, setStorageReady] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"loading" | "saving" | "saved" | "unavailable">("loading");
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState<"brief" | "preview" | "analyze" | null>(null);
  const [refreshingSection, setRefreshingSection] = useState<RefreshSection | "all" | null>(null);
  const [decisionSummaryLoading, setDecisionSummaryLoading] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotQuestion, setCopilotQuestion] = useState("");
  const [copilotMessages, setCopilotMessages] = useState<CopilotMessage[]>([]);
  const [copilotPreferredName, setCopilotPreferredName] = useState<string | null>(null);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotError, setCopilotError] = useState<string | null>(null);
  const copilotEndRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const restoreTimer = window.setTimeout(() => {
      try {
        const rawWorkspace = window.localStorage.getItem(WORKSPACE_STORAGE_KEY);
        if (rawWorkspace) {
          const workspace = JSON.parse(rawWorkspace) as Partial<PersistedWorkspace>;
          if (
            workspace.schema_version === 1
            && workspace.form
            && workspace.pilot_form
            && Array.isArray(workspace.selected_pilot_shop_ids)
          ) {
            setForm(workspace.form);
            setResearchBrief(workspace.research_brief ?? "");
            setBriefDetails(workspace.brief_details ?? null);
            setBriefModel(workspace.brief_model ?? null);
            setBriefWarnings(Array.isArray(workspace.brief_warnings) ? workspace.brief_warnings : []);
            setBriefStale(Boolean(workspace.brief_stale));
            setResult(workspace.result ?? null);
            setPilotForm({ ...initialPilotForm, ...workspace.pilot_form });
            setSelectedPilotShopIds(workspace.selected_pilot_shop_ids);
            setPilotShopOutreach(
              workspace.pilot_shop_outreach && typeof workspace.pilot_shop_outreach === "object"
                ? workspace.pilot_shop_outreach
                : {},
            );
            setShopPilotResults(
              workspace.shop_pilot_results && typeof workspace.shop_pilot_results === "object"
                ? workspace.shop_pilot_results
                : {},
            );
            setPilotReview(workspace.pilot_review ?? null);
            setPilotHistory(
              Array.isArray(workspace.pilot_history) ? workspace.pilot_history.slice(0, 12) : [],
            );
            const restoredCopilotMessages = Array.isArray(workspace.copilot_messages)
              ? workspace.copilot_messages.slice(-30).map((message) => ({
                  ...message,
                  content: sanitizeCopilotContent(message.content),
                }))
              : [];
            setCopilotMessages(restoredCopilotMessages);
            const nameFromOlderChat = [...restoredCopilotMessages]
              .reverse()
              .find((message) => message.role === "user" && extractPreferredName(message.content));
            setCopilotPreferredName(
              typeof workspace.copilot_preferred_name === "string"
                ? workspace.copilot_preferred_name
                : nameFromOlderChat
                  ? extractPreferredName(nameFromOlderChat.content)
                  : null,
            );
            setSavedAt(workspace.saved_at ?? null);
            if (workspace.result) {
              setOpenPlanEngine(
                workspace.result.plan.queries.some((query) => query.engine === "google_shopping")
                  ? "google_shopping"
                  : workspace.result.plan.queries[0]?.engine ?? "google_maps",
              );
            }
          }
        }
        setSaveStatus("saved");
      } catch {
        setSaveStatus("unavailable");
      } finally {
        setStorageReady(true);
      }
    }, 0);

    return () => window.clearTimeout(restoreTimer);
  }, []);

  useEffect(() => {
    if (!storageReady) return;

    const statusTimer = window.setTimeout(() => setSaveStatus("saving"), 0);
    const saveTimer = window.setTimeout(() => {
      const saved_at = new Date().toISOString();
      const workspace: PersistedWorkspace = {
        schema_version: 1,
        saved_at,
        form,
        research_brief: researchBrief,
        brief_details: briefDetails,
        brief_model: briefModel,
        brief_warnings: briefWarnings,
        brief_stale: briefStale,
        result,
        pilot_form: pilotForm,
        selected_pilot_shop_ids: selectedPilotShopIds,
        pilot_shop_outreach: pilotShopOutreach,
        shop_pilot_results: shopPilotResults,
        pilot_review: pilotReview,
        pilot_history: pilotHistory,
        copilot_messages: copilotMessages,
        copilot_preferred_name: copilotPreferredName,
      };
      try {
        window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(workspace));
        setSavedAt(saved_at);
        setSaveStatus("saved");
      } catch {
        setSaveStatus("unavailable");
      }
    }, 400);

    return () => {
      window.clearTimeout(statusTimer);
      window.clearTimeout(saveTimer);
    };
  }, [
    briefDetails,
    briefModel,
    briefStale,
    briefWarnings,
    copilotMessages,
    copilotPreferredName,
    form,
    pilotForm,
    pilotHistory,
    pilotShopOutreach,
    pilotReview,
    researchBrief,
    result,
    selectedPilotShopIds,
    shopPilotResults,
    storageReady,
  ]);

  useEffect(() => {
    if (copilotOpen) {
      copilotEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [copilotLoading, copilotMessages, copilotOpen]);

  const payload = useMemo(
    () => ({
      ...form,
      target_cities: form.target_cities.split(",").map((item) => item.trim()).filter(Boolean),
      price_min_inr: Number(form.price_min_inr),
      price_max_inr: Number(form.price_max_inr),
      differentiators: form.differentiators.split(",").map((item) => item.trim()).filter(Boolean),
      constraints: form.constraints.split(",").map((item) => item.trim()).filter(Boolean),
      research_brief: researchBrief || null,
      language: "English",
    }),
    [form, researchBrief],
  );

  const evidenceGroups = useMemo(() => {
    const evidence = result?.evidence ?? [];
    return {
      direct: evidence.filter((item) => item.competitor_type === "direct"),
      alternative: evidence.filter((item) => item.competitor_type === "alternative"),
      uncertain: evidence.filter((item) => item.competitor_type === "uncertain"),
      customerVoice: evidence.filter((item) => item.evidence_type === "review"),
      verifiedLocal: evidence.filter((item) =>
        ["local_channel", "local_competitor"].includes(item.evidence_type)
        && item.channel_status === "verified_product_mention",
      ),
      potentialLocal: evidence.filter((item) =>
        ["local_channel", "local_competitor"].includes(item.evidence_type)
        && item.channel_status !== "verified_product_mention",
      ),
      trends: evidence.filter((item) => item.evidence_type === "trend"),
      web: evidence.filter((item) => item.evidence_type === "web"),
      news: evidence.filter((item) => item.evidence_type === "news"),
    };
  }, [result]);

  const researchFreshness = useMemo(() => {
    const timestamps = (result?.evidence ?? [])
      .map((item) => item.retrieved_at ? new Date(item.retrieved_at).getTime() : Number.NaN)
      .filter(Number.isFinite);
    if (timestamps.length === 0) return null;

    const newestTimestamp = Math.max(...timestamps);
    const oldestTimestamp = Math.min(...timestamps);
    const newestAgeInDays = Math.max(0, Math.floor((freshnessClock - newestTimestamp) / 86_400_000));
    const oldestAgeInDays = Math.max(0, Math.floor((freshnessClock - oldestTimestamp) / 86_400_000));
    const mixed = oldestAgeInDays > newestAgeInDays;
    const label = mixed
      ? "Some evidence updated"
      : newestAgeInDays === 0
        ? "Checked today"
        : newestAgeInDays === 1
          ? "Checked yesterday"
          : `Checked ${newestAgeInDays} days ago`;

    return {
      exact: formatEvidenceTimestamp(new Date(newestTimestamp).toISOString()),
      oldestExact: formatEvidenceTimestamp(new Date(oldestTimestamp).toISOString()),
      label,
      mixed,
      stale: oldestAgeInDays > 7,
    };
  }, [freshnessClock, result]);

  const planEngines = useMemo(() => {
    const queries = result?.plan.queries ?? [];
    return ["google_shopping", "google_maps", "google_trends", "google", "google_news"]
      .map((engine) => ({
        engine,
        count: queries.filter((query) => query.engine === engine).length,
      }))
      .filter((item) => item.count > 0);
  }, [result]);

  const hasLiveResult = Boolean(result && result.mode !== "plan_only");
  const planMatchesCurrentBrief = Boolean(
    result?.mode === "plan_only"
    && result.plan.approved_brief === researchBrief
    && !briefStale,
  );
  const plannedCities = useMemo(
    () => new Set((result?.plan.queries ?? []).map((query) => query.city)).size,
    [result],
  );
  const uniqueResultWarnings = useMemo(
    () => Array.from(new Set(result?.warnings ?? [])),
    [result],
  );
  const copilotQuickStart = useMemo(() => {
    const cities = result && result.mode !== "plan_only"
      ? Array.from(new Set(result.city_summaries.map((summary) => summary.city.split(",")[0].trim())))
      : [];
    if (cities.length === 0) {
      return {
        description: "Ask how MarketSarthi works, what information to enter, or how to begin live research.",
        prompts: [
          "How does MarketSarthi work?",
          "What should I enter first?",
          "How do I start research?",
        ],
      };
    }
    if (cities.length === 1) {
      return {
        description: `Ask about saved prices, ${cities[0]}, possible shops, evidence gaps, or your next step.`,
        prompts: [
          "What prices did we find?",
          `What did we learn about ${cities[0]}?`,
          "What should I do next?",
        ],
      };
    }
    const cityLabel = cities.length === 2
      ? `${cities[0]} and ${cities[1]}`
      : "the researched cities";
    return {
      description: `Ask about saved prices, ${cityLabel}, possible shops, evidence gaps, or your next step.`,
      prompts: [
        "What prices did we find?",
        `Compare ${cityLabel}.`,
        "What should I do next?",
      ],
    };
  }, [result]);

  const researchQuestions = useMemo(() => {
    const questions = new Map<string, {
      question: string;
      city: string;
      planned: number;
      engines: Set<string>;
    }>();
    for (const query of result?.plan.queries ?? []) {
      const key = `${query.city}::${query.research_question}`;
      const current = questions.get(key) ?? {
        question: query.research_question,
        city: query.city,
        planned: 0,
        engines: new Set<string>(),
      };
      current.planned += 1;
      current.engines.add(query.engine);
      questions.set(key, current);
    }
    return Array.from(questions.entries()).map(([key, question]) => {
      const runs = (result?.tool_runs ?? []).filter(
        (run) => `${run.city}::${run.research_question}` === key,
      );
      const hasAnswer = runs.some(
        (run) => run.status === "success" && run.result_count > 0,
      );
      const hasGap = runs.some((run) => run.status !== "success");
      let status = result?.mode === "plan_only" ? "Planned" : "Not answered";
      if (hasAnswer) status = hasGap ? "Answered with gaps" : "Answered";
      else if (runs.length === 0 && result?.mode !== "plan_only") status = "Not needed";
      return {
        ...question,
        engines: Array.from(question.engines),
        attempted: runs.length,
        status,
      };
    });
  }, [result]);

  const pilotState = useMemo(() => {
    const duration = optionalNumber(pilotForm.duration_days);
    const units = optionalNumber(pilotForm.units_planned);
    const shops = optionalNumber(pilotForm.shops_planned);
    const price = optionalNumber(pilotForm.test_price_inr);
    const targetSellThrough = optionalNumber(pilotForm.target_sell_through_percent);
    const maxReturn = optionalNumber(pilotForm.max_return_percent);
    const actualUnitsPlaced = optionalNumber(pilotForm.actual_units_placed);
    const unitsSold = optionalNumber(pilotForm.units_sold);
    const unitsReturned = optionalNumber(pilotForm.units_returned);
    const unitsDamaged = optionalNumber(pilotForm.units_damaged);
    const unitsMissing = optionalNumber(pilotForm.units_missing);
    const unitsStillAtShops = optionalNumber(pilotForm.units_still_at_shops);
    const shopsWilling = optionalNumber(pilotForm.shops_willing_to_continue);
    const moneyReceived = optionalNumber(pilotForm.money_received_inr);
    const nonrecoverableCosts = optionalNumber(pilotForm.nonrecoverable_costs_inr);
    const maximumAcceptableLoss = optionalNumber(pilotForm.maximum_acceptable_loss_inr);
    const errors: string[] = [];

    if (!pilotForm.city) errors.push("Choose a pilot city.");
    if (duration === null || duration <= 0 || !Number.isInteger(duration)) errors.push("Enter the pilot duration as whole days.");
    if (units === null || units <= 0 || !Number.isInteger(units)) errors.push("Enter the planned units as a positive whole number.");
    if (shops === null || shops <= 0 || !Number.isInteger(shops)) errors.push("Enter the number of shops as a positive whole number.");
    if (price === null || price <= 0) errors.push("Enter a positive test price.");
    if (targetSellThrough === null || targetSellThrough < 0 || targetSellThrough > 100) errors.push("Enter the target percentage of packets customers should buy, from 0 to 100%.");
    if (maxReturn === null || maxReturn < 0 || maxReturn > 100) errors.push("Enter the highest percentage of packets that may be returned, from 0 to 100%.");
    if (actualUnitsPlaced !== null && (actualUnitsPlaced <= 0 || !Number.isInteger(actualUnitsPlaced))) {
      errors.push("Packets given to shops must be a positive whole number.");
    }

    for (const [label, value] of [
      ["Packets customers bought", unitsSold],
      ["Unsold packets returned to you", unitsReturned],
      ["Damaged packets", unitsDamaged],
      ["Missing packets", unitsMissing],
      ["Packets still at shops", unitsStillAtShops],
      ["Shops asking for another batch", shopsWilling],
    ] as const) {
      if (value !== null && (value < 0 || !Number.isInteger(value))) errors.push(`${label} must be zero or a positive whole number.`);
    }
    const stockCounts = [unitsSold, unitsReturned, unitsDamaged, unitsMissing, unitsStillAtShops];
    const hasAnyStockCount = stockCounts.some((value) => value !== null);
    const hasCompleteStockCount = stockCounts.every((value) => value !== null);
    if (hasAnyStockCount && actualUnitsPlaced === null) {
      errors.push("Enter how many packets you gave to the shops before calculating the result.");
    }
    if (hasAnyStockCount && !hasCompleteStockCount) {
      errors.push("Complete all five packet counts. Enter 0 when none were damaged, missing, or left at shops.");
    }
    const accountedPackets = hasCompleteStockCount
      ? stockCounts.reduce<number>((total, value) => total + (value ?? 0), 0)
      : null;
    if (actualUnitsPlaced !== null && accountedPackets !== null && accountedPackets > actualUnitsPlaced) {
      errors.push("The packet counts cannot add up to more than the packets given to shops.");
    }
    if (shops !== null && shopsWilling !== null && shopsWilling > shops) {
      errors.push("Shops asking for another batch cannot be more than the shops in the test.");
    }
    if (shops !== null && selectedPilotShopIds.length > shops) {
      errors.push("The shop shortlist cannot contain more shops than the planned pilot.");
    }
    const moneyValues = [moneyReceived, nonrecoverableCosts, maximumAcceptableLoss];
    const hasAnyMoneyValue = moneyValues.some((value) => value !== null);
    const hasMoneyCheck = moneyValues.every((value) => value !== null);
    if (hasAnyMoneyValue && !hasMoneyCheck) {
      errors.push("Fill in all three money boxes, or leave all three blank.");
    }
    if (moneyValues.some((value) => value !== null && value < 0)) {
      errors.push("The money amounts cannot be below zero.");
    }
    if (pilotHistory.length > 0 && !pilotForm.experiment_change_type) {
      errors.push("Choose the one main thing you changed for this new test round.");
    }
    if (
      pilotHistory.length > 0
      && pilotForm.experiment_change_type
      && pilotForm.experiment_change_description.trim().length < 3
    ) {
      errors.push("Briefly explain what you kept the same or changed in this round.");
    }

    const hasMeasuredResults = actualUnitsPlaced !== null && hasCompleteStockCount;
    const sellThrough = hasMeasuredResults && actualUnitsPlaced > 0 ? (unitsSold ?? 0) / actualUnitsPlaced * 100 : null;
    const returnRate = hasMeasuredResults && actualUnitsPlaced > 0 ? (unitsReturned ?? 0) / actualUnitsPlaced * 100 : null;
    const packetsUnexplained = hasMeasuredResults && accountedPackets !== null
      ? actualUnitsPlaced - accountedPackets
      : null;
    const netCashResult = hasMoneyCheck && moneyReceived !== null && nonrecoverableCosts !== null
      ? moneyReceived - nonrecoverableCosts
      : null;
    const cashCheckMet = netCashResult !== null && maximumAcceptableLoss !== null
      ? netCashResult >= -maximumAcceptableLoss
      : null;
    let decision = "Results not entered yet";
    if (
      sellThrough !== null
      && returnRate !== null
      && targetSellThrough !== null
      && maxReturn !== null
    ) {
      const productChecksMet = sellThrough >= targetSellThrough && returnRate <= maxReturn;
      const stockNeedsChecking = (unitsMissing ?? 0) > 0
        || (unitsStillAtShops ?? 0) > 0
        || (packetsUnexplained ?? 0) > 0;
      if (stockNeedsChecking) {
        decision = "Finish checking the packet counts before the next test";
      } else if ((unitsDamaged ?? 0) > 0) {
        decision = "Check why packets were damaged, then run a small retest";
      } else if (productChecksMet && cashCheckMet === false) {
        decision = "Product targets were reached, but the test spent more than your limit";
      } else {
        decision = productChecksMet
          ? "Your test reached the targets you set"
          : "Check the test results before expanding";
      }
    }

    return {
      duration,
      units,
      shops,
      price,
      targetSellThrough,
      maxReturn,
      actualUnitsPlaced,
      unitsSold,
      unitsReturned,
      unitsDamaged,
      unitsMissing,
      unitsStillAtShops,
      packetsUnexplained,
      shopsWilling,
      moneyReceived,
      nonrecoverableCosts,
      maximumAcceptableLoss,
      hasMoneyCheck,
      netCashResult,
      cashCheckMet,
      errors,
      hasMeasuredResults,
      sellThrough,
      returnRate,
      decision,
    };
  }, [pilotForm, pilotHistory.length, selectedPilotShopIds]);

  const selectedPilotSummary = useMemo(
    () => result?.city_summaries.find((summary) => summary.city === pilotForm.city) ?? null,
    [pilotForm.city, result],
  );
  const currentPilotRoundSignature = useMemo(
    () => pilotRoundSignature(form.product_name, pilotForm),
    [form.product_name, pilotForm],
  );
  const currentPilotRoundSaved = pilotHistory.some(
    (round) => round.signature === currentPilotRoundSignature,
  );
  const pilotRoundComparison = pilotHistory.length >= 2
    ? {
        bought: pilotHistory[0].bought_percent - pilotHistory[1].bought_percent,
        returned: pilotHistory[0].returned_percent - pilotHistory[1].returned_percent,
        money: pilotHistory[0].net_cash_result_inr !== null
          && pilotHistory[1].net_cash_result_inr !== null
          ? pilotHistory[0].net_cash_result_inr - pilotHistory[1].net_cash_result_inr
          : null,
      }
    : null;

  const pilotShopLeads = useMemo(
    () => (result?.evidence ?? []).filter(
      (item) => item.evidence_type === "local_channel" && item.city === pilotForm.city,
    ),
    [pilotForm.city, result],
  );

  const selectedPilotShops = useMemo(
    () => pilotShopLeads.filter((item) => selectedPilotShopIds.includes(item.id)),
    [pilotShopLeads, selectedPilotShopIds],
  );

  const outreachSummary = useMemo(() => {
    const statuses = selectedPilotShops.map(
      (shop) => pilotShopOutreach[shop.id]?.status ?? "not_contacted",
    );
    return {
      confirmed: statuses.filter((status) => status === "confirmed").length,
      interested: statuses.filter((status) => status === "interested").length,
      waiting: statuses.filter((status) => status === "contacted").length,
      declined: statuses.filter((status) => status === "declined").length,
    };
  }, [pilotShopOutreach, selectedPilotShops]);

  const confirmedPilotShops = useMemo(
    () => selectedPilotShops.filter(
      (shop) => pilotShopOutreach[shop.id]?.status === "confirmed",
    ),
    [pilotShopOutreach, selectedPilotShops],
  );

  const shopMeasurementState = useMemo(() => {
    const errors: string[] = [];
    const rows = confirmedPilotShops.map((shop) => {
      const storedEntry = shopPilotResults[shop.id];
      const entry: ShopPilotResult = {
        units_placed: storedEntry?.units_placed ?? "",
        units_sold: storedEntry?.units_sold ?? "",
        units_returned: storedEntry?.units_returned ?? "",
        units_damaged: storedEntry?.units_damaged ?? "",
        units_missing: storedEntry?.units_missing ?? "",
        units_still_at_shop: storedEntry?.units_still_at_shop ?? "",
        continuation: storedEntry?.continuation ?? "not_recorded",
        notes: storedEntry?.notes ?? "",
      };
      const placed = optionalNumber(entry.units_placed);
      const sold = optionalNumber(entry.units_sold);
      const returned = optionalNumber(entry.units_returned);
      const damaged = optionalNumber(entry.units_damaged);
      const missing = optionalNumber(entry.units_missing);
      const stillAtShop = optionalNumber(entry.units_still_at_shop);

      if (placed === null || placed <= 0 || !Number.isInteger(placed)) {
        errors.push(`${shop.title}: enter the packets given to this shop as a positive whole number.`);
      }
      if (sold === null || sold < 0 || !Number.isInteger(sold)) {
        errors.push(`${shop.title}: enter the packets customers bought as zero or a positive whole number.`);
      }
      if (returned === null || returned < 0 || !Number.isInteger(returned)) {
        errors.push(`${shop.title}: enter the unsold packets returned to you as zero or a positive whole number.`);
      }
      for (const [label, value] of [
        ["damaged packets", damaged],
        ["missing packets", missing],
        ["packets still at this shop", stillAtShop],
      ] as const) {
        if (value === null || value < 0 || !Number.isInteger(value)) {
          errors.push(`${shop.title}: enter ${label} as zero or a positive whole number.`);
        }
      }
      const accounted = [sold, returned, damaged, missing, stillAtShop].every((value) => value !== null)
        ? (sold ?? 0) + (returned ?? 0) + (damaged ?? 0) + (missing ?? 0) + (stillAtShop ?? 0)
        : null;
      if (placed !== null && accounted !== null && accounted > placed) {
        errors.push(`${shop.title}: the packet counts cannot add up to more than packets given to the shop.`);
      }
      if (placed !== null && accounted !== null && accounted < placed) {
        errors.push(`${shop.title}: explain all ${placed} packets across bought, returned, damaged, missing, or still at this shop.`);
      }

      return { shop, entry, placed, sold, returned, damaged, missing, stillAtShop };
    });

    return {
      rows,
      errors,
      complete: rows.length > 0 && errors.length === 0,
      totalPlaced: rows.reduce((sum, row) => sum + (row.placed ?? 0), 0),
      totalSold: rows.reduce((sum, row) => sum + (row.sold ?? 0), 0),
      totalReturned: rows.reduce((sum, row) => sum + (row.returned ?? 0), 0),
      totalDamaged: rows.reduce((sum, row) => sum + (row.damaged ?? 0), 0),
      totalMissing: rows.reduce((sum, row) => sum + (row.missing ?? 0), 0),
      totalStillAtShops: rows.reduce((sum, row) => sum + (row.stillAtShop ?? 0), 0),
      shopsContinuing: rows.filter((row) => row.entry.continuation === "yes").length,
    };
  }, [confirmedPilotShops, shopPilotResults]);

  function updatePilotField<K extends keyof PilotForm>(field: K, value: PilotForm[K]) {
    setPilotForm((current) => ({ ...current, [field]: value }));
    setPilotError(null);
    setPilotReview(null);
    setPilotReviewError(null);
    setPilotHistoryMessage(null);
  }

  function updatePilotCity(city: string) {
    setPilotForm((current) => ({ ...current, city }));
    setSelectedPilotShopIds([]);
    setPilotShopOutreach({});
    setShopPilotResults({});
    setPilotError(null);
    setPilotReview(null);
    setPilotReviewError(null);
    setPilotHistoryMessage(null);
  }

  function togglePilotShop(id: string) {
    const removing = selectedPilotShopIds.includes(id);
    setSelectedPilotShopIds((current) => (
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    ));
    setPilotShopOutreach((current) => {
      if (!removing) {
        return {
          ...current,
          [id]: current[id] ?? { status: "not_contacted", notes: "" },
        };
      }
      const next = { ...current };
      delete next[id];
      return next;
    });
    if (removing) {
      setShopPilotResults((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
    }
    setPilotError(null);
    setPilotReview(null);
    setPilotReviewError(null);
  }

  function updatePilotShopOutreach(id: string, changes: Partial<PilotShopOutreach>) {
    setPilotShopOutreach((current) => ({
      ...current,
      [id]: {
        status: current[id]?.status ?? "not_contacted",
        notes: current[id]?.notes ?? "",
        ...changes,
      },
    }));
    setPilotReview(null);
    setPilotReviewError(null);
  }

  function updateShopPilotResult(id: string, changes: Partial<ShopPilotResult>) {
    setShopPilotResults((current) => ({
      ...current,
      [id]: {
        units_placed: current[id]?.units_placed ?? "",
        units_sold: current[id]?.units_sold ?? "",
        units_returned: current[id]?.units_returned ?? "",
        units_damaged: current[id]?.units_damaged ?? "",
        units_missing: current[id]?.units_missing ?? "",
        units_still_at_shop: current[id]?.units_still_at_shop ?? "",
        continuation: current[id]?.continuation ?? "not_recorded",
        notes: current[id]?.notes ?? "",
        ...changes,
      },
    }));
    setPilotError(null);
    setPilotReview(null);
    setPilotReviewError(null);
  }

  function applyShopMeasurementTotals() {
    if (!shopMeasurementState.complete) {
      setPilotError(shopMeasurementState.errors[0] ?? "Complete the shop measurements first.");
      return;
    }
    setPilotForm((current) => ({
      ...current,
      actual_units_placed: String(shopMeasurementState.totalPlaced),
      units_sold: String(shopMeasurementState.totalSold),
      units_returned: String(shopMeasurementState.totalReturned),
      units_damaged: String(shopMeasurementState.totalDamaged),
      units_missing: String(shopMeasurementState.totalMissing),
      units_still_at_shops: String(shopMeasurementState.totalStillAtShops),
      shops_willing_to_continue: String(shopMeasurementState.shopsContinuing),
    }));
    setPilotError(null);
    setPilotReview(null);
    setPilotReviewError(null);
  }

  function savePilotRound() {
    if (
      !pilotReview
      || pilotState.duration === null
      || pilotState.price === null
      || pilotState.actualUnitsPlaced === null
      || pilotState.unitsSold === null
      || pilotState.unitsReturned === null
      || pilotState.shopsWilling === null
    ) {
      setPilotHistoryMessage("Review the completed pilot before saving this round.");
      return;
    }
    if (currentPilotRoundSaved) {
      setPilotHistoryMessage("This pilot round is already saved.");
      return;
    }

    const savedRound: PilotRound = {
      id: globalThis.crypto?.randomUUID?.() ?? `pilot-${Date.now()}`,
      signature: currentPilotRoundSignature,
      saved_at: new Date().toISOString(),
      product_name: form.product_name,
      city: pilotForm.city,
      duration_days: pilotState.duration,
      test_price_inr: pilotState.price,
      actual_packets_given: pilotState.actualUnitsPlaced,
      packets_bought: pilotState.unitsSold,
      packets_returned: pilotState.unitsReturned,
      packets_damaged: pilotState.unitsDamaged ?? 0,
      packets_missing: pilotState.unitsMissing ?? 0,
      packets_still_at_shops: pilotState.unitsStillAtShops ?? 0,
      shops_asking_another_batch: pilotState.shopsWilling,
      bought_percent: pilotReview.facts.bought_percent,
      returned_percent: pilotReview.facts.returned_percent,
      net_cash_result_inr: pilotReview.facts.net_cash_result_inr ?? null,
      outcome: pilotReview.facts.outcome,
      summary: pilotReview.review.summary,
      next_experiment: pilotReview.review.next_experiment,
      learning_notes: pilotForm.learning_notes.trim(),
      experiment_change_type: pilotForm.experiment_change_type,
      experiment_change_description: pilotForm.experiment_change_description.trim(),
    };
    setPilotHistory((current) => [savedRound, ...current].slice(0, 12));
    setPilotHistoryMessage("Pilot round saved in this browser.");
  }

  function removePilotRound(round: PilotRound) {
    const savedDate = new Date(round.saved_at).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
    const confirmed = window.confirm(
      `Remove the ${round.city} pilot round saved on ${savedDate}? This removes only this saved history record. Your current form and research will stay unchanged.`,
    );
    if (!confirmed) return;

    setPilotHistory((current) => current.filter((item) => item.id !== round.id));
    setPilotHistoryMessage(`Removed the ${round.city} pilot round saved on ${savedDate}.`);
  }

  function startNextPilotRound() {
    setPilotForm((current) => ({
      ...current,
      actual_units_placed: "",
      units_sold: "",
      units_returned: "",
      units_damaged: "",
      units_missing: "",
      units_still_at_shops: "",
      shops_willing_to_continue: "",
      money_received_inr: "",
      nonrecoverable_costs_inr: "",
      maximum_acceptable_loss_inr: "",
      experiment_change_type: "",
      experiment_change_description: "",
      learning_notes: "",
    }));
    setShopPilotResults({});
    setPilotReview(null);
    setPilotReviewError(null);
    setPilotError(null);
    setPilotHistoryMessage("New round started. Your city, test plan and shop shortlist were kept.");
  }

  function downloadPilotReport() {
    if (!result || !selectedPilotSummary || pilotState.errors.length > 0) {
      setPilotError(pilotState.errors[0] ?? "Run live analysis before creating a pilot report.");
      return;
    }

    const sources = result.evidence
      .filter((item) => item.source_url && (item.city === pilotForm.city || item.city === "India"))
      .filter((item, index, items) => items.findIndex((candidate) => candidate.source_url === item.source_url) === index)
      .slice(0, 15);
    const measuredResults = pilotState.hasMeasuredResults
      ? [
          `- Packets given to shops: ${pilotState.actualUnitsPlaced}`,
          `- Packets customers bought: ${pilotState.unitsSold}`,
          `- Unsold packets returned to the merchant: ${pilotState.unitsReturned}`,
          `- Damaged packets: ${pilotState.unitsDamaged}`,
          `- Missing packets: ${pilotState.unitsMissing}`,
          `- Packets still at shops: ${pilotState.unitsStillAtShops}`,
          `- Packets not explained by any count: ${pilotState.packetsUnexplained}`,
          `- Percentage of packets sold: ${pilotState.sellThrough?.toFixed(1)}%`,
          `- Percentage of packets returned: ${pilotState.returnRate?.toFixed(1)}%`,
          `- Shops asking for another batch: ${pilotState.shopsWilling ?? "Not entered"}`,
          `- Result against the merchant's targets: ${pilotState.decision}`,
        ]
      : ["- Actual results have not been entered yet."];
    const moneyCheckLines = pilotState.hasMoneyCheck
      ? [
          "## Did this small test cover its costs?",
          "",
          `- Money received from sold packets: ₹${pilotState.moneyReceived?.toFixed(2)}`,
          `- Test costs already used up: ₹${pilotState.nonrecoverableCosts?.toFixed(2)}`,
          `- Loss the merchant said was okay for this test: ₹${pilotState.maximumAcceptableLoss?.toFixed(2)}`,
          `- Money left after used-up test costs: ₹${pilotState.netCashResult?.toFixed(2)}`,
          `- Check result: ${pilotState.cashCheckMet ? "Within the amount the merchant said was okay" : "More loss than the merchant said was okay"}`,
          "- This simple test check does not predict future profit.",
          "",
        ]
      : [];
    const shopResultLines = confirmedPilotShops.length > 0
      ? confirmedPilotShops.map((shop) => {
          const entry = shopPilotResults[shop.id];
          if (
            !entry?.units_placed
            || entry.units_sold === undefined || entry.units_sold === ""
            || entry.units_returned === undefined || entry.units_returned === ""
            || entry.units_damaged === undefined || entry.units_damaged === ""
            || entry.units_missing === undefined || entry.units_missing === ""
            || entry.units_still_at_shop === undefined || entry.units_still_at_shop === ""
          ) {
            return `- ${shop.title} — Results not fully entered.`;
          }
          const continuation = entry.continuation === "yes"
            ? "willing to continue"
            : entry.continuation === "no"
              ? "not willing to continue"
              : "continuation not recorded";
          const notes = entry.notes.trim() ? ` Notes: ${entry.notes.trim()}` : "";
          return `- ${shop.title} — packets given: ${entry.units_placed}; bought: ${entry.units_sold}; returned: ${entry.units_returned}; damaged: ${entry.units_damaged}; missing: ${entry.units_missing}; still at shop: ${entry.units_still_at_shop}; ${continuation}.${notes}`;
        })
      : ["- No retailer is marked as confirmed for the pilot."];
    const shortlistedShops = selectedPilotShops.length > 0
      ? selectedPilotShops.map((item) => {
          const evidenceStatus = item.channel_status === "verified_product_mention"
            ? "A review mentions the product; call to confirm current stock and interest"
            : "Potential shop; product fit and interest are unconfirmed";
          const outreach = pilotShopOutreach[item.id] ?? { status: "not_contacted", notes: "" };
          const title = item.source_url ? `[${item.title}](${item.source_url})` : item.title;
          const notes = outreach.notes.trim() ? ` Merchant note: ${outreach.notes.trim()}` : "";
          return `- ${title} — Outreach: ${outreachStatusLabel(outreach.status)}. Evidence: ${evidenceStatus}. ${item.observation}${notes}`;
        })
      : ["- No named shops selected yet. Use the research leads and confirm participation directly."];
    const pilotReviewLines = pilotReview
      ? [
          "## Post-pilot decision review",
          "",
          `- Deterministic outcome: ${pilotOutcomeLabel(pilotReview.facts.outcome)}`,
          `- Explanation source: ${pilotReview.model_used}`,
          `- Packets not yet accounted for: ${pilotReview.facts.packets_unaccounted_for}`,
          `- Damaged packets: ${pilotReview.facts.packets_damaged ?? 0}`,
          `- Missing packets: ${pilotReview.facts.packets_missing ?? 0}`,
          `- Packets still at shops: ${pilotReview.facts.packets_still_at_shops ?? 0}`,
          "",
          pilotReview.review.summary,
          "",
          "### Recommended next experiment",
          "",
          pilotReview.review.next_experiment,
          "",
          "### What this pilot does not prove",
          "",
          ...pilotReview.review.do_not_conclude.map((item) => `- ${item}`),
          "",
        ]
      : [];
    const pilotHistoryLines = pilotHistory.length > 0
      ? [
          "## Saved pilot rounds",
          "",
          ...pilotHistory.slice(0, 5).map((round, index) => (
            `- Round ${pilotHistory.length - index}: ${round.city}, planned change: ${pilotChangeLabel(round.experiment_change_type)}${round.experiment_change_description ? ` (${round.experiment_change_description})` : ""}, ${round.bought_percent.toFixed(1)}% bought, ${round.returned_percent.toFixed(1)}% returned, damaged: ${round.packets_damaged ?? 0}, missing: ${round.packets_missing ?? 0}, still at shops: ${round.packets_still_at_shops ?? 0}, outcome: ${pilotOutcomeLabel(round.outcome)}${round.net_cash_result_inr === null ? "" : `, test money result: ₹${round.net_cash_result_inr.toFixed(2)}`}. Saved ${round.saved_at}.`
          )),
          "- These rounds are merchant-entered test records, not proof of city-wide demand or future sales.",
          "",
        ]
      : [];
    const decisionSummaryLines = result.decision_summary
      ? [
          "## Final decision summary",
          "",
          "### What we observed",
          "",
          ...result.decision_summary.observed.map((item) => `- ${item}`),
          "",
          "### What is still unknown",
          "",
          ...result.decision_summary.unknowns.map((item) => `- ${item}`),
          "",
          "### What to do next",
          "",
          ...result.decision_summary.next_actions.map((item) => `- ${item}`),
          "",
          "### What not to conclude",
          "",
          ...result.decision_summary.do_not_conclude.map((item) => `- ${item}`),
          "",
        ]
      : [];
    const sourceLines = sources.length > 0
      ? sources.map((item) => `- [${item.title}](${item.source_url}) — ${scopeLabel(item.evidence_scope, item.engine)}; checked for this report: ${formatEvidenceTimestamp(item.retrieved_at)}`)
      : ["- No source URL was available for this city."];
    const report = [
      "# MarketSarthi pilot report",
      "",
      `Generated: ${new Date().toISOString()}`,
      "",
      "> This is a merchant-defined experiment, not a sales forecast or guarantee.",
      "",
      "## Business and city",
      "",
      `- Product: ${form.product_name}`,
      `- Category: ${form.category}`,
      `- Current market: ${form.current_city}`,
      `- Pilot city: ${pilotForm.city}`,
      `- Pack size: ${form.pack_size || "Not entered"}`,
      `- Merchant price range: ₹${form.price_min_inr}–₹${form.price_max_inr}`,
      "",
      "### Merchant context",
      "",
      form.business_background.trim() || "Not entered",
      "",
      "### Expansion goal",
      "",
      form.expansion_goal.trim() || "Not entered",
      "",
      "### Approved research brief",
      "",
      researchBrief.trim() || "Not entered",
      "",
      "## Evidence snapshot",
      "",
      `- Same-product listings found: ${selectedPilotSummary.direct_competitors}`,
      `- Shops to check: ${selectedPilotSummary.local_channels}`,
      `- Shops with product mentions: ${selectedPilotSummary.verified_local_channels}`,
      `- City-specific web pages: ${selectedPilotSummary.city_specific_web_results}`,
      `- Recent city articles: ${selectedPilotSummary.city_specific_news_results}`,
      `- Relative Google Trends score: ${selectedPilotSummary.trend_interest_score ?? "Not returned"}`,
      `- Evidence coverage: ${selectedPilotSummary.evidence_coverage_percent}% (${selectedPilotSummary.evidence_dimensions_met} of ${selectedPilotSummary.evidence_dimensions_total} checks)`,
      `- Latest evidence check: ${researchFreshness?.exact ?? "Time not available"}`,
      `- Oldest preserved evidence check: ${researchFreshness?.oldestExact ?? "Time not available"}`,
      "- Evidence coverage describes research completeness, not demand or probability of success.",
      "- The check time is not the source publication time. Search results, prices and shop details can change.",
      "",
      ...decisionSummaryLines,
      "## Merchant-approved pilot setup",
      "",
      `- Duration: ${pilotState.duration} days`,
      `- Packets planned for the test: ${pilotState.units}`,
      `- Shops included: ${pilotState.shops}`,
      `- Test price: ₹${pilotState.price}`,
      `- Target percentage of packets sold: ${pilotState.targetSellThrough}%`,
      `- Highest acceptable percentage returned: ${pilotState.maxReturn}%`,
      `- Main change for this round: ${pilotChangeLabel(pilotForm.experiment_change_type)} — ${pilotForm.experiment_change_description.trim() || "Not entered"}`,
      "",
      "## Shops selected for outreach",
      "",
      ...shortlistedShops,
      "",
      `- Named shops selected: ${selectedPilotShops.length} of ${pilotState.shops} planned`,
      `- Shops confirmed by merchant: ${outreachSummary.confirmed}`,
      "- Selection is an outreach shortlist, not proof of current stock, product fit or retailer agreement.",
      "",
      "## Before starting",
      "",
      "- Call each shop and confirm current product fit, terms and available shelf space.",
      "- Confirm shelf life, packaging, labels, transport conditions and applicable compliance requirements.",
      "- Record how many packets each shop receives and use the same counting method throughout the test.",
      "",
      "## Measurements to record",
      "",
      "- Packets given to each shop, bought by customers, returned, damaged, missing, or still at the shop.",
      "- Actual selling price, discounts and retailer margin used.",
      "- Reorder requests and retailer willingness to continue.",
      "- Customer comments as individual observations, without presenting them as city-wide sentiment.",
      "",
      "## Merchant-entered results",
      "",
      ...measuredResults,
      `- Learning notes: ${pilotForm.learning_notes.trim() || "Not entered"}`,
      "",
      ...moneyCheckLines,
      "## Shop-by-shop measured results",
      "",
      ...shopResultLines,
      "",
      ...pilotReviewLines,
      ...pilotHistoryLines,
      "## Evidence sources",
      "",
      ...sourceLines,
      "",
      "## Review rule",
      "",
      "Compare the measured results with the merchant-defined thresholds above. Investigate missing stock, returns, discounting and shop-level differences before expanding. Passing these checks supports another bounded test; it does not prove city-wide demand.",
      "",
    ].join("\n");

    const blob = new Blob([report], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `marketsarthi-pilot-${safeFilenamePart(pilotForm.city)}.md`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  async function parseResponse(response: Response) {
    const body = await response.json();
    if (!response.ok) {
      const detail = body.detail?.message ?? body.detail ?? "The research request failed.";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return body;
  }

  async function generatePilotReview() {
    if (!result || !selectedPilotSummary || pilotState.errors.length > 0) {
      setPilotReviewError(
        pilotState.errors[0] ?? "Complete the measured pilot result before requesting a review.",
      );
      return;
    }
    if (
      pilotState.units === null
      || pilotState.actualUnitsPlaced === null
      || pilotState.unitsSold === null
      || pilotState.unitsReturned === null
      || pilotState.unitsDamaged === null
      || pilotState.unitsMissing === null
      || pilotState.unitsStillAtShops === null
      || pilotState.targetSellThrough === null
      || pilotState.maxReturn === null
      || pilotState.shops === null
      || pilotState.shopsWilling === null
    ) {
      setPilotReviewError(
        "Enter the actual packet totals and how many shops asked for another batch.",
      );
      return;
    }

    const shopResults = shopMeasurementState.rows.flatMap((row) => {
      if (
        row.placed === null
        || row.placed <= 0
        || row.sold === null
        || row.returned === null
        || row.damaged === null
        || row.missing === null
        || row.stillAtShop === null
        || row.sold + row.returned + row.damaged + row.missing + row.stillAtShop !== row.placed
      ) {
        return [];
      }
      return [{
        shop_name: row.shop.title,
        packets_given: row.placed,
        packets_bought: row.sold,
        packets_returned: row.returned,
        packets_damaged: row.damaged,
        packets_missing: row.missing,
        packets_still_at_shop: row.stillAtShop,
        wants_another_batch: row.entry.continuation === "yes"
          ? true
          : row.entry.continuation === "no" ? false : null,
        notes: row.entry.notes.trim() || null,
      }];
    });
    const researchContext = result.evidence
      .filter((item) => item.city === pilotForm.city || item.city === "India")
      .slice(0, 12)
      .map((item) => `${item.title}: ${item.observation} (${scopeLabel(item.evidence_scope, item.engine)})`);
    if (result.synthesis?.recommendation) {
      researchContext.unshift(`Earlier AI research recommendation: ${result.synthesis.recommendation}`);
    }

    setPilotReviewLoading(true);
    setPilotReviewError(null);
    try {
      const response = await fetch(`${API_BASE}/research/pilot-review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_name: form.product_name,
          city: pilotForm.city,
          planned_packets: pilotState.units,
          actual_packets_given: pilotState.actualUnitsPlaced,
          packets_bought: pilotState.unitsSold,
          packets_returned: pilotState.unitsReturned,
          packets_damaged: pilotState.unitsDamaged,
          packets_missing: pilotState.unitsMissing,
          packets_still_at_shops: pilotState.unitsStillAtShops,
          target_bought_percent: pilotState.targetSellThrough,
          maximum_returned_percent: pilotState.maxReturn,
          shops_planned: pilotState.shops,
          shops_asking_another_batch: pilotState.shopsWilling,
          money_received_inr: pilotState.hasMoneyCheck ? pilotState.moneyReceived : null,
          nonrecoverable_costs_inr: pilotState.hasMoneyCheck ? pilotState.nonrecoverableCosts : null,
          maximum_acceptable_loss_inr: pilotState.hasMoneyCheck ? pilotState.maximumAcceptableLoss : null,
          change_from_previous_round: pilotForm.experiment_change_type
            ? `${pilotChangeLabel(pilotForm.experiment_change_type)}: ${pilotForm.experiment_change_description.trim()}`
            : null,
          shop_results: shopResults,
          merchant_notes: pilotForm.learning_notes.trim() || null,
          research_context: researchContext,
        }),
      });
      const body = (await parseResponse(response)) as PilotReviewResponse;
      setPilotReview(body);
    } catch (caught) {
      setPilotReviewError(
        caught instanceof Error ? caught.message : "Unable to review the completed pilot.",
      );
    } finally {
      setPilotReviewLoading(false);
    }
  }

  async function generateBrief() {
    setLoading("brief");
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/research/brief`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, research_brief: null }),
      });
      const body = (await parseResponse(response)) as BriefResponse;
      setResearchBrief(body.brief.research_brief);
      setBriefDetails(body.brief);
      setBriefModel(body.model_used);
      setBriefWarnings(body.warnings);
      setBriefStale(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to generate the research brief.");
    } finally {
      setLoading(null);
    }
  }

  async function submit(action: "preview" | "analyze") {
    if (!researchBrief.trim()) {
      setError("Generate or write the research brief before planning the research.");
      return;
    }
    setLoading(action);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/research/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const nextResult = (await parseResponse(response)) as ResearchResponse;
      setResult(nextResult);
      setAppView(action === "analyze" ? "results" : "prepare");
      setResultsTab("overview");
      setPilotForm({
        ...initialPilotForm,
        city: nextResult.city_summaries[0]?.city ?? "",
      });
      setSelectedPilotShopIds([]);
      setPilotShopOutreach({});
      setShopPilotResults({});
      setPilotReview(null);
      setPilotReviewError(null);
      setPilotError(null);
      setPlanOpen(false);
      setOpenPlanEngine(
        nextResult.plan.queries.some((query) => query.engine === "google_shopping")
          ? "google_shopping"
          : nextResult.plan.queries[0]?.engine ?? "google_maps",
      );
      setToolTraceOpen(false);
      setComparisonOpen(true);
      setScorecardOpen(true);
      setEvidenceLedgerOpen(true);
      setOpenEvidenceGroup("direct");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to reach MarketSarthi API.");
    } finally {
      setLoading(null);
    }
  }

  async function refreshEvidence(section: RefreshSection | "all") {
    if (!result || result.mode === "plan_only") {
      setError("Run live analysis before refreshing one evidence section.");
      return;
    }
    if (briefStale) {
      setError("The merchant details changed. Approve the updated brief and run full live analysis before refreshing one section.");
      return;
    }
    const sections = section === "all"
      ? REFRESH_SECTIONS.map((item) => item.value)
      : [section];
    setRefreshingSection(section);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/research/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: payload, current_result: result, sections }),
      });
      const nextResult = (await parseResponse(response)) as ResearchResponse;
      setResult(nextResult);
      setToolTraceOpen(false);
      setScorecardOpen(true);
      setEvidenceLedgerOpen(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to refresh this evidence section.");
    } finally {
      setRefreshingSection(null);
    }
  }

  async function updateDecisionSummary() {
    if (!result || result.mode === "plan_only") {
      setError("Run live analysis before creating the final decision summary.");
      return;
    }
    if (briefStale) {
      setError("The merchant details changed. Run full live analysis before updating the final decision summary.");
      return;
    }
    setDecisionSummaryLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/research/decision-summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: payload, current_result: result }),
      });
      const body = (await parseResponse(response)) as DecisionSummaryResponse;
      setResult((current) => current ? {
        ...current,
        decision_summary: body.summary,
        decision_model_used: body.model_used,
        decision_warnings: body.warnings,
      } : current);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update the decision summary.");
    } finally {
      setDecisionSummaryLoading(false);
    }
  }

  async function askCopilot(questionOverride?: string) {
    const question = (questionOverride ?? copilotQuestion).trim();
    if (!question || copilotLoading) return;
    const learnedName = extractPreferredName(question);
    const activePreferredName = learnedName ?? copilotPreferredName;
    if (learnedName) setCopilotPreferredName(learnedName);

    const userMessage: CopilotMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };
    setCopilotMessages((current) => [...current, userMessage].slice(-30));
    setCopilotQuestion("");
    setCopilotLoading(true);
    setCopilotError(null);
    try {
      const response = await fetch(`${API_BASE}/research/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          merchant_context: {
            preferred_name: activePreferredName,
            product_name: form.product_name.trim() || null,
            category: form.category.trim() || null,
            current_city: form.current_city.trim() || null,
            target_cities: form.target_cities.split(",").map((item) => item.trim()).filter(Boolean),
            price_min_inr: optionalNumber(form.price_min_inr),
            price_max_inr: optionalNumber(form.price_max_inr),
            pack_size: form.pack_size.trim() || null,
            business_background: form.business_background.trim() || null,
            expansion_goal: form.expansion_goal.trim() || null,
          },
          current_result: result,
          research_details_changed: briefStale,
          pilot_context: {
            city: pilotForm.city || null,
            selected_shops: selectedPilotShopIds.length,
            confirmed_shops: Object.values(pilotShopOutreach).filter(
              (shop) => shop.status === "confirmed",
            ).length,
            has_completed_review: Boolean(pilotReview),
            saved_rounds: pilotHistory.length,
          },
          history: copilotMessages.slice(-8).map((message) => ({
            role: message.role,
            content: message.content,
          })),
        }),
      });
      const body = (await parseResponse(response)) as CopilotResponse;
      if (body.preferred_name) setCopilotPreferredName(body.preferred_name);
      const assistantMessage: CopilotMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: sanitizeCopilotContent(body.answer),
        sources: body.sources,
        suggested_refresh: body.suggested_refresh,
        model_used: body.model_used,
        warnings: body.warnings,
      };
      setCopilotMessages((current) => [...current, assistantMessage].slice(-30));
    } catch (caught) {
      setCopilotError(
        caught instanceof Error ? caught.message : "MarketSarthi Copilot could not answer.",
      );
    } finally {
      setCopilotLoading(false);
    }
  }

  function showRefreshControls() {
    setAppView("results");
    setResultsTab("overview");
    setCopilotOpen(false);
    window.setTimeout(() => {
      document.getElementById("evidence-refresh-controls")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 0);
  }

  function update(name: keyof typeof initialForm, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
    if (researchBrief) setBriefStale(true);
  }

  function downloadWorkspaceBackup() {
    if (!storageReady) {
      setBackupMessage("Wait for this browser workspace to finish loading.");
      return;
    }
    const exportedAt = new Date().toISOString();
    const workspace: PersistedWorkspace = {
      schema_version: 1,
      saved_at: exportedAt,
      form,
      research_brief: researchBrief,
      brief_details: briefDetails,
      brief_model: briefModel,
      brief_warnings: briefWarnings,
      brief_stale: briefStale,
      result,
      pilot_form: pilotForm,
      selected_pilot_shop_ids: selectedPilotShopIds,
      pilot_shop_outreach: pilotShopOutreach,
      shop_pilot_results: shopPilotResults,
      pilot_review: pilotReview,
      pilot_history: pilotHistory,
      copilot_messages: copilotMessages,
      copilot_preferred_name: copilotPreferredName,
    };
    const backup: WorkspaceBackup = {
      app: "MarketSarthi",
      backup_version: 1,
      exported_at: exportedAt,
      workspace,
    };
    const blob = new Blob([JSON.stringify(backup, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `marketsarthi-workspace-${new Date().toISOString().slice(0, 10)}.json`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
    setBackupMessage("Workspace backup downloaded. Keep it private because it contains your business notes.");
  }

  async function importWorkspaceBackup(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    input.value = "";
    if (!file) return;
    if (file.size > MAX_BACKUP_BYTES) {
      setBackupMessage("This backup is too large. MarketSarthi accepts files up to 5 MB.");
      return;
    }
    try {
      const parsed = JSON.parse(await file.text()) as unknown;
      const workspace = validateWorkspaceBackup(parsed);
      if (!workspace) {
        setBackupMessage("This is not a valid MarketSarthi backup, or it contains unsafe data.");
        return;
      }
      const roundCount = Array.isArray(workspace.pilot_history) ? workspace.pilot_history.length : 0;
      const shouldImport = window.confirm(
        `Restore this MarketSarthi backup with ${roundCount} saved pilot round${roundCount === 1 ? "" : "s"}? This will replace the workspace currently saved in this browser.`,
      );
      if (!shouldImport) {
        setBackupMessage("Backup restore cancelled. Your current workspace was not changed.");
        return;
      }
      window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(workspace));
      window.location.reload();
    } catch {
      setBackupMessage("MarketSarthi could not read this backup file. Choose an unedited JSON backup created by this app.");
    }
  }

  function startNewWorkspace() {
    const shouldClear = window.confirm(
      "Start a new MarketSarthi workspace? This removes the saved research, Copilot conversation, pilot draft and saved pilot rounds from this browser.",
    );
    if (!shouldClear) return;
    window.localStorage.removeItem(WORKSPACE_STORAGE_KEY);
    window.location.reload();
  }

  return (
    <main>
      <nav className="nav shell">
        <a className="brand" href="#top" aria-label="MarketSarthi home" onClick={() => setAppView("prepare")}>
          <span className="brand-mark">M</span><span>MarketSarthi</span>
        </a>
        <div className="app-view-switch" aria-label="MarketSarthi workflow">
          <button
            className={appView === "prepare" ? "active" : ""}
            type="button"
            onClick={() => { setAppView("prepare"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
          >
            <span>1</span><b>Prepare research</b>
          </button>
          <i aria-hidden="true" />
          <button
            className={appView === "results" ? "active" : ""}
            type="button"
            disabled={!hasLiveResult}
            onClick={() => { setAppView("results"); setResultsTab("overview"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
          >
            <span>2</span><b>Results &amp; pilot</b>
          </button>
        </div>
      </nav>

      {appView === "prepare" && <>
      <section className="hero shell" id="top">
        <div>
          <p className="eyebrow">REGIONAL EXPANSION, WITH RECEIPTS</p>
          <h1>Know the market<br />before you enter it.</h1>
          <p className="hero-copy">
            Turn product details and the merchant&apos;s real business story into a transparent
            city-expansion hypothesis grounded in source-linked evidence.
          </p>
          <div className="trust-row">
            <span>Powered by SerpApi</span><span>DeepSeek V4.1 Flash primary · Gemini fallback</span><span>No success guarantees</span>
          </div>
        </div>
        <div className="hero-orbit" aria-hidden="true">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <div className="city-dot city-a"><b>KOL</b><small>candidate</small></div>
          <div className="city-dot city-b"><b>BLR</b><small>compare</small></div>
          <div className="city-dot city-c"><b>PUN</b><small>compare</small></div>
          <div className="product-chip">KH<br /><span>200g</span></div>
        </div>
      </section>

      <section className="workspace shell">
        <form className="research-card" onSubmit={(event) => { event.preventDefault(); void submit("preview"); }}>
          <div className="section-heading">
            <div><span className="step">01</span><h2>Describe the expansion</h2></div>
            <p>Share the business facts and the human context behind the expansion.</p>
          </div>

          <div className={`workspace-memory ${saveStatus}`}>
            <div role="status" aria-live="polite">
              <span aria-hidden="true" />
              <div>
                <b>
                  {saveStatus === "loading" && "Checking this browser for saved work…"}
                  {saveStatus === "saving" && "Saving this workspace…"}
                  {saveStatus === "saved" && "Workspace saved on this browser"}
                  {saveStatus === "unavailable" && "Browser autosave is unavailable"}
                </b>
                <small>
                  {saveStatus === "saved" && savedAt
                    ? `Last saved ${new Date(savedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}. Research, Copilot chat, pilot drafts and saved rounds restore after refresh.`
                    : saveStatus === "unavailable"
                      ? "Download the pilot report before closing the page."
                      : "Your API keys are never stored in the browser workspace."}
                </small>
              </div>
            </div>
            <div className="workspace-memory-actions">
              <button type="button" disabled={!storageReady} onClick={downloadWorkspaceBackup}>Download backup</button>
              <button type="button" disabled={!storageReady} onClick={() => backupInputRef.current?.click()}>Restore backup</button>
              <button type="button" disabled={!storageReady} onClick={startNewWorkspace}>Start new workspace</button>
              <input ref={backupInputRef} className="workspace-backup-input" type="file" accept="application/json,.json" onChange={(event) => void importWorkspaceBackup(event)} />
            </div>
          </div>
          {backupMessage && <p className="workspace-backup-message" role="status">{backupMessage}</p>}

          <div className="form-grid">
            <label>Product<input value={form.product_name} onChange={(e) => update("product_name", e.target.value)} /></label>
            <label>Category<input value={form.category} onChange={(e) => update("category", e.target.value)} /></label>
            <label>Current market<input value={form.current_city} onChange={(e) => update("current_city", e.target.value)} /></label>
            <label>Candidate cities<input value={form.target_cities} onChange={(e) => update("target_cities", e.target.value)} /><small>Comma-separated, maximum five</small></label>
            <label>Minimum price (₹)<input type="number" value={form.price_min_inr} onChange={(e) => update("price_min_inr", e.target.value)} /></label>
            <label>Maximum price (₹)<input type="number" value={form.price_max_inr} onChange={(e) => update("price_max_inr", e.target.value)} /></label>
            <label>Pack size<input value={form.pack_size} onChange={(e) => update("pack_size", e.target.value)} /></label>
            <label>Differentiators<input value={form.differentiators} onChange={(e) => update("differentiators", e.target.value)} /></label>
            <label className="wide">Business constraints<input value={form.constraints} onChange={(e) => update("constraints", e.target.value)} /></label>
            <label className="wide">Business background and story<textarea rows={4} value={form.business_background} onChange={(e) => update("business_background", e.target.value)} /><small>Explain who runs the business, its history and the situation today.</small></label>
            <label className="wide">Expansion goal<textarea rows={3} value={form.expansion_goal} onChange={(e) => update("expansion_goal", e.target.value)} /><small>What outcome do you want, and how much risk can the business take?</small></label>
          </div>

          <p className="privacy-note">Do not enter identity documents, bank details or confidential customer information.</p>

          <div className="brief-builder">
            <div className="brief-heading">
              <div><span className="step light">02</span><div><h3>Merchant-approved research brief</h3><p>DeepSeek is primary; the configured fallback keeps the workflow resilient.</p></div></div>
              <button className="button brief-button" type="button" disabled={Boolean(loading)} onClick={() => void generateBrief()}>
                {loading === "brief" ? "Drafting brief…" : researchBrief ? "Regenerate brief" : "Generate research brief"}
              </button>
            </div>

            {researchBrief ? (
              <>
                <label className="brief-editor">Edit before approving<textarea rows={10} value={researchBrief} onChange={(event) => { setResearchBrief(event.target.value); setBriefStale(false); }} /></label>
                <div className="brief-status">
                  <span>
                    {briefModel === "local-template"
                      ? "Editable fallback draft · AI provider temporarily unavailable"
                      : briefModel ? `Generated with ${briefModel}` : "Merchant-written brief"}
                  </span>
                  <span>Editing is allowed</span>
                  {briefStale && <strong>Details changed—review or regenerate this brief.</strong>}
                </div>
                {briefWarnings.length > 0 && (
                  <div className={`brief-warnings ${briefModel === "local-template" ? "fallback" : ""}`}>
                    {briefWarnings.map((warning) => <p key={warning}>{warning}</p>)}
                  </div>
                )}
                {briefDetails && (
                  <div className="brief-facts">
                    <div><b>Facts preserved</b><span>{briefDetails.business_facts.length}</span></div>
                    <div><b>Goals understood</b><span>{briefDetails.merchant_goals.length}</span></div>
                    <div><b>Assumptions exposed</b><span>{briefDetails.assumptions.length}</span></div>
                    <div><b>Open questions</b><span>{briefDetails.open_questions.length}</span></div>
                  </div>
                )}
              </>
            ) : (
              <p className="brief-empty">Generate a draft, then edit it until it accurately represents the merchant&apos;s situation.</p>
            )}
          </div>

          <div className="actions">
            <p className="action-sequence">
              <b>Next step:</b>{" "}
              {!researchBrief.trim()
                ? "Generate and approve the research brief."
                : briefStale
                  ? "Review the changed details, then regenerate or edit the brief."
                  : !planMatchesCurrentBrief
                    ? "Preview the research plan before starting live research."
                    : "The plan is ready. Start live research when you approve it."}
            </p>
            <button className="button secondary" disabled={Boolean(loading) || !researchBrief.trim() || briefStale} type="submit">
              {loading === "preview" ? "Planning…" : "Preview approved plan"}
            </button>
            <button className="button primary" disabled={Boolean(loading) || !planMatchesCurrentBrief} type="button" onClick={() => void submit("analyze")}>
              {loading === "analyze" ? "Researching…" : "Start live research"}<span>↗</span>
            </button>
          </div>
          {error && <div className="error-banner">{error}</div>}
        </form>

        <aside className="principles-card">
          <p className="eyebrow">THE EVIDENCE CONTRACT</p>
          <h3>Useful uncertainty beats false confidence.</h3>
          <ol>
            <li><span>1</span><div><b>Understand</b><small>Preserve the merchant&apos;s context and goal.</small></div></li>
            <li><span>2</span><div><b>Observe</b><small>Collect source-linked market signals.</small></div></li>
            <li><span>3</span><div><b>Compare</b><small>Keep businesses selling the same product separate from other customer choices.</small></div></li>
            <li><span>4</span><div><b>Pilot</b><small>Recommend a bounded real-world experiment.</small></div></li>
          </ol>
        </aside>
      </section>

      {hasLiveResult && (
        <section className="prepare-complete shell">
          <div><span aria-hidden="true">✓</span><div><b>Live research is already saved</b><small>You can update the business details here or return to the results workspace.</small></div></div>
          <button className="button secondary" type="button" onClick={() => { setAppView("results"); setResultsTab("overview"); window.scrollTo({ top: 0, behavior: "smooth" }); }}>
            View results &amp; pilot <span>→</span>
          </button>
        </section>
      )}
      </>}

      {appView === "results" && hasLiveResult && (
        <section className="results-intro shell" id="top">
          <div><p className="eyebrow">PAGE 2 · RESEARCH RESULTS</p><h1>Your market research workspace.</h1><p>Start with the decision, inspect the supporting evidence when needed, then prepare a small real-world pilot.</p></div>
          <button className="button secondary" type="button" onClick={() => { setAppView("prepare"); window.scrollTo({ top: 0, behavior: "smooth" }); }}>← Edit business details</button>
        </section>
      )}

      {result && ((result.mode === "plan_only" && appView === "prepare") || (result.mode !== "plan_only" && appView === "results")) && (
        <section className={`results shell result-tab-${result.mode === "plan_only" ? "prepare" : resultsTab}`}>
          <div className="section-heading result-heading">
            <div><span className="step">03</span><h2>{result.synthesis?.headline ?? (result.mode === "plan_only" ? "Research plan ready" : "Evidence updated — decision summary pending")}</h2></div>
            <div className="result-actions">
              {researchFreshness && (
                <span className={`research-freshness ${researchFreshness.stale ? "stale" : "fresh"}`}>
                  {researchFreshness.label}
                </span>
              )}
              <span className="mode">{result.mode.replaceAll("_", " ")}</span>
              {result.classification_model_used && (
                <span className="jev-badge" title="Jev classified Shopping listings; low-confidence items kept MarketSarthi's existing labels.">
                  Jev · {result.classification_items_applied ?? 0} classified
                </span>
              )}
              {result.mode === "plan_only" && (
                <button
                  className="dropdown-button"
                  type="button"
                  aria-expanded={planOpen}
                  aria-controls="research-plan-panel"
                  onClick={() => setPlanOpen((open) => !open)}
                >
                  Review research plan <i aria-hidden="true">⌄</i>
                </button>
              )}
              {result.mode === "plan_only" && (
                <button className="button primary" type="button" disabled={Boolean(loading) || !planMatchesCurrentBrief} onClick={() => void submit("analyze")}>
                  {loading === "analyze" ? "Researching…" : "Start live research"}<span>↗</span>
                </button>
              )}
            </div>
          </div>
          {result.mode !== "plan_only" && (
            <nav className="results-tabs" aria-label="Research results sections">
              <button className={resultsTab === "overview" ? "active" : ""} type="button" onClick={() => setResultsTab("overview")}><span>1</span><div><b>Decision overview</b><small>What the merchant should do</small></div></button>
              <button className={resultsTab === "evidence" ? "active" : ""} type="button" onClick={() => setResultsTab("evidence")}><span>2</span><div><b>Evidence &amp; sources</b><small>How the answer was built</small></div></button>
              <button className={resultsTab === "pilot" ? "active" : ""} type="button" onClick={() => setResultsTab("pilot")}><span>3</span><div><b>Plan a small test</b><small>Try it before scaling</small></div></button>
            </nav>
          )}
          {result.mode === "plan_only" && (
            <div className="plan-summary-strip" aria-label="Research plan summary">
              <div><b>{result.plan.queries.length}</b><small>planned searches</small></div>
              <div><b>{planEngines.length}</b><small>SerpApi tools</small></div>
              <div><b>{plannedCities}</b><small>{plannedCities === 1 ? "candidate city" : "candidate cities"}</small></div>
              <p>Review the plan if you want, then start live research. No live evidence has been collected yet.</p>
            </div>
          )}
          {result.synthesis && <p className="recommendation">{result.synthesis.recommendation}</p>}
          {researchFreshness && (
            <p className={`freshness-note ${researchFreshness.stale ? "stale" : ""}`}>
              {researchFreshness.stale
                ? `Some preserved evidence was last checked on ${researchFreshness.oldestExact}. Prices, listings, shops and news may have changed. Refresh the relevant section before making a new commitment.`
                : researchFreshness.mixed
                  ? `The latest section was checked on ${researchFreshness.exact}; preserved evidence goes back to ${researchFreshness.oldestExact}. These are check times, not source publication times.`
                  : `Evidence checked on ${researchFreshness.exact}. This is the check time, not the source publication time, and search results can change.`}
            </p>
          )}
          {result.mode !== "plan_only" && (
            <section className="evidence-refresh" id="evidence-refresh-controls">
              <div className="evidence-refresh-heading">
                <div>
                  <p className="eyebrow">REFRESH ONLY WHAT CHANGED</p>
                  <h3>Update one evidence section</h3>
                  <small>Each refresh bypasses MarketSarthi&apos;s local cache, replaces only that section, and preserves your pilot workspace.</small>
                </div>
                <button
                  className="button secondary"
                  type="button"
                  disabled={Boolean(refreshingSection)}
                  onClick={() => void refreshEvidence("all")}
                >
                  {refreshingSection === "all" ? "Refreshing everything…" : "Refresh everything"}
                </button>
              </div>
              <div className="refresh-grid">
                {REFRESH_SECTIONS.map((item) => (
                  <button
                    type="button"
                    key={item.value}
                    disabled={Boolean(refreshingSection)}
                    onClick={() => void refreshEvidence(item.value)}
                  >
                    <b>{refreshingSection === item.value ? "Refreshing…" : `Refresh ${item.label}`}</b>
                    <small>{item.detail}</small>
                  </button>
                ))}
              </div>
            </section>
          )}
          {result.mode !== "plan_only" && (
            <section className="decision-summary">
              <div className="decision-summary-heading">
                <div>
                  <p className="eyebrow">FINAL DECISION SUMMARY</p>
                  <h3>What this research means for the merchant</h3>
                  <small>Observed facts and gaps are calculated first. The AI only explains the next actions in simple English.</small>
                </div>
                <button
                  className="button primary"
                  type="button"
                  disabled={decisionSummaryLoading || Boolean(refreshingSection)}
                  onClick={() => void updateDecisionSummary()}
                >
                  {decisionSummaryLoading ? "Updating summary…" : result.decision_summary ? "Update decision summary" : "Create decision summary"}
                </button>
              </div>
              {result.decision_summary ? (
                <div className="decision-summary-grid">
                  <article><h4>What we observed</h4><ul>{result.decision_summary.observed.map((item) => <li key={item}>{item}</li>)}</ul></article>
                  <article><h4>What is still unknown</h4><ul>{result.decision_summary.unknowns.map((item) => <li key={item}>{item}</li>)}</ul></article>
                  <article className="next"><h4>What to do next</h4><ul>{result.decision_summary.next_actions.map((item) => <li key={item}>{item}</li>)}</ul></article>
                  <article className="warning-card"><h4>What not to conclude</h4><ul>{result.decision_summary.do_not_conclude.map((item) => <li key={item}>{item}</li>)}</ul></article>
                </div>
              ) : (
                <p className="decision-summary-empty">Refresh any old evidence first, then create the summary once. This avoids spending an LLM call after every small refresh.</p>
              )}
              {result.decision_model_used && <p className="decision-summary-model">Explanation source: {result.decision_model_used}</p>}
              {(result.decision_warnings ?? []).map((warning) => <p className="decision-summary-warning" key={warning}>{warning}</p>)}
            </section>
          )}
          {(result.mode !== "plan_only" || planOpen) && <div className="plan-browser" id="research-plan-panel">
            <section className="research-questions" aria-label="Business research questions">
              <div className="research-questions-heading">
                <p className="eyebrow">HUMAN-STYLE RESEARCH PLAN</p>
                <h3>Questions MarketSarthi will investigate</h3>
                <small>The web and news investigation uses 18 human-style angles. News can stop after broad coverage is found; every attempted, skipped, empty or failed angle remains visible.</small>
              </div>
              <div className="research-question-grid">
                {researchQuestions.map((item) => (
                  <article key={`${item.city}-${item.question}`}>
                    <div><span>{item.city}</span><b>{item.status}</b></div>
                    <h4>{item.question}</h4>
                    <p>{item.engines.map(engineLabel).join(" + ")} · {item.planned} planned {item.planned === 1 ? "search" : "searches"}{item.attempted > 0 ? ` · ${item.attempted} attempted` : ""}</p>
                  </article>
                ))}
              </div>
            </section>
            <div className="engine-accordion" aria-label="SerpApi research tools">
              {planEngines.map(({ engine, count }) => (
                <section className={`engine-accordion-item ${openPlanEngine === engine ? "open" : ""}`} key={engine}>
                  <button
                    type="button"
                    aria-expanded={openPlanEngine === engine}
                    aria-controls={`plan-${engine}`}
                    onClick={() => setOpenPlanEngine((open) => open === engine ? null : engine)}
                  >
                    <span><small>SerpApi</small>{engineLabel(engine)}</span>
                    <span className="accordion-meta"><b>{count} searches</b><i aria-hidden="true">⌄</i></span>
                  </button>
                  {openPlanEngine === engine && <div className="engine-accordion-content" id={`plan-${engine}`}>
                    <p className="engine-explainer">
                      {engine === "google_shopping" && "We search for your product first, then try broader names and common spellings if needed."}
                      {engine === "google_maps" && "We search product shops first, then related shops such as Gujarati snack, namkeen and farsan stores. Reviews help us find product mentions."}
                      {engine === "google_trends" && "We check how relative search interest changed over time and where it appeared. These scores do not measure demand or sales."}
                      {engine === "google" && "We find useful pages that mention the product and city. Each page remains a lead to inspect, not proof of demand."}
                      {engine === "google_news" && "We widen from the exact product into category changes, events, retailers, distributors, competitors, regulations, schemes, supply and customer context. Articles do not prove demand or business impact."}
                    </p>
                    <div className="query-grid">
                      {result.plan.queries.filter((query) => query.engine === engine).map((query) => (
                        <article className="query-card" key={`${query.engine}-${query.city}-${query.tool}-${query.stage}-${query.query}`}>
                          <div><span className="engine">{query.provider} · {engineLabel(query.engine)}</span><span className="city">{query.city}</span></div>
                          <small className="query-question">Business question: {query.research_question}</small>
                          <h3>{query.query}</h3><p>{query.purpose}</p>
                          {query.fallback_rank && (
                            <small>
                              {queryStepLabel(query.engine)} #{query.fallback_rank}
                            </small>
                          )}
                        </article>
                      ))}
                    </div>
                  </div>}
                </section>
              ))}
            </div>
          </div>}
          {(result.city_summaries ?? []).length > 1 && (
            <section className="city-comparison">
              <button
                className="city-comparison-heading"
                type="button"
                aria-expanded={comparisonOpen}
                aria-controls="city-comparison-panel"
                onClick={() => setComparisonOpen((open) => !open)}
              >
                <div>
                  <p className="eyebrow">SIDE-BY-SIDE EVIDENCE</p>
                  <h3>Compare candidate cities</h3>
                  <small>Coverage shows how many evidence checks were completed. It is not a market-potential score or success prediction.</small>
                </div>
                <span className="accordion-meta"><b>{result.city_summaries.length} cities</b><i aria-hidden="true">⌄</i></span>
              </button>
              {comparisonOpen && <div className="city-comparison-scroll" id="city-comparison-panel">
                <table>
                  <thead>
                    <tr>
                      <th>City</th>
                      <th>Same-product listings</th>
                      <th>Shops to check</th>
                      <th>Shops with product mentions</th>
                      <th>City web pages</th>
                      <th>Recent city articles</th>
                      <th>Relative Trends score</th>
                      <th>Price comparison</th>
                      <th>Evidence coverage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.city_summaries.map((summary) => (
                      <tr key={summary.city}>
                        <th>{summary.city}</th>
                        <td>{summary.direct_competitors}</td>
                        <td>{summary.local_channels}</td>
                        <td>{summary.verified_local_channels}</td>
                        <td>{summary.city_specific_web_results}</td>
                        <td>{summary.city_specific_news_results}</td>
                        <td>{summary.trend_interest_score ?? "Not returned"}</td>
                        <td>{shortPriceSignalLabel(summary.price_band_signal)}</td>
                        <td><b>{summary.evidence_coverage_percent}%</b><small>{summary.evidence_dimensions_met} of {summary.evidence_dimensions_total} checks</small></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p>For Trends, 100 means the highest relative interest inside that returned Google Trends comparison—not 100 searches or 100% demand. News counts are context only and do not increase the coverage percentage.</p>
              </div>}
            </section>
          )}
          {(result.city_summaries ?? []).length > 0 && (
            <section className="city-scorecard">
              <button
                className="city-scorecard-heading"
                type="button"
                aria-expanded={scorecardOpen}
                aria-controls="city-scorecard-panel"
                onClick={() => setScorecardOpen((open) => !open)}
              >
                <div>
                  <p className="eyebrow">NO AI MODEL REQUIRED</p>
                  <h3>City evidence scorecard</h3>
                  <small>Shows what we found and what is still missing. It does not promise sales.</small>
                </div>
                <span className="accordion-meta"><b>{result.city_summaries.length} cities</b><i aria-hidden="true">⌄</i></span>
              </button>
              {scorecardOpen && <div className="city-scorecard-grid" id="city-scorecard-panel">
                {result.city_summaries.map((summary) => (
                  <article className={`city-score ${summary.coverage_level}`} key={summary.city}>
                    <div className="city-score-title">
                      <h4>{summary.city}</h4>
                      <span>{coverageLabel(summary.coverage_level)}</span>
                    </div>
                    <div className="city-metrics">
                      <div><b>{summary.direct_competitors}</b><small>same-product listings found</small></div>
                      <div><b>{summary.local_channels}</b><small>shops you could check</small></div>
                      <div><b>{summary.verified_local_channels}</b><small>shops with a product mention</small></div>
                      <div><b>{summary.observed_price_median ? `₹${summary.observed_price_median}` : "—"}</b><small>middle price among listings</small></div>
                    </div>
                    <p className="price-signal">{priceSignalLabel(summary.price_band_signal)}</p>
                    <div className="next-action"><b>What to do next</b><p>{summary.next_action}</p></div>
                    {summary.evidence_gaps.length > 0 && (
                      <div className="evidence-gaps">
                        <b>What we still need to check</b>
                        <ul>{summary.evidence_gaps.map((gap) => <li key={gap}>{gap}</li>)}</ul>
                      </div>
                    )}
                  </article>
                ))}
              </div>}
            </section>
          )}
          {result.mode !== "plan_only" && result.city_summaries.length > 0 && (
            <section className="pilot-workspace">
              <div className="pilot-heading">
                <div>
                  <p className="eyebrow">04 · MEASURED REAL-WORLD TEST</p>
                  <h3>Plan a small shop pilot</h3>
                  <p>
                    You choose the quantity, price and success checks. MarketSarthi adds the
                    evidence snapshot and calculates results—it does not invent a pilot or
                    promise that the city will succeed.
                  </p>
                </div>
                <span>Merchant controlled</span>
              </div>

              <div className="pilot-grid">
                <div className="pilot-form">
                  <div className="pilot-section-title">
                    <span>1</span>
                    <div><b>Set the test</b><small>Enter the plan you can realistically run.</small></div>
                  </div>
                  <div className="pilot-field-grid">
                    <label>
                      Pilot city
                      <select value={pilotForm.city} onChange={(event) => updatePilotCity(event.target.value)}>
                        {result.city_summaries.map((summary) => <option key={summary.city} value={summary.city}>{summary.city}</option>)}
                      </select>
                    </label>
                    <label>
                      Duration (days)
                      <input type="number" min="1" step="1" placeholder="Example: 14" value={pilotForm.duration_days} onChange={(event) => updatePilotField("duration_days", event.target.value)} />
                    </label>
                    <label>
                      Packets planned for the test
                      <input type="number" min="1" step="1" placeholder="Example: 60" value={pilotForm.units_planned} onChange={(event) => updatePilotField("units_planned", event.target.value)} />
                      <small>How many packets you may give to all test shops.</small>
                    </label>
                    <label>
                      Shops to include
                      <input type="number" min="1" step="1" placeholder="Example: 3" value={pilotForm.shops_planned} onChange={(event) => updatePilotField("shops_planned", event.target.value)} />
                    </label>
                    <label>
                      Test price (₹)
                      <input type="number" min="0.01" step="0.01" placeholder="Example: 150" value={pilotForm.test_price_inr} onChange={(event) => updatePilotField("test_price_inr", event.target.value)} />
                    </label>
                    <label>
                      Target packets sold (%)
                      <input type="number" min="0" max="100" step="0.1" placeholder="Example: 60" value={pilotForm.target_sell_through_percent} onChange={(event) => updatePilotField("target_sell_through_percent", event.target.value)} />
                      <small>Percentage of given packets you want customers to buy.</small>
                    </label>
                    <label>
                      Highest packets returned (%)
                      <input type="number" min="0" max="100" step="0.1" placeholder="Example: 10" value={pilotForm.max_return_percent} onChange={(event) => updatePilotField("max_return_percent", event.target.value)} />
                      <small>Highest percentage of unsold packets you will accept back.</small>
                    </label>
                  </div>
                  {pilotHistory.length > 0 ? (
                    <div className="pilot-change-plan">
                      <div>
                        <b>What is different in this round?</b>
                        <small>For a clearer comparison, change only one main thing and keep the rest as similar as you can.</small>
                      </div>
                      <div className="pilot-field-grid change-fields">
                        <label>
                          One main change
                          <select value={pilotForm.experiment_change_type} onChange={(event) => updatePilotField("experiment_change_type", event.target.value as PilotChangeType)}>
                            <option value="">Choose one</option>
                            <option value="repeat_same">Repeat the same test</option>
                            <option value="price">Price</option>
                            <option value="pack_size">Pack size</option>
                            <option value="product">Product or recipe</option>
                            <option value="shop_type">Type of shop</option>
                            <option value="display_message">Display or sales message</option>
                            <option value="other">Another change</option>
                          </select>
                        </label>
                        <label>
                          Explain the change simply
                          <textarea rows={2} placeholder="Example: Price changed from ₹150 to ₹140. Pack size and shops stayed the same." value={pilotForm.experiment_change_description} onChange={(event) => updatePilotField("experiment_change_description", event.target.value)} />
                        </label>
                      </div>
                      <p>This records what you planned to change. A better or worse result still does not prove that this change caused it.</p>
                    </div>
                  ) : (
                    <p className="first-round-note">This is your first recorded round. Later rounds will ask you to record one main change.</p>
                  )}
                </div>

                <aside className="pilot-evidence">
                  <p className="eyebrow">RESEARCH SNAPSHOT</p>
                  <h4>{selectedPilotSummary?.city ?? "Choose a city"}</h4>
                  {selectedPilotSummary && (
                    <div className="pilot-evidence-grid">
                      <div><b>{selectedPilotSummary.direct_competitors}</b><small>same-product listings found</small></div>
                      <div><b>{selectedPilotSummary.local_channels}</b><small>shops you could check</small></div>
                      <div><b>{selectedPilotSummary.verified_local_channels}</b><small>shops with a product mention</small></div>
                      <div><b>{selectedPilotSummary.evidence_coverage_percent}%</b><small>research checks completed</small></div>
                    </div>
                  )}
                  <p>
                    These numbers help you prepare the test. They do not measure city-wide
                    demand, stock availability or future sales.
                  </p>
                </aside>
              </div>

              <div className="pilot-shop-shortlist">
                <div className="pilot-section-title shortlist-title">
                  <span>2</span>
                  <div>
                    <b>Choose shops to contact</b>
                    <small>Select real Google Maps leads for outreach. Contact them before treating them as pilot partners.</small>
                  </div>
                  <strong>{selectedPilotShops.length} selected · {pilotState.shops ?? "—"} planned</strong>
                </div>
                {pilotShopLeads.length > 0 ? (
                  <div className="pilot-shop-grid">
                    {pilotShopLeads.map((shop) => {
                      const selected = selectedPilotShopIds.includes(shop.id);
                      const verified = shop.channel_status === "verified_product_mention";
                      return (
                        <article className={`pilot-shop-card ${selected ? "selected" : ""}`} key={shop.id}>
                          <div className="pilot-shop-card-heading">
                            <span className={verified ? "verified" : "potential"}>
                              {verified ? "Product mentioned in a review" : "Possible shop to contact"}
                            </span>
                            <button type="button" aria-pressed={selected} onClick={() => togglePilotShop(shop.id)}>
                              {selected ? "Selected ✓" : "Add to pilot"}
                            </button>
                          </div>
                          <h5>{shop.title}</h5>
                          <p>{shop.observation}</p>
                          <div className="pilot-shop-card-footer">
                            <small>{verified ? "Current stock is still unconfirmed." : "Product fit and interest are unconfirmed."}</small>
                            {shop.source_url && <a href={shop.source_url} target="_blank" rel="noreferrer">Open source ↗</a>}
                          </div>
                        </article>
                      );
                    })}
                  </div>
                ) : (
                  <p className="pilot-shop-empty">No Google Maps shop leads were returned for this city. The pilot can still be planned, but shops must be found and confirmed separately.</p>
                )}
              </div>

              <div className="pilot-outreach-tracker">
                  <div className="pilot-section-title outreach-title">
                    <span>3</span>
                    <div>
                      <b>Track retailer outreach</b>
                      <small>Record what the merchant actually learns after contacting each selected business.</small>
                    </div>
                    <strong>{outreachSummary.confirmed} confirmed · {selectedPilotShops.length} selected</strong>
                  </div>
                  {selectedPilotShops.length > 0 ? <>
                    <div className="outreach-summary" aria-label="Retailer outreach summary">
                      <span><b>{outreachSummary.waiting}</b> waiting for reply</span>
                      <span><b>{outreachSummary.interested}</b> discussing terms</span>
                      <span><b>{outreachSummary.confirmed}</b> confirmed</span>
                      <span><b>{outreachSummary.declined}</b> not participating</span>
                    </div>
                    <div className="outreach-grid">
                      {selectedPilotShops.map((shop) => {
                        const outreach = pilotShopOutreach[shop.id] ?? { status: "not_contacted", notes: "" };
                        return (
                          <article className={`outreach-card ${outreach.status}`} key={shop.id}>
                            <div>
                              <h5>{shop.title}</h5>
                              {shop.source_url && <a href={shop.source_url} target="_blank" rel="noreferrer">Map source ↗</a>}
                            </div>
                            <label>
                              Merchant-recorded status
                              <select
                                value={outreach.status}
                                onChange={(event) => updatePilotShopOutreach(
                                  shop.id,
                                  { status: event.target.value as OutreachStatus },
                                )}
                              >
                                <option value="not_contacted">Not contacted yet</option>
                                <option value="contacted">Contacted — waiting for reply</option>
                                <option value="interested">Interested — discussing terms</option>
                                <option value="confirmed">Confirmed for this pilot</option>
                                <option value="declined">Not participating</option>
                              </select>
                            </label>
                            <label>
                              Contact notes
                              <textarea
                                rows={2}
                                placeholder="Example: Call again Friday; retailer asked about margin and shelf life."
                                value={outreach.notes}
                                onChange={(event) => updatePilotShopOutreach(shop.id, { notes: event.target.value })}
                              />
                            </label>
                            <small>Status and notes come from the merchant, not from search results or AI.</small>
                          </article>
                        );
                      })}
                    </div>
                  </> : (
                    <p className="pilot-shop-empty">Choose one or more shops above. Their contact status and notes will appear here before you record pilot results.</p>
                  )}
                </div>

              {confirmedPilotShops.length > 0 && (
                <div className="shop-measurement">
                  <div className="pilot-section-title measurement-title">
                    <span>4</span>
                    <div>
                      <b>Record what happened at each confirmed shop</b>
                      <small>Count each shop separately so one strong shop does not hide another shop&apos;s weak result.</small>
                    </div>
                    <strong>{confirmedPilotShops.length} confirmed shops</strong>
                  </div>
                  <div className="shop-measurement-grid">
                    {shopMeasurementState.rows.map(({ shop, entry }) => (
                      <article className="shop-measurement-card" key={shop.id}>
                        <h5>{shop.title}</h5>
                        <div className="shop-number-grid">
                          <label>
                            Packets given to this shop
                            <input type="number" min="1" step="1" value={entry.units_placed} onChange={(event) => updateShopPilotResult(shop.id, { units_placed: event.target.value })} />
                            <small>How many packets the merchant delivered here.</small>
                          </label>
                          <label>
                            Packets customers bought
                            <input type="number" min="0" step="1" value={entry.units_sold} onChange={(event) => updateShopPilotResult(shop.id, { units_sold: event.target.value })} />
                            <small>Count customer purchases, not packets invoiced to the shop.</small>
                          </label>
                          <label>
                            Unsold packets returned to you
                            <input type="number" min="0" step="1" value={entry.units_returned} onChange={(event) => updateShopPilotResult(shop.id, { units_returned: event.target.value })} />
                            <small>Packets physically returned by this shop.</small>
                          </label>
                          <label>
                            Damaged packets
                            <input type="number" min="0" step="1" value={entry.units_damaged} onChange={(event) => updateShopPilotResult(shop.id, { units_damaged: event.target.value })} />
                            <small>Enter 0 if no packets were damaged here.</small>
                          </label>
                          <label>
                            Missing packets
                            <input type="number" min="0" step="1" value={entry.units_missing} onChange={(event) => updateShopPilotResult(shop.id, { units_missing: event.target.value })} />
                            <small>Packets assigned here that cannot be found.</small>
                          </label>
                          <label>
                            Packets still at this shop
                            <input type="number" min="0" step="1" value={entry.units_still_at_shop} onChange={(event) => updateShopPilotResult(shop.id, { units_still_at_shop: event.target.value })} />
                            <small>Unsold packets not yet returned to you.</small>
                          </label>
                        </div>
                        <label>
                          Does this shop want another batch?
                          <select value={entry.continuation} onChange={(event) => updateShopPilotResult(shop.id, { continuation: event.target.value as ContinuationDecision })}>
                            <option value="not_recorded">Not recorded yet</option>
                            <option value="yes">Yes</option>
                            <option value="no">No</option>
                          </select>
                        </label>
                        <label>
                          Shop-level learning
                          <textarea rows={2} placeholder="Record price, display, customer comments or retailer feedback." value={entry.notes} onChange={(event) => updateShopPilotResult(shop.id, { notes: event.target.value })} />
                        </label>
                      </article>
                    ))}
                  </div>
                  <div className="shop-measurement-totals">
                    <div><small>PACKETS GIVEN TO SHOPS</small><b>{shopMeasurementState.totalPlaced}</b></div>
                    <div><small>PACKETS CUSTOMERS BOUGHT</small><b>{shopMeasurementState.totalSold}</b></div>
                    <div><small>UNSOLD PACKETS RETURNED</small><b>{shopMeasurementState.totalReturned}</b></div>
                    <div><small>DAMAGED PACKETS</small><b>{shopMeasurementState.totalDamaged}</b></div>
                    <div><small>MISSING PACKETS</small><b>{shopMeasurementState.totalMissing}</b></div>
                    <div><small>STILL AT SHOPS</small><b>{shopMeasurementState.totalStillAtShops}</b></div>
                    <div><small>SHOPS ASKING FOR MORE</small><b>{shopMeasurementState.shopsContinuing}</b></div>
                    <button className="button secondary" type="button" disabled={!shopMeasurementState.complete} onClick={applyShopMeasurementTotals}>Use these totals</button>
                  </div>
                  {shopMeasurementState.errors.length > 0
                    ? <p className="shop-measurement-error">{shopMeasurementState.errors[0]}</p>
                    : <p>Every confirmed shop&apos;s packets are explained. Press the button to copy all totals below.</p>}
                </div>
              )}

              <div className="pilot-results-entry">
                <div className="pilot-section-title">
                  <span>{confirmedPilotShops.length > 0 ? "5" : "4"}</span>
                  <div><b>Review the total result</b><small>Enter the totals directly, or use the confirmed-shop totals above.</small></div>
                </div>
                <div className="pilot-field-grid results-fields">
                  <label>
                    Packets given to all shops
                    <input type="number" min="1" step="1" placeholder="Example: 60" value={pilotForm.actual_units_placed} onChange={(event) => updatePilotField("actual_units_placed", event.target.value)} />
                    <small>Total packets the merchant actually delivered for this test.</small>
                  </label>
                  <label>
                    Packets customers bought
                    <input type="number" min="0" step="1" placeholder="Example: 32" value={pilotForm.units_sold} onChange={(event) => updatePilotField("units_sold", event.target.value)} />
                    <small>Count packets bought by customers across all shops.</small>
                  </label>
                  <label>
                    Unsold packets returned to you
                    <input type="number" min="0" step="1" placeholder="Example: 28" value={pilotForm.units_returned} onChange={(event) => updatePilotField("units_returned", event.target.value)} />
                    <small>Count packets physically returned by the shops.</small>
                  </label>
                  <label>
                    Damaged packets
                    <input type="number" min="0" step="1" placeholder="Enter 0 if none" value={pilotForm.units_damaged} onChange={(event) => updatePilotField("units_damaged", event.target.value)} />
                    <small>Packets that cannot be sold because they were damaged.</small>
                  </label>
                  <label>
                    Missing packets
                    <input type="number" min="0" step="1" placeholder="Enter 0 if none" value={pilotForm.units_missing} onChange={(event) => updatePilotField("units_missing", event.target.value)} />
                    <small>Packets that should be present but cannot be found.</small>
                  </label>
                  <label>
                    Packets still at shops
                    <input type="number" min="0" step="1" placeholder="Enter 0 if none" value={pilotForm.units_still_at_shops} onChange={(event) => updatePilotField("units_still_at_shops", event.target.value)} />
                    <small>Unsold packets that have not yet been returned.</small>
                  </label>
                  <label>
                    Shops asking for another batch
                    <input type="number" min="0" step="1" placeholder="Example: 2" value={pilotForm.shops_willing_to_continue} onChange={(event) => updatePilotField("shops_willing_to_continue", event.target.value)} />
                    <small>How many shops want to continue after this test.</small>
                  </label>
                  <label className="wide">
                    What did you learn?
                    <textarea rows={3} placeholder="Record retailer feedback, customer comments, discounts or anything unusual." value={pilotForm.learning_notes} onChange={(event) => updatePilotField("learning_notes", event.target.value)} />
                  </label>
                </div>
                <p className={`stock-count-note ${pilotState.packetsUnexplained === 0 ? "complete" : ""}`}>
                  {pilotState.packetsUnexplained === null
                    ? "Account for every packet. Enter 0 when none were damaged, missing, or left at shops."
                    : pilotState.packetsUnexplained === 0
                      ? "Every packet is accounted for in the counts above."
                      : `${pilotState.packetsUnexplained} packets are not explained yet. Check the counts before reviewing the pilot.`}
                </p>
              </div>

              <div className="pilot-money-check">
                <div className="pilot-section-title money-title">
                  <span>₹</span>
                  <div>
                    <b>Did this small test cover its costs?</b>
                    <small>Optional. Enter the money that came in and the test costs that were used up. This does not predict future profit.</small>
                  </div>
                </div>
                <div className="pilot-field-grid money-fields">
                  <label>
                    Money received from sold packets (₹)
                    <input type="number" min="0" step="0.01" placeholder="Example: 4800" value={pilotForm.money_received_inr} onChange={(event) => updatePilotField("money_received_inr", event.target.value)} />
                    <small>Total money you actually received from shops or customers.</small>
                  </label>
                  <label>
                    Test costs already used up (₹)
                    <input type="number" min="0" step="0.01" placeholder="Example: 4300" value={pilotForm.nonrecoverable_costs_inr} onChange={(event) => updatePilotField("nonrecoverable_costs_inr", event.target.value)} />
                    <small>Include making sold or damaged packets, delivery and free samples. Leave out returned packets you can sell again.</small>
                  </label>
                  <label>
                    How much loss is okay for this test? (₹)
                    <input type="number" min="0" step="0.01" placeholder="Example: 500" value={pilotForm.maximum_acceptable_loss_inr} onChange={(event) => updatePilotField("maximum_acceptable_loss_inr", event.target.value)} />
                    <small>Enter zero if you do not want this test to lose money.</small>
                  </label>
                </div>
                {pilotState.hasMoneyCheck && (
                  <div className={`pilot-money-result ${pilotState.cashCheckMet ? "within" : "outside"}`}>
                    <div><small>{pilotState.netCashResult !== null && pilotState.netCashResult >= 0 ? "MONEY LEFT AFTER TEST COSTS" : "TEST COSTS NOT COVERED"}</small><b>{pilotState.netCashResult !== null && pilotState.netCashResult >= 0 ? "+" : ""}₹{pilotState.netCashResult?.toFixed(2)}</b></div>
                    <p>{pilotState.cashCheckMet ? "This is within the amount you said was okay for this test." : "This test lost more money than the amount you said was okay. Check the price or test costs before trying again."}</p>
                  </div>
                )}
              </div>

              <div className={`pilot-outcome ${pilotState.hasMeasuredResults ? "measured" : "waiting"}`}>
                <div>
                  <small>PERCENT OF PACKETS SOLD</small>
                  <b>{pilotState.sellThrough === null ? "Not entered" : `${pilotState.sellThrough.toFixed(1)}%`}</b>
                </div>
                <div>
                  <small>PERCENT OF PACKETS RETURNED</small>
                  <b>{pilotState.returnRate === null ? "Not entered" : `${pilotState.returnRate.toFixed(1)}%`}</b>
                </div>
                <div>
                  <small>RESULT AGAINST YOUR TARGETS</small>
                  <b>{pilotState.decision}</b>
                </div>
              </div>

              <div className="pilot-decision-review">
                <div className="pilot-review-heading">
                  <div>
                    <p className="eyebrow">CALCULATED FACTS · AI EXPLANATION</p>
                    <h4>Decide the next small action</h4>
                    <p>MarketSarthi first checks your numbers against your own targets. AI then explains that fixed result and suggests one limited next test; it cannot change the calculated outcome.</p>
                  </div>
                  <button className="button primary" type="button" disabled={pilotReviewLoading} onClick={() => void generatePilotReview()}>
                    {pilotReviewLoading ? "Reviewing…" : pilotReview ? "Review again" : "Review pilot"}<span>→</span>
                  </button>
                </div>

                {pilotReviewError && <p className="pilot-error">{pilotReviewError}</p>}

                {pilotReview ? (
                  <div className="pilot-review-result">
                    <div className={`pilot-review-outcome ${pilotReview.facts.outcome}`}>
                      <small>CALCULATED OUTCOME</small>
                      <h5>{pilotOutcomeLabel(pilotReview.facts.outcome)}</h5>
                      <p>{pilotReview.review.summary}</p>
                      <span>{pilotReview.model_used === "local-rule-review" ? "Explained with local safety rules" : `Explained with ${pilotReview.model_used}`}</span>
                    </div>

                    <div className="pilot-review-metrics">
                      <div><b>{pilotReview.facts.bought_percent.toFixed(1)}%</b><small>packets bought</small></div>
                      <div><b>{pilotReview.facts.returned_percent.toFixed(1)}%</b><small>packets returned</small></div>
                      <div><b>{pilotReview.facts.shops_asking_another_batch}</b><small>shops asking for more</small></div>
                      <div><b>{pilotReview.facts.packets_unaccounted_for}</b><small>packets unresolved</small></div>
                      <div><b>{pilotReview.facts.packets_damaged ?? 0}</b><small>damaged packets</small></div>
                      <div><b>{pilotReview.facts.packets_missing ?? 0}</b><small>missing packets</small></div>
                      <div><b>{pilotReview.facts.packets_still_at_shops ?? 0}</b><small>still at shops</small></div>
                      {pilotReview.facts.net_cash_result_inr !== null && pilotReview.facts.net_cash_result_inr !== undefined && (
                        <div><b>{pilotReview.facts.net_cash_result_inr >= 0 ? "+" : ""}₹{pilotReview.facts.net_cash_result_inr.toFixed(2)}</b><small>{pilotReview.facts.net_cash_result_inr >= 0 ? "money left after test costs" : "test costs not covered"}</small></div>
                      )}
                    </div>

                    <div className="pilot-review-grid">
                      <article>
                        <h5>Why MarketSarthi reached this result</h5>
                        <ul>{pilotReview.facts.reasons.map((item) => <li key={item}>{item}</li>)}</ul>
                      </article>
                      <article>
                        <h5>What worked</h5>
                        {pilotReview.review.what_worked.length > 0
                          ? <ul>{pilotReview.review.what_worked.map((item) => <li key={item}>{item}</li>)}</ul>
                          : <p>No positive signal was recorded strongly enough to list here.</p>}
                      </article>
                      <article>
                        <h5>What needs attention</h5>
                        {pilotReview.review.what_needs_attention.length + pilotReview.facts.data_gaps.length > 0
                          ? <ul>{Array.from(new Set([...pilotReview.review.what_needs_attention, ...pilotReview.facts.data_gaps])).map((item) => <li key={item}>{item}</li>)}</ul>
                          : <p>No unresolved issue was recorded in the submitted totals.</p>}
                      </article>
                      <article className="next-experiment">
                        <h5>One small next experiment</h5>
                        <p>{pilotReview.review.next_experiment}</p>
                      </article>
                    </div>

                    <div className="do-not-conclude">
                      <b>What this pilot does not prove</b>
                      <ul>{pilotReview.review.do_not_conclude.map((item) => <li key={item}>{item}</li>)}</ul>
                    </div>
                    {pilotReview.warnings.map((warning) => <p className="pilot-review-warning" key={warning}>{warning}</p>)}
                    <div className="pilot-round-save">
                      <div>
                        <b>{currentPilotRoundSaved ? "This pilot round is saved" : "Keep this result before starting another test"}</b>
                        <small>Saved rounds stay in this browser and let you compare repeated tests without changing the calculated result.</small>
                        {pilotHistoryMessage && <p>{pilotHistoryMessage}</p>}
                      </div>
                      <div>
                        <button className="button secondary" type="button" disabled={currentPilotRoundSaved} onClick={savePilotRound}>
                          {currentPilotRoundSaved ? "Round saved ✓" : "Save this pilot round"}
                        </button>
                        {currentPilotRoundSaved && (
                          <button className="button primary" type="button" onClick={startNextPilotRound}>Start next round<span>→</span></button>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="pilot-review-empty">Enter the completed pilot totals, including how many shops asked for another batch, then ask MarketSarthi to review the result.</p>
                    {pilotHistoryMessage && <p className="pilot-history-status">{pilotHistoryMessage}</p>}
                  </>
                )}
              </div>

              {pilotHistory.length > 0 && (
                <section className="pilot-history">
                  <div className="pilot-history-heading">
                    <div>
                      <p className="eyebrow">SAVED IN THIS BROWSER</p>
                      <h4>Your pilot rounds</h4>
                      <p>Compare repeated small tests. A change between rounds is an observation, not proof of what caused it.</p>
                    </div>
                    <strong>{pilotHistory.length} saved</strong>
                  </div>

                  {pilotRoundComparison && (
                    <div className="pilot-history-comparison">
                      <div><small>PACKETS BOUGHT</small><b>{pilotRoundComparison.bought >= 0 ? "+" : ""}{pilotRoundComparison.bought.toFixed(1)} points</b></div>
                      <div><small>PACKETS RETURNED</small><b>{pilotRoundComparison.returned >= 0 ? "+" : ""}{pilotRoundComparison.returned.toFixed(1)} points</b></div>
                      {pilotRoundComparison.money !== null && <div><small>MONEY AFTER USED-UP COSTS</small><b>{pilotRoundComparison.money >= 0 ? "+" : ""}₹{pilotRoundComparison.money.toFixed(2)}</b></div>}
                      <p><b>Latest planned change:</b> {pilotChangeLabel(pilotHistory[0].experiment_change_type)}{pilotHistory[0].experiment_change_description ? ` — ${pilotHistory[0].experiment_change_description}` : ""}. Latest saved round compared with the previous saved round; this does not prove the change caused the difference.</p>
                    </div>
                  )}

                  <div className="pilot-history-list">
                    {pilotHistory.map((round, index) => (
                      <article key={round.id}>
                        <div className="pilot-history-number"><span>{pilotHistory.length - index}</span><small>ROUND</small></div>
                        <div className="pilot-history-main">
                          <div><h5>{round.city}</h5><span>{new Date(round.saved_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span></div>
                          <b>{pilotOutcomeLabel(round.outcome)}</b>
                          <small className="pilot-history-change">Planned change: {pilotChangeLabel(round.experiment_change_type)}{round.experiment_change_description ? ` — ${round.experiment_change_description}` : ""}</small>
                          {((round.packets_damaged ?? 0) > 0 || (round.packets_missing ?? 0) > 0 || (round.packets_still_at_shops ?? 0) > 0) && (
                            <small className="pilot-history-stock">Stock check: {round.packets_damaged ?? 0} damaged · {round.packets_missing ?? 0} missing · {round.packets_still_at_shops ?? 0} still at shops</small>
                          )}
                          <p>{round.next_experiment}</p>
                        </div>
                        <div className="pilot-history-actions">
                          <div className="pilot-history-numbers">
                            <span><b>{round.bought_percent.toFixed(1)}%</b><small>bought</small></span>
                            <span><b>{round.returned_percent.toFixed(1)}%</b><small>returned</small></span>
                            <span><b>{round.shops_asking_another_batch}</b><small>shops want more</small></span>
                            {round.net_cash_result_inr !== null && <span><b>{round.net_cash_result_inr >= 0 ? "+" : ""}₹{round.net_cash_result_inr.toFixed(0)}</b><small>test money</small></span>}
                          </div>
                          <button
                            className="remove-round-button"
                            type="button"
                            aria-label={`Remove saved ${round.city} pilot round`}
                            onClick={() => removePilotRound(round)}
                          >
                            Remove round
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              )}

              <div className="pilot-actions">
                <div>
                  <b>Download a working report</b>
                  <small>The Markdown file includes your plan, actual results and up to 15 evidence links.</small>
                  {(pilotError || pilotState.errors.length > 0) && (
                    <p className="pilot-error">{pilotError ?? pilotState.errors[0]}</p>
                  )}
                </div>
                <button className="button primary" type="button" onClick={downloadPilotReport}>
                  Download pilot report (.md)<span>↓</span>
                </button>
              </div>
            </section>
          )}
          {(result.tool_runs ?? []).length > 0 && (
            <section className="tool-trace">
              <button
                className="tool-trace-heading"
                type="button"
                aria-expanded={toolTraceOpen}
                aria-controls="tool-trace-panel"
                onClick={() => setToolTraceOpen((open) => !open)}
              >
                <div><p className="eyebrow">LIVE TOOL TRACE</p><h3>Powered by SerpApi</h3></div>
                <span className="accordion-meta"><b>{result.tool_runs.length} calls</b><i aria-hidden="true">⌄</i></span>
              </button>
              {toolTraceOpen && <div className="tool-run-grid" id="tool-trace-panel">
                {result.tool_runs.map((run, index) => (
                  <article key={`${run.engine}-${run.query}-${index}`} className={`tool-run ${run.status}`}>
                    <div><b>{run.provider} · {engineLabel(run.engine)}</b><span>{run.status.replaceAll("_", " ")}</span></div>
                    <small className="tool-question">Question: {run.research_question}</small>
                    <h4>{run.query}</h4>
                    <p>{run.scope} · {run.result_count} results{run.cache_hit ? " · reused from local cache" : ""}</p>
                    {run.note && <small>{run.note}</small>}
                  </article>
                ))}
              </div>}
            </section>
          )}
          {result.evidence.length > 0 && (
            <div className="evidence-section">
              <button
                className="evidence-ledger-heading"
                type="button"
                aria-expanded={evidenceLedgerOpen}
                aria-controls="evidence-ledger-panel"
                onClick={() => setEvidenceLedgerOpen((open) => !open)}
              >
                <h3>Evidence ledger</h3>
                <span className="accordion-meta"><b>{result.evidence.length} observations</b><i aria-hidden="true">⌄</i></span>
              </button>
              {evidenceLedgerOpen && <div id="evidence-ledger-panel">
                <EvidenceGroup groupKey="direct" title="Businesses selling the same product" description="These businesses sell the same kind of product as you. Compare their prices, pack sizes and product claims with yours." items={evidenceGroups.direct} tone="direct" isOpen={openEvidenceGroup === "direct"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
                <EvidenceGroup groupKey="alternative" title="Other products customers may choose" description="These products are different from yours, but a customer may buy them for the same need or occasion." items={evidenceGroups.alternative} tone="alternative" isOpen={openEvidenceGroup === "alternative"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
                <EvidenceGroup groupKey="uncertain" title="Results that need checking" description="These search results may or may not be useful. Check them before using them in a business decision." items={evidenceGroups.uncertain} tone="uncertain" isOpen={openEvidenceGroup === "uncertain"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
                <EvidenceGroup groupKey="trends" title="How search interest is changing" description="Google Trends shows relative search activity over time and between places. It does not show the number of buyers, demand or sales." items={evidenceGroups.trends} tone="trend" isOpen={openEvidenceGroup === "trends"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
                <EvidenceGroup groupKey="web" title="Useful pages and market mentions" description="These pages appeared when we searched for the product and target city. Open the source before treating any claim as confirmed." items={evidenceGroups.web} tone="web" isOpen={openEvidenceGroup === "web"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
                <EvidenceGroup groupKey="news" title="Events and reported market changes" description="These articles may describe past, ongoing or publicly announced upcoming events and changes. Check the source and date; coverage does not prove customer demand or business impact." items={evidenceGroups.news} tone="news" isOpen={openEvidenceGroup === "news"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
                <EvidenceGroup groupKey="customer-voice" title="What customers are saying" description="These are short reviews that mention your product. They come from a few shops and do not represent every customer in the city." items={evidenceGroups.customerVoice} tone="review" isOpen={openEvidenceGroup === "customer-voice"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
                <EvidenceGroup groupKey="verified" title="Shops with product mentions" description="At least one review mentions the product at these shops. Call the shop to confirm that it sells the product now." items={evidenceGroups.verifiedLocal} tone="verified" isOpen={openEvidenceGroup === "verified"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
                <EvidenceGroup groupKey="potential" title="Shops you could contact" description="These nearby shops may be suitable for your product, but we have not confirmed that they sell it." items={evidenceGroups.potentialLocal} tone="local" isOpen={openEvidenceGroup === "potential"} onToggle={(key) => setOpenEvidenceGroup((open) => open === key ? null : key)} />
              </div>}
            </div>
          )}
          {uniqueResultWarnings.map((warning) => <p className="warning" key={warning}>⚑ {warning}</p>)}
        </section>
      )}

      <footer className="shell"><span>MarketSarthi · Hackathon build</span><span>Evidence, not prophecy.</span></footer>

      <button
        className={`copilot-launcher ${copilotOpen ? "open" : ""}`}
        type="button"
        aria-label={copilotOpen ? "Close MarketSarthi Copilot" : "Open MarketSarthi Copilot"}
        aria-expanded={copilotOpen}
        aria-controls="marketsarthi-copilot"
        onClick={() => setCopilotOpen((open) => !open)}
      >
        <span aria-hidden="true">✦</span>
        <b>{copilotOpen ? "Close" : "Ask Sarthi"}</b>
      </button>

      {copilotOpen && (
        <aside
          className="copilot-panel"
          id="marketsarthi-copilot"
          role="dialog"
          aria-label="MarketSarthi Copilot"
        >
          <header className="copilot-header">
            <div>
              <span aria-hidden="true">✦</span>
              <div><b>MarketSarthi Copilot</b><small>Answers from this workspace</small></div>
            </div>
            <div>
              {copilotMessages.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setCopilotMessages([]);
                    setCopilotError(null);
                  }}
                >
                  Clear
                </button>
              )}
              <button type="button" aria-label="Close Copilot" onClick={() => setCopilotOpen(false)}>×</button>
            </div>
          </header>

          <div className="copilot-body" aria-live="polite">
            {copilotMessages.length === 0 && (
              <div className="copilot-welcome">
                <span aria-hidden="true">✦</span>
                <h3>{copilotPreferredName ? `Hello, ${copilotPreferredName}!` : "Hello! How can I help?"}</h3>
                <p>
                  {copilotQuickStart.description} I will tell you when a refresh is needed.
                </p>
                <div className="copilot-prompts">
                  {copilotQuickStart.prompts.map((prompt) => (
                    <button type="button" key={prompt} onClick={() => void askCopilot(prompt)}>
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {copilotMessages.map((message) => (
              <article className={`copilot-message ${message.role}`} key={message.id}>
                <span>{message.role === "assistant" ? "Sarthi" : "You"}</span>
                <p>{sanitizeCopilotContent(message.content)}</p>
                {message.sources && message.sources.length > 0 && (
                  <div className="copilot-sources">
                    <b>Sources from your research</b>
                    {message.sources.map((source) => (
                      <a
                        href={source.source_url}
                        target="_blank"
                        rel="noreferrer"
                        key={source.evidence_id}
                      >
                        {source.title}<small>{engineLabel(source.engine)} · {source.city}</small>
                      </a>
                    ))}
                  </div>
                )}
                {message.role === "assistant" && message.suggested_refresh && result && result.mode !== "plan_only" && (
                  <button className="copilot-guide-button" type="button" onClick={showRefreshControls}>
                    Show the refresh controls
                  </button>
                )}
                {message.warnings?.map((warning) => (
                  <small className="copilot-warning" key={warning}>{warning}</small>
                ))}
              </article>
            ))}
            {copilotLoading && (
              <div className="copilot-thinking" role="status">
                <span /><span /><span /><b>Reading your MarketSarthi workspace…</b>
              </div>
            )}
            {copilotError && <p className="copilot-error">{copilotError}</p>}
            <div ref={copilotEndRef} />
          </div>

          <form
            className="copilot-composer"
            onSubmit={(event) => {
              event.preventDefault();
              void askCopilot();
            }}
          >
            <textarea
              aria-label="Ask MarketSarthi Copilot"
              placeholder="Ask about prices, a city, shops, or your next step…"
              maxLength={1000}
              rows={2}
              value={copilotQuestion}
              onChange={(event) => setCopilotQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void askCopilot();
                }
              }}
            />
            <button type="submit" disabled={!copilotQuestion.trim() || copilotLoading}>
              {copilotLoading ? "…" : "↑"}
            </button>
          </form>
          <small className="copilot-boundary">Your configured AI may receive the question and relevant workspace context · Never guarantees success</small>
        </aside>
      )}
    </main>
  );
}
