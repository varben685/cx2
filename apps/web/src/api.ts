export type HealthStatus = {
  status: string;
  service: string;
  version: string;
  timestamp: string;
};

export type SetupScoreComponent = {
  name: string;
  score: number;
  maxScore: number;
  reason: string;
};

export type SetupCandidate = {
  setupId: string;
  eventId: string;
  schemaVersion: string;
  strategyVersion: string;
  scoringConfigVersion: string;
  symbol: string;
  exchange: string;
  timeframe: string;
  direction: "LONG" | "SHORT" | string;
  htfBias: "BULLISH" | "BEARISH" | "NEUTRAL" | string;
  score: number;
  accepted: boolean;
  components: SetupScoreComponent[];
  rejectionReasons: string[];
  positiveReasons: string[];
  negativeReasons: string[];
  barCloseTime: string;
  receivedAt: string;
};

export type SetupCandidateList = {
  count: number;
  items: SetupCandidate[];
};

export type SetupCandidateQuery = {
  limit?: number;
  symbol?: string;
  accepted?: boolean;
};

export type BacktestConfig = {
  maxHoldingBars: number;
  entryTimeoutBars: number;
  commissionBpsPerSide: number;
  slippageBpsPerSide: number;
};

export type BacktestStatistics = {
  totalSetups: number;
  closedTrades: number;
  excludedSetups: number;
  outcomeCounts: Record<string, number>;
  netWins: number;
  netLosses: number;
  netBreakEven: number;
  netWinRate: number | null;
  totalNetR: number;
  netExpectancyR: number | null;
  netProfitR: number;
  netLossR: number;
  netProfitFactor: number | null;
};

export type RiskStatistics = {
  averageWinR: number | null;
  averageLossR: number | null;
  maximumDrawdownR: number;
  longestWinningStreak: number;
  longestLosingStreak: number;
};

export type EquityPoint = {
  sequence: number;
  eventId: string;
  occurredAt: string;
  netR: number;
  cumulativeNetR: number;
  drawdownR: number;
};

export type AnalyticsBreakdown = {
  key: string;
  label: string;
  statistics: BacktestStatistics;
};

export type ComponentBreakdown = {
  component: string;
  state: "ZERO" | "PARTIAL" | "FULL";
  statistics: BacktestStatistics;
};

export type DecisionComparison = {
  journaledSetups: number;
  taken: number;
  skipped: number;
  notRecorded: number;
  followedRecommendation: number;
  overrodeRecommendation: number;
  manualOverrides: number;
  agreementRate: number | null;
  takenStatistics: BacktestStatistics;
  skippedStatistics: BacktestStatistics;
};

export type PerformanceReport = {
  runId: string;
  scoringConfigVersion: string;
  statistics: BacktestStatistics;
  risk: RiskStatistics;
  equityCurve: EquityPoint[];
  bySession: AnalyticsBreakdown[];
  byInstrument: AnalyticsBreakdown[];
  byDirection: AnalyticsBreakdown[];
  byScoreBucket: AnalyticsBreakdown[];
  byStrategyVersion: AnalyticsBreakdown[];
  bySetupComponent: ComponentBreakdown[];
  decisions: DecisionComparison;
};

export type BacktestRun = {
  runId: string;
  status: "COMPLETED";
  startedAt: string;
  completedAt: string;
  symbol: string;
  exchange: string;
  timeframe: string;
  strategyVersion: string;
  requestSha256: string;
  config: BacktestConfig;
  outcomeIds: string[];
  statistics: BacktestStatistics;
};

export type BacktestList = {
  count: number;
  items: BacktestRun[];
};

export type BacktestRequest = {
  runId: string;
  setups: unknown[];
  candlesCsv: string;
  config: BacktestConfig;
};

export type OutcomeCost = {
  commissionAmount: number;
  slippageAmount: number;
  totalAmount: number;
  costR: number;
};

export type OutcomeExcursion = {
  mfeR: number;
  maeR: number;
  maxFavorablePrice: number;
  maxAdversePrice: number;
};

export type TradeOutcome = {
  label: string;
  exitReason: string;
  realizedR: number | null;
  netRealizedR: number | null;
  costs: OutcomeCost | null;
  excursion: OutcomeExcursion | null;
  entryTime: string | null;
  exitTime: string | null;
  exitPrice: number | null;
  barsToEntry: number | null;
  barsHeld: number | null;
};

export type OutcomeRecord = {
  outcomeId: string;
  runId: string;
  eventId: string;
  symbol: string;
  timeframe: string;
  direction: "LONG" | "SHORT";
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  evaluatedAt: string;
  engineVersion: string;
  marketDataSha256: string;
  outcome: TradeOutcome;
};

export type OutcomeList = {
  count: number;
  items: OutcomeRecord[];
};

export type JournalExecutionStatus = "NOT_RECORDED" | "TAKEN" | "SKIPPED";

