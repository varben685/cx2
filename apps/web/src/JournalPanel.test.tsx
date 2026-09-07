import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { JournalEntry, SetupCandidate } from "./api";
import { JournalPanel } from "./JournalPanel";

const setup: SetupCandidate = {
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
  score: 92,
  accepted: true,
  components: [],
  rejectionReasons: [],
  positiveReasons: ["Bullish structure"],
  negativeReasons: [],
  barCloseTime: "2026-01-01T12:01:00Z",
  receivedAt: "2026-01-01T12:01:01Z",
};

const journal: JournalEntry = {
  journalId: "47e97845-3307-4e8f-a910-33c0b99ee2ae",
  setupId: setup.setupId,
  outcomeId: "67281361-d585-493a-b954-ea74349db0b0",
  eventId: setup.eventId,
  symbol: setup.symbol,
  exchange: setup.exchange,
  timeframe: setup.timeframe,
  direction: setup.direction,
  session: "NEW_YORK",
  strategyVersion: setup.strategyVersion,
  signalTime: setup.barCloseTime,
  outcomeLabel: "WIN",
  realizedR: 1.937,
  mfeR: 2.2,
  maeR: -0.2,
  executionStatus: "TAKEN",
  userNote: "Waited for confirmation.",
  screenshotReference: "screenshots/btc-long.png",
  manualRating: 4,
  manualOverride: false,
  overrideReason: null,
  tags: ["A+", "patience"],
  revision: 2,
  createdAt: "2026-01-01T12:05:00Z",
  updatedAt: "2026-01-01T12:06:00Z",
  setupSnapshot: { sourcePayload: { eventId: setup.eventId } },
  outcomeSnapshot: { outcomeId: "67281361-d585-493a-b954-ea74349db0b0" },
};

function renderPanel() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <JournalPanel />
    </QueryClientProvider>,
  );
}

function stubFetch(initialEntries: JournalEntry[] = [journal]) {
  let entries = initialEntries;
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes("/api/v1/setups?")) {
      return Promise.resolve({ ok: true, json: async () => ({ count: 1, items: [setup] }) });
    }
    if (url.endsWith("/revisions")) {
      return Promise.resolve({ ok: true, json: async () => ({ count: 2, items: [journal, journal] }) });
    }
    if (url.includes(`/api/v1/journal/${journal.journalId}`) && init?.method === "PUT") {
      const body = JSON.parse(String(init.body)) as { userNote: string };
      entries = [{ ...journal, userNote: body.userNote, revision: 3 }];
      return Promise.resolve({ ok: true, json: async () => entries[0] });
    }
    if (url.includes(`/api/v1/journal/${journal.journalId}`)) {
      return Promise.resolve({ ok: true, json: async () => entries[0] ?? journal });
    }
    if (url.includes("/api/v1/journal?") && init?.method !== "POST") {
      return Promise.resolve({ ok: true, json: async () => ({ count: entries.length, items: entries }) });
    }
    if (url.includes(`/api/v1/setups/${encodeURIComponent(setup.setupId)}/journal`)) {
      entries = [{ ...journal, revision: 1, outcomeId: null }];
      return Promise.resolve({ ok: true, status: 201, json: async () => entries[0] });
    }
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}) });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("JournalPanel", () => {
  beforeEach(() => {
    stubFetch();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows journal context, notes and revision history", async () => {
    const user = userEvent.setup();
    renderPanel();

    expect(await screen.findByText("Döntési napló")).toBeInTheDocument();
    expect((await screen.findAllByText("1.937R")).length).toBeGreaterThan(0);
    await user.click(screen.getByLabelText("Journal megnyitása"));
    const drawerTitle = await screen.findByText("Journal részletek");
    const drawer = drawerTitle.closest(".ant-drawer-content") as HTMLElement;
    expect(within(drawer).getByText("Waited for confirmation.")).toBeInTheDocument();
    expect(within(drawer).getAllByText(/v2/)).toHaveLength(2);
  });

  it("creates a journal for an available setup", async () => {
    const user = userEvent.setup();
    const fetchMock = stubFetch([]);
    renderPanel();

    await user.click(await screen.findByRole("button", { name: /Új bejegyzés/i }));
    await user.type(screen.getByLabelText("Megjegyzés"), "Clean execution.");
    await user.click(screen.getByRole("button", { name: "Mentés" }));
    expect((await screen.findAllByText("TAKEN")).length).toBeGreaterThan(0);

    const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(String(post?.[0])).toContain(encodeURIComponent(setup.setupId));
    const body = JSON.parse(String(post?.[1]?.body)) as { userNote: string; outcomeId?: string };
    expect(body.userNote).toBe("Clean execution.");
    expect(body.outcomeId).toBeUndefined();
  });

  it("updates with the loaded revision", async () => {
    const user = userEvent.setup();
    const fetchMock = stubFetch();
    renderPanel();

    await user.click(await screen.findByLabelText("Journal megnyitása"));
    await user.click(await screen.findByRole("button", { name: /Szerkesztés/i }));
    const note = screen.getByLabelText("Megjegyzés");
    await user.clear(note);
    await user.type(note, "Updated discipline note.");
    await user.click(screen.getByRole("button", { name: "Mentés" }));

    expect((await screen.findAllByText("Updated discipline note.")).length).toBeGreaterThan(0);
    const put = fetchMock.mock.calls.find(([, init]) => init?.method === "PUT");
    const body = JSON.parse(String(put?.[1]?.body)) as { expectedRevision: number };
    expect(body.expectedRevision).toBe(2);
  });
});
