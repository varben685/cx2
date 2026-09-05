import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const setupCandidate = {
  setupId: "BTCUSDT-1-1767225660000-LONG",
  eventId: "BTCUSDT-1-1767225660000-LONG",
  schemaVersion: "1.0",
  strategyVersion: "smc-rce-v1",
  scoringConfigVersion: "rule-score-v1",
  symbol: "BTCUSDT",
  exchange: "BINANCE",
  timeframe: "1",
  direction: "LONG",
  htfBias: "BULLISH",
  score: 100,
  accepted: true,
  components: [
    {
      name: "HTF_BIAS",
      score: 20,
      maxScore: 20,
      reason: "HTF bias aligns with setup direction.",
    },
  ],
  rejectionReasons: [],
  positiveReasons: ["HTF bias aligns with setup direction."],
  negativeReasons: [],
  barCloseTime: "2026-01-01T12:01:00Z",
  receivedAt: "2026-09-03T10:00:00Z",
};

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/health")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              status: "ok",
              service: "smc-assistant-api",
              version: "0.1.0",
              timestamp: "2026-01-01T12:00:00Z",
            }),
          });
        }

        if (url.includes("/api/v1/setups/")) {
          return Promise.resolve({
            ok: true,
            json: async () => setupCandidate,
          });
        }

        if (url.includes("/api/v1/setups")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              count: 1,
              items: [setupCandidate],
            }),
          });
        }

        return Promise.resolve({
          ok: false,
          status: 404,
          json: async () => ({}),
        });
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders backend health status", async () => {
    renderApp();

    expect(await screen.findByText("smc-assistant-api")).toBeInTheDocument();
    expect(screen.getByText("Backend kapcsolat")).toBeInTheDocument();
    expect(screen.getByText("0.1.0")).toBeInTheDocument();
  });

  it("renders setup candidates from the backend", async () => {
    renderApp();

    expect(await screen.findByText("Pontozott setupok")).toBeInTheDocument();
    expect(await screen.findByText("BTCUSDT")).toBeInTheDocument();
    expect(screen.getByText("LONG")).toBeInTheDocument();
    expect(screen.getByText("100.0")).toBeInTheDocument();
    expect(screen.getByText("ACCEPTED")).toBeInTheDocument();
  });

  it("opens setup details from the setup table", async () => {
    const user = userEvent.setup();
    renderApp();

    await user.click(await screen.findByLabelText("Setup részletek"));

    expect(await screen.findByText("Setup részletek")).toBeInTheDocument();
    expect(screen.getByText("rule-score-v1")).toBeInTheDocument();
    expect(screen.getByText("HTF_BIAS")).toBeInTheDocument();
    expect(screen.getAllByText("HTF bias aligns with setup direction.")).toHaveLength(3);
  });
});
