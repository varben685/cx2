import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

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
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: "ok",
          service: "smc-assistant-api",
          version: "0.1.0",
          timestamp: "2026-01-01T12:00:00Z",
        }),
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
});
