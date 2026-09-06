# Backtest analytics API

## Végpont

`GET /api/v1/analytics/summary?runId=<UUID>&symbol=<opcionális instrumentum>`

A `runId` kötelező, így külön futások eredményei nem keverednek. A `symbol`
pontos egyezéssel szűr, 1-40 karakter hosszú lehet. Hibás vagy hiányzó UUID,
illetve hibás szimbólumparaméter esetén a válasz `422`.

A válasz a teljes kiválasztott futásra vonatkozik, nincs 50/100 rekordos
listalimit. A korábbi közvetlen outcome rekordokkal való kompatibilitás miatt
ismeretlen UUID vagy üres szimbólumszűrés esetén `200` és üres statisztika
érkezik. Ez csak a mentett outcome-okat méri. A HTTP-n indított teljes futás
meglétét a `GET /api/v1/backtests/{run_id}` ellenőrzi, amely ismeretlen futásra
404-et ad. A futtatást a `backtests.md` dokumentálja.

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

## Kipróbálás

Futó Docker API mellett üres eredmény ellenőrzése:

```bash
curl 'http://localhost:8000/api/v1/analytics/summary?runId=00000000-0000-0000-0000-000000000000'
```

Valós mentett futáshoz a mentéskor használt `run_id` értéket add meg.
Interaktív lekérdezés: `http://localhost:8000/docs`, `analytics` csoport.

A mentéstől a HTTP-válaszig tartó teszt az `apps/api` könyvtárból:

```bash
uv run pytest tests/test_analytics_api.py tests/test_backtest_analytics.py
```
