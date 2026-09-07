import type { BacktestRequest } from "./api";

export function createExampleBacktest(): BacktestRequest {
  return {
    runId: crypto.randomUUID(),
    setups: [
      {
        schemaVersion: "1.0",
        eventId: `synthetic-btc-long-${Date.now()}`,
        eventType: "SETUP_CANDIDATE",
        source: "TRADINGVIEW",
        strategyVersion: "smc-rce-v1",
        symbol: "BTCUSDT",
        exchange: "BINANCE",
        timeframe: "1",
        barOpenTime: "2026-01-01T12:00:00Z",
        barCloseTime: "2026-01-01T12:01:00Z",
        direction: "LONG",
        marketStructure: {
          htfTimeframe: "15",
          htfBias: "BULLISH",
          bos: true,
          choch: true,
          liquiditySweep: true,
        },
        fvg: {
          lower: 99,
          upper: 101,
          equilibrium: 100,
          sizeAtrRatio: 0.42,
          mitigationPercent: 0,
        },
        execution: {
          entry: 100,
          stopLoss: 95,
          takeProfit: 110,
          riskReward: 2,
        },
        features: {
          atr: null,
          relativeVolume: null,
          displacementScore: 0.81,
          session: "NEW_YORK",
        },
      },
    ],
    candlesCsv: [
      "symbol,timeframe,time,open,high,low,close,volume",
      "BTCUSDT,1,2026-01-01T12:01:00Z,100,101,99,100,1000",
      "BTCUSDT,1,2026-01-01T12:02:00Z,100,111,99,110,1000",
    ].join("\n"),
    config: {
      maxHoldingBars: 30,
      entryTimeoutBars: 5,
      commissionBpsPerSide: 10,
      slippageBpsPerSide: 5,
    },
  };
}
