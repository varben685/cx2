# Paper trading

A paper trading kizárólag szimulált végrehajtás. A rendszerben nincs broker
adapter és semmilyen útvonal nem tud valódi tőzsdei megbízást küldeni.

## Automatikus mód

Docker Compose alatt az automatikus mód alapértelmezésben aktív. Fontos env
változók:

```bash
PAPER_AUTO_TRADE_ENABLED=true
PAPER_ACCOUNT_BALANCE=10000
PAPER_DEFAULT_RISK_PERCENT=1
PAPER_NOTIFICATION_ADAPTER=log
```

Egy új, score és risk policy szerint elfogadott `SETUP_CANDIDATE` webhookból
`PENDING` trade készül. A `MARKET_PRICE` webhook ugyanazon symbol, exchange és
timeframe aktív trade-jeit frissíti. Entry elérésekor `OPEN`, stop vagy target
elérésekor `CLOSED` állapot következik.

Terminális állapotnál a backend automatikusan live outcome rekordot készít,
frissíti a már létező journal bejegyzést, és a `log` adapterrel strukturált
értesítési eseményt ír. Az adapter `PAPER_NOTIFICATION_ADAPTER=none` értékkel
kikapcsolható. A lezárt eredmények a `GET /api/v1/outcomes/paper-trades`
végponton ellenőrizhetők; hiányzó rekordok a
`POST /api/v1/outcomes/paper-trades/reconcile` hívással pótolhatók.

## TradingView beállítás

A Pine prototípus `Send paper price updates` kapcsolója alapértelmezésben ki
van kapcsolva. Bekapcsolás után a lezárt, setupot nem tartalmazó gyertyák
`MARKET_PRICE` alertet küldenek. A TradingView alertet az `Any alert() function
call` feltétellel kell létrehozni, és a webhook URL a publikus vagy tunnel mögötti
`POST /api/v1/webhooks/tradingview` végpont legyen.

Az alert létrehozása után megváltoztatott Pine inputok nem írják át a már
létező alert snapshotját; ilyenkor az alertet újra létre kell hozni.

## Korlátok

- Az árjel jelenleg gyertyazáró ár, nem tick- vagy OHLC-stream.
- A setup gyertyáján nem küld külön price eseményt, az első frissítés a következő
  lezárt gyertyán érkezik.
- Nincs pending timeout, részleges fill, gap, commission vagy slippage modell.
- A market price esemény mentése megelőzi a trade-frissítést. Ritka belső hiba
  után automatikus retry/outbox még nincs.
- Több API workerhez adatbázisszintű portfólió-lock szükséges.
- Az értesítés best effort, nincs tartós outbox vagy automatikus újraküldés.
