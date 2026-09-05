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

type FetchStubOptions = {
  setupItems?: typeof setupCandidate[];
  failSetupList?: boolean;
  emptyFilteredSymbol?: string;
};

function stubFetch({
  setupItems = [setupCandidate],
  failSetupList = false,
  emptyFilteredSymbol,
}: FetchStubOptions = {}) {
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
        if (failSetupList) {
          return Promise.resolve({
            ok: false,
            status: 503,
            json: async () => ({}),
          });
        }

        const items =
          emptyFilteredSymbol !== undefined && url.includes(`symbol=${emptyFilteredSymbol}`)
            ? []
            : setupItems;

        return Promise.resolve({
          ok: true,
          json: async () => ({
            count: items.length,
            items,
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
}

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
    stubFetch();
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
    expect(screen.getByText("1 setup")).toBeInTheDocument();
    expect(screen.getByText("Megjelenítve: 1 / 1")).toBeInTheDocument();
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

  it("shows a distinct empty state when no setup exists yet", async () => {
    stubFetch({ setupItems: [] });
    renderApp();

    expect(await screen.findByText("Még nincs beérkezett setup candidate.")).toBeInTheDocument();
    expect(await screen.findByText("0 setup")).toBeInTheDocument();
    expect(await screen.findByText("Megjelenítve: 0 / 0")).toBeInTheDocument();
  });

  it("shows a filtered empty state when filters remove all setup candidates", async () => {
    const user = userEvent.setup();
    stubFetch({ emptyFilteredSymbol: "ETHUSDT" });
    renderApp();

    await user.type(await screen.findByLabelText("Symbol szűrő"), "ETHUSDT");

    expect(await screen.findByText("Nincs találat a jelenlegi szűrőkkel.")).toBeInTheDocument();
    expect(screen.getByText("Szűrve")).toBeInTheDocument();
    expect(screen.getByText("Megjelenítve: 0 / 0")).toBeInTheDocument();
  });

  it("shows a recoverable setup API error state", async () => {
    stubFetch({ failSetupList: true });
    renderApp();

    expect(
      await screen.findByText("A setup lista nem érhető el.", {}, { timeout: 3000 }),
    ).toBeInTheDocument();
    expect(screen.getByText("API hiba")).toBeInTheDocument();
    expect(screen.getByText("A setupok nem tölthetők be.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Újrapróbálás/i })).toBeInTheDocument();
  });
});
