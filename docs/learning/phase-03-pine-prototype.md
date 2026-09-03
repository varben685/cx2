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

Az első TradingView próba túl zajosnak bizonyult, mert minden debug marker
látszott egyszerre. A túl szigorú clean nézet viszont szinte mindent elrejtett.
Ezért az alapértelmezett nézet most balanced:

- `leftBars/rightBars = 3/3`, közepesen érzékeny pivotokkal;
- swing label, sweep label és displacement marker alapból kikapcsolva;
- BOS és CHoCH label alapból bekapcsolva;
- FVG boxok alapból látszanak, de csak az utolsó 8 marad a charton.
- A legutóbbi swing high és swing low szint alapból két finom, jobbra nyúló
  vonalként látszik.
- A jobb oldalon egy kis bias badge mutatja az aktuális `BULLISH`, `BEARISH`
  vagy `NEUTRAL` állapotot.
- A BOS/CHoCH logika a bar elején ismert, figyelt swing szinteket használja,
  és csak ezután dolgozza fel az újonnan megerősített pivotokat.
- A semleges bias megerősített swing-sorozatból is képes irányt találni:
  magasabb high + magasabb low esetén `BULLISH`, alacsonyabb high + alacsonyabb
  low esetén `BEARISH`.

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
- Ha részletes diagnosztika kell, a kikapcsolt debug elemek egyenként
  visszakapcsolhatók az indikátor beállításaiban.
- Ha BOS/CHoCH épp nincs a látható chart szakaszon, a legutóbbi struktúraszintek
  akkor is mutatják, milyen törést figyel az indikátor.
- A bias bootstrap nem jelent kereskedési setupot önmagában. Csak kontextust ad,
  hogy a későbbi ellentétes structure break már CHoCH-ként értelmezhető legyen.

## 4. Repainting védelem

A swing jelölés `ta.pivothigh` és `ta.pivotlow` alapján készül. Ezek a pivotot
csak `rightBars` gyertya után erősítik meg, ezért a vizuális jelölés a múltbeli
pivotgyertyára kerül, de csak késve válik ismertté.

Ez ugyanaz a szemlélet, mint a backend domain modellben: nem kezelünk pivotot
ismertként a megerősítő gyertyák lezárása előtt.

Fontos Pine-specifikus részlet: egy baron egyszerre történhet ármozgás és új
pivot-visszaigazolás. Ezért a BOS vizsgálat először a bar elején ismert
`watchedSwingHigh/Low` szinteken fut, és csak utána frissül a legutóbbi pivot.
Így nem veszítünk el egy törést azért, mert ugyanazon a baron egy új pivot is
megerősítést kapott.

## 5. Kapcsolódó fájlok

- `tradingview/indicators/smc_assistant_prototype.pine`
- `apps/api/src/smc_assistant/contracts/tradingview.py`
- `docs/contracts/tradingview-webhook.md`
- `docs/strategy/market-structure.md`
- `docs/strategy/fair-value-gaps.md`
- `docs/strategy/liquidity.md`
- `docs/strategy/displacement.md`

## 6. Következő lépés

A következő Phase 3 szeletben TradingView editorban kell újra ellenőrizni a
balanced alapnézetet és a bias bootstrap viselkedését, majd a tényleges alert
payloadot összevetni a backend Pydantic contracttal.