export type JournalEntry = {
  journalId: string;
  setupId: string;
  outcomeId: string | null;
  eventId: string;
  symbol: string;
  exchange: string;
  timeframe: string;
  direction: "LONG" | "SHORT" | string;
  session: string;
  strategyVersion: string;
  signalTime: string;
  outcomeLabel: string | null;
  realizedR: number | null;
  mfeR: number | null;
  maeR: number | null;
  executionStatus: JournalExecutionStatus;
  userNote: string | null;
  screenshotReference: string | null;
  manualRating: number | null;
  manualOverride: boolean;
  overrideReason: string | null;
  tags: string[];
  revision: number;
  createdAt: string;
  updatedAt: string;
  setupSnapshot?: Record<string, unknown>;
  outcomeSnapshot?: Record<string, unknown> | null;
};

export type JournalList = {
  count: number;
  items: JournalEntry[];
};

export type JournalContent = {
  executionStatus: JournalExecutionStatus;
  userNote: string | null;
  screenshotReference: string | null;
  manualRating: number | null;
  manualOverride: boolean;
  overrideReason: string | null;
  tags: string[];
};

export type JournalCreateRequest = JournalContent & {
  setupId: string;
  outcomeId?: string;
};

export type JournalUpdateRequest = JournalContent & {
  journalId: string;
  expectedRevision: number;
};

export type PaperTradeStatus = "PENDING" | "OPEN" | "CLOSED" | "CANCELLED";

export type RiskDecision = {
  approved: boolean;
  policyVersion: string;
  rejectionReasons: string[];
  dailyLossR: number;
  consecutiveLosses: number;
  openPositions: number;
};

export type PaperTrade = {
  tradeId: string;
  setupId: string;
  eventId: string;
  symbol: string;
  exchange: string;
  timeframe: string;
  direction: "LONG" | "SHORT" | string;
  session: string;
  strategyVersion: string;
  status: PaperTradeStatus;
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  plannedRiskReward: number;
  accountBalance: number;
  riskPercent: number;
  riskAmount: number;
  quantity: number;
  openedAt: string | null;
  closedAt: string | null;
  exitPrice: number | null;
  exitReason: string | null;
  realizedPnl: number | null;
  realizedR: number | null;
  riskPolicyVersion: string;
  createdAt: string;
  updatedAt: string;
  revision: number;
  riskDecision?: RiskDecision;
};

export type PaperTradeList = {
  count: number;
  items: PaperTrade[];
};

export type PaperTradeEvent = {
  tradeId: string;
  sequence: number;
  eventType: "CREATED" | "PRICE_OBSERVED" | "OPENED" | "CLOSED" | "CANCELLED";
  occurredAt: string;
  details: Record<string, unknown>;
};

export type PaperTradeEventList = {
  count: number;
  items: PaperTradeEvent[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${apiBaseUrl}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthStatus>;
}

export async function fetchSetupCandidates(
  query: SetupCandidateQuery = {},
): Promise<SetupCandidateList> {
  const searchParams = new URLSearchParams();
  if (query.limit !== undefined) {
    searchParams.set("limit", String(query.limit));
  }

  if (query.symbol !== undefined && query.symbol.trim() !== "") {
    searchParams.set("symbol", query.symbol.trim().toUpperCase());
  }

  if (query.accepted !== undefined) {
    searchParams.set("accepted", String(query.accepted));
  }

  const queryString = searchParams.toString();
  const response = await fetch(
    `${apiBaseUrl}/api/v1/setups${queryString ? `?${queryString}` : ""}`,
  );

  if (!response.ok) {
    throw new Error(`Setup query failed with status ${response.status}`);
  }

  return response.json() as Promise<SetupCandidateList>;
}

export async function fetchSetupCandidate(setupId: string): Promise<SetupCandidate> {
  const response = await fetch(`${apiBaseUrl}/api/v1/setups/${setupId}`);

  if (!response.ok) {
    throw new Error(`Setup detail query failed with status ${response.status}`);
  }

  return response.json() as Promise<SetupCandidate>;
}

async function errorFromResponse(response: Response, fallback: string): Promise<ApiError> {
  let message = fallback;
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      message = payload.detail;
    } else if (Array.isArray(payload.detail)) {
      const validationMessages = payload.detail
        .map((item) =>
          typeof item === "object" && item !== null && "msg" in item
            ? String(item.msg)
            : null,
        )
        .filter((item): item is string => item !== null);
      if (validationMessages.length > 0) {
        message = validationMessages.join(" ");
      }
    }
  } catch {
    // Keep the operation-specific fallback when the response is not JSON.
  }
  return new ApiError(message, response.status);
}

export async function fetchBacktests(limit = 50): Promise<BacktestList> {
  const response = await fetch(`${apiBaseUrl}/api/v1/backtests?limit=${limit}`);
  if (!response.ok) {
    throw await errorFromResponse(response, "A backtest futások nem tölthetők be.");
  }
  return response.json() as Promise<BacktestList>;
}

