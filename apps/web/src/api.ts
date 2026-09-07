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
