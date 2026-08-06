# TradingView webhook contract

Az első verzió célja egy verziózott JSON payload, amely Pydantic modellel
validálható és JSON Schema formában is exportálható.

```json
{
  "schemaVersion": "1.0",
  "eventId": "BTCUSDT-1m-1720000000-bullish-choch",
  "eventType": "SETUP_CANDIDATE",
  "source": "TRADINGVIEW",
  "strategyVersion": "smc-rce-v1",
  "symbol": "BTCUSDT",
  "exchange": "BINANCE",
  "timeframe": "1",
  "barOpenTime": "2026-01-01T12:00:00Z",
  "barCloseTime": "2026-01-01T12:01:00Z",
  "direction": "LONG"
}
```

Következő fázisban ez részletes `marketStructure`, `fvg`, `execution` és
`features` blokkokkal bővül.

