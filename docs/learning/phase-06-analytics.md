# Phase 06: Teljesítmény-analytics

## 1. Elkészült

A kiválasztott backtest futáshoz részletes analytics jelentés készült: equity
curve, átlagos nyerő és vesztes R, maximum drawdown, nyerő/vesztes sorozatok,
hatféle bontás és journal döntési összevetés. A dashboard mindezt a futás
eredményei mellett jeleníti meg.

## 2. Hogyan működik?

A backend a mentett futás immutable setupjait összekapcsolja az outcome-okkal,
exit idő szerint rendezi a lezárt trade-eket, majd kumulálja a nettó R-t. A
setup inputból ugyanazzal a verziózott rule score-ral score-t és komponens-
állapotokat számol. Az eventId alapján megtalált journal döntések külön
összevetésbe kerülnek.

## 3. Trading fogalmak

- `Equity curve`: itt a lezárt trade-ek kumulált nettó R sorozata.
- `Maximum drawdown`: a korábbi R-csúcstól a későbbi mélypontig mért legnagyobb
  visszaesés.
- `Losing streak`: egymást követő negatív nettó R trade-ek száma.
- `Counterfactual`: egy kihagyott setup szimulált eredménye, amely nem valódi
  megkötött trade.

## 4. Technikai fogalmak

- `Run-scoped`: minden jelentés egyetlen backtest futáshoz tartozik.
- `Deterministic grouping`: ugyanaz a setup és scoring verzió mindig ugyanabba
  a bontási csoportba kerül.
- `Accessible SVG`: a grafikon reszponzív vektorgrafika, géppel olvasható
  címkével és pontonkénti leírással.

## 5. Ellenőrzés

A számítási teszt szándékosan rendezetlen outcome-okkal ellenőrzi az időrendet,
a drawdownt, az átlagokat és a sorozatokat. Külön teszt fedi a session-, score-,
komponens- és journal bontást. Az API memória, SQLite és PostgreSQL adapterrel,
a frontend pedig contracthű válasszal fut.

## 6. Manuális kipróbálás

Nyisd meg a `http://localhost:5173` oldalt, válassz egy backtest futást, majd a
futás összesítője alatt nézd meg a `Teljesítményelemzés` részt. A bontások
fülein összehasonlítható a session, score, direction, komponens, instrumentum
és stratégia.

## 7. Fontos fájlok

- `analytics/performance.py`: időrend, equity, drawdown és sorozatok.
- `application/performance_analytics.py`: bontások és journal összevetés.
- `api/analytics.py`: report és részhalmaz végpontok.
- `AnalyticsReportPanel.tsx`: KPI-k, SVG görbe és bontási táblák.
- `docs/contracts/backtest-analytics.md`: pontos számítási contract.

## 8. Döntések és feltételezések

A görbe fix R-alapú, nem számlaegyenleg. A score a mentett setup inputból a
`scoringConfigVersion` szerint újraszámolt érték. Nullszaldó mindkét sorozatot
megszakítja. Azonos exit idő esetén az outcome UUID ad stabil sorrendet.

## 9. Kockázatok és nyitott kérdések

Egy backtest jelenleg egy instrumentumot enged, ezért az instrumentumbontás egy
futáson belül rendszerint egysoros. Nincs pénzalapú pozícióméret, párhuzamos
pozíciókezelés, compounding, benchmark vagy konfidenciaintervallum. Kis mintán
a mutatók leíró értékűek, nem statisztikai bizonyítékok.

## 10. Következő mérföldkő

Phase 7 paper trading workflow: élő webhookból követhető setup-életciklus,
outcome frissítés, értesítési adapter, valamint napi és heti összesítő.
