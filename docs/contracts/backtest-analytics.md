# Backtest analytics API

## Végpontok

`GET /api/v1/analytics/summary?runId=<UUID>&symbol=<opcionális instrumentum>`

`GET /api/v1/analytics/report?runId=<UUID>`

`GET /api/v1/analytics/by-session?runId=<UUID>`

`GET /api/v1/analytics/by-score-bucket?runId=<UUID>`

A `runId` kötelező, így külön futások eredményei nem keverednek. A `symbol`
pontos egyezéssel szűr, 1-40 karakter hosszú lehet. Hibás vagy hiányzó UUID,
illetve hibás szimbólumparaméter esetén a válasz `422`.

A válasz a teljes kiválasztott futásra vonatkozik, nincs 50/100 rekordos
listalimit. A korábbi közvetlen outcome rekordokkal való kompatibilitás miatt
ismeretlen UUID vagy üres szimbólumszűrés esetén `200` és üres statisztika
érkezik. Ez csak a mentett outcome-okat méri. A HTTP-n indított teljes futás
meglétét a `GET /api/v1/backtests/{run_id}` ellenőrzi, amely ismeretlen futásra
404-et ad. A futtatást a `backtests.md` dokumentálja.

A `report` csak teljes, mentett backtest futáshoz érhető el; ismeretlen
`runId` esetén 404-et ad. A másik két új végpont ugyanennek a jelentésnek a
session-, illetve score-bucket részhalmazát adja `count` és `items` mezőkkel.

## Válasz

A külső mezők `runId`, `symbol` és `statistics`. A `statistics` tartalma:

| Mező | Jelentés |
| --- | --- |
| `totalSetups` | Az összes mentett eredmény száma a kiválasztásban. |
| `closedTrades` | WIN, LOSS, BREAK_EVEN és TIMEOUT címkéjű trade-ek száma. |
| `excludedSetups` | NOT_TRIGGERED, CANCELLED és INVALIDATED darabszám együtt. |
| `outcomeCounts` | Minden outcome címke darabszáma, a nulla értékekkel is. |
| `netWins` | Pozitív nettó R-rel zárult trade-ek. |
| `netLosses` | Negatív nettó R-rel zárult trade-ek. |
| `netBreakEven` | Pontosan nulla nettó R-rel zárult trade-ek. |
| `netWinRate` | `netWins / closedTrades`, 0-1 arány, nem százalék. |
| `totalNetR` | A lezárt trade-ek nettó R értékeinek összege. |
| `netExpectancyR` | `totalNetR / closedTrades`, a megfigyelt átlagos nettó R. |
| `netProfitR` | A pozitív nettó R értékek összege. |
| `netLossR` | A negatív nettó R értékek összegének abszolút értéke. |
| `netProfitFactor` | `netProfitR / netLossR`, R-alapú profit factor. |

A nyerő/vesztő besorolás a mentett `net_realized_r` előjeléből készül, nem
a barrier címkéből. Egy targetet elérő, `WIN` címkéjű trade költségek után
vesztes is lehet. A timeoutok előjelük szerint számítanak bele, a nullszaldók
a win rate és expectancy nevezőjében is szerepelnek. Az inaktív/elvetett
setupok a trade-mutatókat nem módosítják. Jelenleg ezekre nem szimulálunk
pozíciózárást; ha ez változik, a számlálási szabályt is módosítani kell.

Ha nincs lezárt trade, a win rate és expectancy `null`. Ha nincs negatív
nettó eredmény, a profit factor `null`: ilyenkor az arány nem számítható,
nem küldünk JSON `Infinity` értéket. Csak vesztes trade-eknél profit factor
`0`. A teljesen üres kiválasztás darabszámai és R-összegei nullák.

A számítás a tárolt nettó R értékeken fut, új költséget nem von le. Az
R-összegek négy, az arányok és expectancy hat tizedesre kerekítettek. Az
osztás a kerekítés előtti összegekkel történik. Hiányzó vagy nem véges nettó
R-rel rendelkező lezárt trade esetén a számítás hibát jelez; ilyen rekordot
nem hagy figyelmen kívül.

Az R-alapú mutatók nem számlapénznemben számolt eredmények: eltérő pozícióméret
vagy kockáztatott pénzösszeg esetén a pénzalapú profit factor eltérhet.

## Részletes teljesítményjelentés

A `report` a korábbi `statistics` blokk mellett az alábbiakat tartalmazza:

| Mező | Jelentés |
| --- | --- |
| `risk.averageWinR` | Pozitív nettó R eredmények átlaga. |
| `risk.averageLossR` | Negatív nettó R eredmények előjeles átlaga. |
| `risk.maximumDrawdownR` | Kumulált nettó R korábbi csúcsától mért legnagyobb visszaesés. |
| `risk.longestWinningStreak` | Egymást követő pozitív nettó eredmények maximuma. |
| `risk.longestLosingStreak` | Egymást követő negatív nettó eredmények maximuma. |
| `equityCurve` | Trade-enként idő, nettó/kumulált R és drawdown. |
| `bySession` | Trading session szerinti statisztika. |
| `byInstrument` | Exchange és instrumentum szerinti statisztika. |
| `byDirection` | LONG és SHORT szerinti statisztika. |
| `byScoreBucket` | `0-49`, `50-69`, `70-84`, `85-100` score tartományok. |
| `byStrategyVersion` | Strategy version szerinti statisztika. |
| `bySetupComponent` | Komponens és `ZERO`/`PARTIAL`/`FULL` állapot szerinti statisztika. |
| `decisions` | Journal döntések és a rule score javaslatának összevetése. |

Az equity curve a lezárás időpontja, majd outcome UUID szerint rendezett.
Nullszaldó megszakítja a nyerő és vesztes sorozatot. A görbe nem compounding
számlaegyenleg, hanem fix kockázati egységek összege, ezért pénzügyi
hozamgörbeként nem értelmezhető.

A score-bucket és komponensbontás az immutable backtest inputból újraszámolt,
a válasz `scoringConfigVersion` mezőjében megnevezett rule score-ra épül. A
journal összevetésben a rendszerjavaslat követése az accepted+TAKEN vagy
rejected+SKIPPED pár; a `NOT_RECORDED` sorok nem kerülnek az agreement rate
nevezőjébe. A kihagyott setupok eredménye counterfactual backtest eredmény.

## Kipróbálás

Futó Docker API mellett az összesítő üres eredménye ellenőrizhető egy ismeretlen
azonosítóval:

```bash
curl 'http://localhost:8000/api/v1/analytics/summary?runId=00000000-0000-0000-0000-000000000000'
```

Az összetett riport csak létező futáshoz érhető el; ismeretlen `runId` esetén
`404` választ ad. Valós mentett futáshoz a mentéskor kapott `runId` értéket add
meg:

```bash
curl 'http://localhost:8000/api/v1/analytics/report?runId=<RUN_ID>'
```

Interaktív lekérdezés: `http://localhost:8000/docs`, `analytics` csoport.

A mentéstől a HTTP-válaszig tartó teszt az `apps/api` könyvtárból:

```bash
uv run pytest tests/test_analytics_api.py tests/test_backtest_analytics.py
```
