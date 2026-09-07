import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { BacktestRun, OutcomeRecord } from "./api";
import { BacktestsPanel } from "./BacktestsPanel";

const run: BacktestRun = {
  runId: "c70c415f-95b7-4faa-bfca-f1a5b6a7d151",
  status: "COMPLETED",
  startedAt: "2026-01-01T12:03:00Z",
  completedAt: "2026-01-01T12:03:01Z",
  symbol: "BTCUSDT",
  exchange: "BINANCE",
  timeframe: "1",
  strategyVersion: "smc-rce-v1",
  requestSha256: "a".repeat(64),
  config: {
    maxHoldingBars: 30,
    entryTimeoutBars: 5,
    commissionBpsPerSide: 10,
    slippageBpsPerSide: 5,
  },
  outcomeIds: ["c3bc2e95-011d-4278-a40e-0633fb51a018"],
  statistics: {
    totalSetups: 1,
    closedTrades: 1,
    excludedSetups: 0,
    outcomeCounts: { WIN: 1 },
    netWins: 1,
    netLosses: 0,
    netBreakEven: 0,
    netWinRate: 1,
    totalNetR: 1.937,
    netExpectancyR: 1.937,
    netProfitR: 1.937,
    netLossR: 0,
    netProfitFactor: null,
  },
};

const outcome: OutcomeRecord = {
  outcomeId: run.outcomeIds[0],
  runId: run.runId,
  eventId: "synthetic-btc-long-demo-001",
  symbol: "BTCUSDT",
  timeframe: "1",
  direction: "LONG",
  entryPrice: 100,
  stopLoss: 95,
  takeProfit: 110,
  evaluatedAt: "2026-01-01T12:03:01Z",
  engineVersion: "triple-barrier-v1",
  marketDataSha256: "b".repeat(64),
  outcome: {
    label: "WIN",
    exitReason: "TAKE_PROFIT_HIT",
    realizedR: 2,
    netRealizedR: 1.937,
    costs: {
      commissionAmount: 0.021,
      slippageAmount: 0.0105,
      totalAmount: 0.0315,
      costR: 0.063,
    },
    excursion: {
      mfeR: 2.2,
      maeR: -0.2,
      maxFavorablePrice: 111,
      maxAdversePrice: 99,
    },
    entryTime: "2026-01-01T12:02:00Z",
    exitTime: "2026-01-01T12:03:00Z",
    exitPrice: 110,
    barsToEntry: 1,
    barsHeld: 2,
  },
};

function renderPanel() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BacktestsPanel />
    </QueryClientProvider>,
  );
}

function stubBacktestFetch(options: { initialRuns?: BacktestRun[]; createError?: string } = {}) {
  let runs = options.initialRuns ?? [run];
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes("/api/v1/outcomes?")) {
      return Promise.resolve({ ok: true, json: async () => ({ count: 1, items: [outcome] }) });
    }
    if (url.includes("/api/v1/backtests?") && init?.method !== "POST") {
      return Promise.resolve({ ok: true, json: async () => ({ count: runs.length, items: runs }) });
    }
    if (url.endsWith("/api/v1/backtests") && init?.method === "POST") {
      if (options.createError) {
        return Promise.resolve({
          ok: false,
          status: 422,
          json: async () => ({ detail: options.createError }),
        });
      }
      runs = [run];
      return Promise.resolve({ ok: true, status: 201, json: async () => run });
    }
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}) });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("BacktestsPanel", () => {
  beforeEach(() => {
    stubBacktestFetch();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a saved run, statistics and outcome details", async () => {
    const user = userEvent.setup();
    renderPanel();

    expect(await screen.findByText("Backtest futások")).toBeInTheDocument();
    expect((await screen.findAllByText("BTCUSDT")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("1.937R")).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("100.0%")).toHaveLength(2);

    await user.click(screen.getByLabelText("Outcome részletek"));
    const drawer = await screen.findByText("Outcome részletek");
    const drawerRoot = drawer.closest(".ant-drawer-content") as HTMLElement;
    expect(within(drawerRoot).getByText("TAKE_PROFIT_HIT")).toBeInTheDocument();
    expect(within(drawerRoot).getByText("0.063R")).toBeInTheDocument();
    expect(within(drawerRoot).getByText("2.200R / -0.200R")).toBeInTheDocument();
  });

  it("starts from the editable sample and refreshes the run list", async () => {
    const user = userEvent.setup();
    const fetchMock = stubBacktestFetch({ initialRuns: [] });
    renderPanel();

    await user.click(await screen.findByRole("button", { name: /Új backtest/i }));
    expect(String((screen.getByLabelText("Setup JSON") as HTMLTextAreaElement).value)).toContain("smc-rce-v1");
    expect(String((screen.getByLabelText("OHLCV CSV") as HTMLTextAreaElement).value)).toContain("BTCUSDT,1");
    await user.click(screen.getByRole("button", { name: /Futtatás/i }));

    expect(await screen.findByText("COMPLETED")).toBeInTheDocument();
    const postCall = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(postCall).toBeDefined();
    const payload = JSON.parse(String(postCall?.[1]?.body)) as { setups: unknown[]; candlesCsv: string };
    expect(payload.setups).toHaveLength(1);
    expect(payload.candlesCsv).toContain("open,high,low,close");
  });

  it("keeps invalid setup JSON in the modal without sending it", async () => {
    const user = userEvent.setup();
    const fetchMock = stubBacktestFetch({ initialRuns: [] });
    renderPanel();

    await user.click(await screen.findByRole("button", { name: /Új backtest/i }));
    const setupInput = screen.getByLabelText("Setup JSON");
    fireEvent.change(setupInput, { target: { value: "{" } });
    await user.click(screen.getByRole("button", { name: /Futtatás/i }));

    expect(await screen.findByText("A setup JSON nem értelmezhető.")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("shows the backend validation message", async () => {
    const user = userEvent.setup();
    stubBacktestFetch({ initialRuns: [], createError: "Not enough candles to persist a final outcome." });
    renderPanel();

    await user.click(await screen.findByRole("button", { name: /Új backtest/i }));
    await user.click(screen.getByRole("button", { name: /Futtatás/i }));
    expect(await screen.findByText("Not enough candles to persist a final outcome.")).toBeInTheDocument();
  });
});