export async function createBacktest(payload: BacktestRequest): Promise<BacktestRun> {
  const response = await fetch(`${apiBaseUrl}/api/v1/backtests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await errorFromResponse(response, "A backtest futtatása sikertelen.");
  }
  return response.json() as Promise<BacktestRun>;
}

export async function fetchOutcomes(runId: string, limit = 100): Promise<OutcomeList> {
  const params = new URLSearchParams({ runId, limit: String(limit) });
  const response = await fetch(`${apiBaseUrl}/api/v1/outcomes?${params.toString()}`);
  if (!response.ok) {
    throw await errorFromResponse(response, "Az outcome eredmények nem tölthetők be.");
  }
  return response.json() as Promise<OutcomeList>;
}

export async function fetchPerformanceReport(runId: string): Promise<PerformanceReport> {
  const searchParams = new URLSearchParams({ runId });
  const response = await fetch(`${apiBaseUrl}/api/v1/analytics/report?${searchParams}`);
  if (!response.ok) {
    throw await errorFromResponse(response, "Az elemzés nem tölthető be.");
  }
  return response.json() as Promise<PerformanceReport>;
}

export async function fetchJournal(limit = 100): Promise<JournalList> {
  const response = await fetch(`${apiBaseUrl}/api/v1/journal?limit=${limit}`);
  if (!response.ok) {
    throw await errorFromResponse(response, "A journal nem tölthető be.");
  }
  return response.json() as Promise<JournalList>;
}

export async function fetchJournalEntry(journalId: string): Promise<JournalEntry> {
  const response = await fetch(`${apiBaseUrl}/api/v1/journal/${journalId}`);
  if (!response.ok) {
    throw await errorFromResponse(response, "A journal bejegyzés nem tölthető be.");
  }
  return response.json() as Promise<JournalEntry>;
}

export async function fetchJournalRevisions(journalId: string): Promise<JournalList> {
  const response = await fetch(`${apiBaseUrl}/api/v1/journal/${journalId}/revisions`);
  if (!response.ok) {
    throw await errorFromResponse(response, "A journal előzmények nem tölthetők be.");
  }
  return response.json() as Promise<JournalList>;
}

export async function createJournalEntry(payload: JournalCreateRequest): Promise<JournalEntry> {
  const { setupId, ...body } = payload;
  const response = await fetch(`${apiBaseUrl}/api/v1/setups/${encodeURIComponent(setupId)}/journal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw await errorFromResponse(response, "A journal bejegyzés nem menthető.");
  }
  return response.json() as Promise<JournalEntry>;
}

export async function updateJournalEntry(payload: JournalUpdateRequest): Promise<JournalEntry> {
  const { journalId, ...body } = payload;
  const response = await fetch(`${apiBaseUrl}/api/v1/journal/${journalId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw await errorFromResponse(response, "A journal bejegyzés nem frissíthető.");
  }
  return response.json() as Promise<JournalEntry>;
}

export async function fetchPaperTrades(limit = 100): Promise<PaperTradeList> {
  const response = await fetch(`${apiBaseUrl}/api/v1/paper-trades?limit=${limit}`);
  if (!response.ok) {
    throw await errorFromResponse(response, "A paper trade lista nem tölthető be.");
  }
  return response.json() as Promise<PaperTradeList>;
}

export async function fetchPaperTradeEvents(tradeId: string): Promise<PaperTradeEventList> {
  const response = await fetch(`${apiBaseUrl}/api/v1/paper-trades/${tradeId}/events`);
  if (!response.ok) {
    throw await errorFromResponse(response, "A végrehajtási napló nem tölthető be.");
  }
  return response.json() as Promise<PaperTradeEventList>;
}

export async function createPaperTrade(payload: {
  setupId: string;
  accountBalance: number;
  riskPercent: number;
}): Promise<PaperTrade> {
  const response = await fetch(`${apiBaseUrl}/api/v1/paper-trades`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await errorFromResponse(response, "A paper trade nem hozható létre.");
  }
  return response.json() as Promise<PaperTrade>;
}

export async function observePaperTradePrice(tradeId: string, price: number): Promise<PaperTrade> {
  const response = await fetch(`${apiBaseUrl}/api/v1/paper-trades/${tradeId}/market-price`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ price }),
  });
  if (!response.ok) {
    throw await errorFromResponse(response, "Az árfrissítés sikertelen.");
  }
  return response.json() as Promise<PaperTrade>;
}

export async function closePaperTrade(tradeId: string, exitPrice: number): Promise<PaperTrade> {
  const response = await fetch(`${apiBaseUrl}/api/v1/paper-trades/${tradeId}/close`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exitPrice }),
  });
  if (!response.ok) {
    throw await errorFromResponse(response, "A paper trade lezárása sikertelen.");
  }
  return response.json() as Promise<PaperTrade>;
}

export async function cancelPaperTrade(tradeId: string): Promise<PaperTrade> {
  const response = await fetch(`${apiBaseUrl}/api/v1/paper-trades/${tradeId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    throw await errorFromResponse(response, "A paper trade visszavonása sikertelen.");
  }
  return response.json() as Promise<PaperTrade>;
}
