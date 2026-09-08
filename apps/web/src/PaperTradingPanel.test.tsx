import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { PaperTrade, PaperTradeEvent, SetupCandidate } from "./api";
import { PaperTradingPanel } from "./PaperTradingPanel";

const setup: SetupCandidate = {
  setupId: "BTCUSDT-1-paper-ui",
  eventId: "BTCUSDT-1-paper-ui",
  schemaVersion: "1.0",
  strategyVersion: "smc-rce-v1",
  scoringConfigVersion: "rule-score-v1",
  symbol: "BTCUSDT",
  exchange: "BINANCE",
  timeframe: "1",
  direction: "LONG",
  htfBias: "BULLISH",
  score: 90,
  accepted: true,
  components: [],
  rejectionReasons: [],
  positiveReasons: [],
  negativeReasons: [],
  barCloseTime: "2026-09-08T12:00:00Z",
  receivedAt: "2026-09-08T12:00:01Z",
};

function paperTrade(status: PaperTrade["status"]): PaperTrade {
  return {
    tradeId: "00000000-0000-4000-8000-000000000001",
    setupId: setup.setupId,
    eventId: setup.eventId,
    symbol: setup.symbol,
    exchange: setup.exchange,
    timeframe: setup.timeframe,
    direction: setup.direction,
    session: "NEW_YORK",
    strategyVersion: setup.strategyVersion,
    status,
    entryPrice: 100,
    stopLoss: 95,
    takeProfit: 110,
    plannedRiskReward: 2,
    accountBalance: 10_000,
    riskPercent: 1,
    riskAmount: 100,
    quantity: 20,
    openedAt: status === "OPEN" ? "2026-09-08T12:01:00Z" : null,
    closedAt: null,
    exitPrice: null,
    exitReason: null,
    realizedPnl: null,
    realizedR: null,
    riskPolicyVersion: "paper-risk-v1",
    createdAt: "2026-09-08T12:00:00Z",
    updatedAt: "2026-09-08T12:01:00Z",
    revision: status === "OPEN" ? 2 : 1,
  };
}

describe("PaperTradingPanel", () => {
  let trades: PaperTrade[];
  let events: PaperTradeEvent[];

  beforeEach(() => {
    trades = [];
    events = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/api/v1/paper-trades?limit=100")) {
          return { ok: true, json: async () => ({ count: trades.length, items: trades }) };
        }
        if (url.endsWith("/api/v1/paper-trades") && init?.method === "POST") {
          trades = [paperTrade("PENDING")];
          events = [
            {
              tradeId: trades[0].tradeId,
              sequence: 1,
              eventType: "CREATED",
              occurredAt: trades[0].createdAt,
              details: {},
            },
          ];
          return { ok: true, json: async () => trades[0] };
        }
        if (url.endsWith(`/api/v1/paper-trades/${paperTrade("PENDING").tradeId}/events`)) {
          return { ok: true, json: async () => ({ count: events.length, items: events }) };
        }
        if (url.endsWith(`/api/v1/paper-trades/${paperTrade("PENDING").tradeId}/market-price`)) {
          trades = [paperTrade("OPEN")];
          events = [
            ...events,
            {
              tradeId: trades[0].tradeId,
              sequence: 2,
              eventType: "OPENED",
              occurredAt: trades[0].updatedAt,
              details: {},
            },
          ];
          return { ok: true, json: async () => trades[0] };
        }
        return { ok: false, status: 404, json: async () => ({}) };
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("creates a pending trade and opens it after the entry price arrives", async () => {
    const user = userEvent.setup();
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <PaperTradingPanel setups={[setup]} />
      </QueryClientProvider>,
    );

    await user.click(await screen.findByRole("combobox", { name: "Paper trade setup" }));
    await user.click(await screen.findByText("BTCUSDT · LONG · 90"));
    await user.click(screen.getByRole("button", { name: /Új trade/i }));

    await waitFor(() => expect(screen.getAllByText("PENDING").length).toBeGreaterThan(0));
    expect(await screen.findByText("paper-risk-v1")).toBeInTheDocument();
    expect(await screen.findByText("CREATED")).toBeInTheDocument();

    const priceInput = screen.getByLabelText("Paper market price");
    await user.type(priceInput, "100");
    await user.click(screen.getByRole("button", { name: /Ár küldése/i }));

    await waitFor(() => expect(screen.getAllByText("OPEN").length).toBeGreaterThan(0));
    expect(await screen.findByText("OPENED")).toBeInTheDocument();
  });
});
