# Phase 03: Pine Script prototípus

## 1. Mit építettünk?

Elkészült az első TradingView indikátor prototípus:
`tradingview/indicators/smc_assistant_prototype.pine`.

Ez még nem végleges stratégia, hanem vizuális és alert alap:

- confirmed pivot alapú swing high / swing low jelölés;
- BOS és CHoCH jelölés;
- háromgyertyás bullish és bearish FVG box;
- liquidity sweep jelölés;
- egyszerű displacement score;
- backend contracthoz igazított JSON alert payload váz;
- egyszerű FVG equilibrium entry, stop loss, take profit és risk-reward számítás.

## 2. Miért erre van szükség?

A backend már fogad TradingView webhookot, de kell egy TradingView oldali forrás,
ami képes a setup candidate események előállítására. A Pine prototípus célja,
hogy korán lássuk a charton, hogyan viselkednek a szabályok, és milyen alert
mezőket kell pontosítani.

## 3. Fontos korlátok

- A scriptet lokálisan nem tudjuk Pine fordítóval ellenőrizni.
- Az `execution` blokk első számítása egyszerű: FVG equilibrium entry, FVG-n
  kívüli stop, fix 2R target.
- A risk-reward még prototípus logika, nem végleges kereskedési szabály.
- A session felismerés egyszerűsített.
- A production alert előtt TradingView editorban kézzel fordítani és finomítani
  kell.

## 4. Repainting védelem

A swing jelölés `ta.pivothigh` és `ta.pivotlow` alapján készül. Ezek a pivotot
csak `rightBars` gyertya után erősítik meg, ezért a vizuális jelölés a múltbeli
pivotgyertyára kerül, de csak késve válik ismertté.

Ez ugyanaz a szemlélet, mint a backend domain modellben: nem kezelünk pivotot
ismertként a megerősítő gyertyák lezárása előtt.

## 5. Kapcsolódó fájlok

- `tradingview/indicators/smc_assistant_prototype.pine`
- `apps/api/src/smc_assistant/contracts/tradingview.py`
- `docs/contracts/tradingview-webhook.md`
- `docs/strategy/market-structure.md`
- `docs/strategy/fair-value-gaps.md`
- `docs/strategy/liquidity.md`
- `docs/strategy/displacement.md`

## 6. Következő lépés

A következő Phase 3 szeletben TradingView editorban kell fordítani a scriptet,
majd a tényleges alert payloadot összevetni a backend Pydantic contracttal.
