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

Elkészült az első outcome evaluation application réteg:

- TradingView payload `execution` blokkból `TradePlan` építés;
- market data lekérés symbol, timeframe és a setup gyertya záróideje alapján;
- triple-barrier outcome futtatás importált gyertyákon.

Elkészült az első commission/slippage modell:

- bps-alapú oldalankénti commission;
- bps-alapú oldalankénti slippage;
- bruttó `realized_r`;
- nettó `net_realized_r`;
- részletes `TradeCostEstimate`.

Elkészült az első MFE/MAE számítás:

- `TradeExcursion` modell;
- maximum favorable excursion R-ben;
- maximum adverse excursion R-ben;
- irányhelyes long/short ármezők;
- `NOT_TRIGGERED` esetben üres excursion.

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
- Az első outcome evaluation a setup `barCloseTime` értékétől induló market
  data szeletet kér, hogy ne használjon a setup gyertya előtti adatot.
- A commission és slippage első verziója egyszerű round-trip becslés, amely az
  entry és exit notional összegére alkalmazott bps költséget R-re vetíti.
- A bruttó R mező megmarad, hogy később tisztán össze lehessen hasonlítani a
  költségek előtti és utáni backtest eredményeket.
- Az MFE/MAE számítás az entry aktiválódása utáni, exitig vizsgált gyertyákból
  dolgozik. Így megmutatja, mennyit adott a piac a setup irányába és mennyire
  ment ellene még akkor is, ha a végső outcome csak `WIN`, `LOSS` vagy
  `TIMEOUT`.

## 3. Ellenőrzés

- Célzott outcome teszt: `uv run pytest tests/test_outcomes.py`.
- Célzott CSV market data teszt: `uv run pytest tests/test_csv_market_data.py`.
- Célzott outcome evaluation teszt:
  `uv run pytest tests/test_outcome_evaluation.py`.
- Célzott commission/slippage ellenőrzés az outcome és outcome evaluation
  tesztekben.
- Célzott MFE/MAE ellenőrzés az outcome tesztekben.
- Teljes backend regresszió: `uv run pytest`.
- Statikus ellenőrzés: `uv run ruff check .`, `uv run mypy src`.

## 4. Következő lépés

A következő Phase 5 szeletben érdemes outcome rekord persistence-t és az első
backtest analytics aggregációkat bevezetni, hogy a backtest eredmények már
adatbázisban is auditálhatók legyenek.
