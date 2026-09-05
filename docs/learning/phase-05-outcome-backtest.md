# Phase 05: Outcome és backtest

## 1. Mit építettünk?

Elkészült az első outcome domain modul:
`apps/api/src/smc_assistant/domain/outcomes.py`.

Az első szelet egy conservative triple-barrier engine:

- validált `TradePlan`;
- `OutcomeConfig` maximális tartási és entry timeout gyertyaszámmal;
- `TradeOutcome` auditálható kimeneti mezőkkel;
- `evaluate_triple_barrier_outcome` függvény.

Elkészült az első market data input réteg is:

- `MarketDataQuery`;
- `MarketDataProvider` protocol;
- `CsvMarketDataProvider`;
- timeframe alapú `close_time` inferálás.

## 2. Fontos döntések

- Az engine csak lezárt, jövőbeli OHLCV gyertyákból dolgozik.
- A gyertyákat időrendben várja, és rendezetlen inputra hibát dob.
- Az entry akkor aktiválódik, ha a gyertya high/low tartománya érinti az entry
  árat.
- Ha az entry nem aktiválódik az entry timeout ablakban, az outcome
  `NOT_TRIGGERED`.
- Ha ugyanazon gyertyán belül a stop és a target is érinthető, konzervatívan a
  stop számít előbbinek.
- Vertikális barrier esetén az exit ár az utolsó vizsgált gyertya záróára.
- A `realized_r` ugyanarra az R-alapú logikára épül, mint a korábbi risk modul.
- A CSV provider csak UTC időbélyegeket fogad el, hogy a backtest ne keverjen
  lokális és tőzsdei időzónákat.
- A provider csak időrendben rendezett gyertyákat fogad el.

## 3. Ellenőrzés

- Célzott outcome teszt: `uv run pytest tests/test_outcomes.py`.
- Célzott CSV market data teszt: `uv run pytest tests/test_csv_market_data.py`.
- Teljes backend regresszió: `uv run pytest`.
- Statikus ellenőrzés: `uv run ruff check .`, `uv run mypy src`.

## 4. Következő lépés

A következő Phase 5 szeletben érdemes összekötni a `MarketDataProvider`
interfészt az outcome engine-nel, hogy egy setup candidate trade tervéből és
egy importált OHLCV idősorból automatikusan outcome rekord készüljön.
