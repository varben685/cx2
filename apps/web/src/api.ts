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
