# SMC AI Trading Assistant – teljes projektindító Codex-utasítás

Dolgozz ebben a repositoryban vezető szoftverarchitektként, senior Python- és TypeScript-fejlesztőként, quantitative developer szerepben, valamint türelmes oktatóként.

A feladatod egy teljes, működőképes, tesztelt és dokumentált **SMC-alapú trading setup elemző és AI-támogatott kereskedési asszisztens** megtervezése és fokozatos megvalósítása.

A projekt munkaneve:

`smc-ai-trading-assistant`

## 1. Elsődleges cél

Olyan alkalmazást készíts, amely:

1. TradingView alert webhookokat fogad.
2. SMC/ICT-jellegű setupokat tárol és értékel.
3. Felismeri vagy fogadja az alábbi eseményeket:

   * swing high és swing low;
   * BOS;
   * CHoCH;
   * bullish és bearish Fair Value Gap;
   * liquidity sweep;
   * displacement;
   * FVG mitigation;
   * magasabb idősíkú bias;
   * kereskedési session;
   * belépési, stop loss és take profit szintek.
4. Determinisztikus, szabályalapú pontszámot számít a setupokra.
5. Automatikus trading journalt vezet.
6. Utólag megállapítja, hogy a setup nyertes, vesztes, nullszaldós vagy lejárt lett-e.
7. Backtestet és paper tradinget támogat.
8. Megfelelő mennyiségű adat után gépi tanulási modellel becsüli a setupok minőségét.
9. Közérthetően elmagyarázza, hogy egy setup miért kapott magas vagy alacsony pontszámot.
10. Webes dashboardon jeleníti meg az eredményeket.

A rendszer elsődleges célja nem az árfolyam biztos előrejelzése, hanem a kereskedési döntések:

* következetesebbé;
* mérhetőbbé;
* visszatesztelhetőbbé;
* reprodukálhatóbbá;
* kevésbé érzelemvezéreltté

tétele.

A projekt nem ígér és nem garantál profitot.

## 2. Kötelező munkamódszer

Ez egy összetett, többfázisú projekt. Ne próbáld egyetlen átláthatatlan módosítással elkészíteni.

Első lépésként:

1. Vizsgáld meg a repository jelenlegi tartalmát.
2. Hozz létre egy rövid, legfeljebb körülbelül 100–150 soros gyökérszintű `AGENTS.md` fájlt.
3. Hozd létre a részletes projekt-dokumentáció struktúráját.
4. Hozd létre a `docs/PLANS.md` fájlt, amely meghatározza az ExecPlanek használatát.
5. Hozd létre az első aktív végrehajtási tervet:

   * `docs/exec-plans/active/full-project.md`
6. A tervet a fejlesztés közben folyamatosan aktualizáld.
7. Mindig az első befejezetlen mérföldkőtől folytasd.
8. Egy mérföldkő befejezése után futtasd a hozzá tartozó teszteket.
9. Ne jelölj egy feladatot késznek, amíg a kód, a teszt és a dokumentáció nincs összhangban.

Ne kérdezd meg minden kisebb lépés után, hogy folytathatod-e. Folytasd önállóan a következő mérföldkővel.

Csak akkor állj meg, ha:

* külső hozzáférési adat szükséges;
* a felhasználónak kell TradingView-ban manuálisan létrehoznia egy alertet;
* olyan üzleti vagy stratégiai döntés hiányzik, amelyet nem lehet biztonságosan alapértelmezni;
* valódi tőzsdei megbízás engedélyezéséről lenne szó;
* a következő lépés adatvesztést, fizetős szolgáltatást vagy éles telepítést okozna.

Ne pusholj automatikusan távoli branchre, és ne végezz éles telepítést külön felhasználói engedély nélkül.

## 3. Oktatási követelmény

A repository tulajdonosa tapasztalt szoftverfejlesztő, de szeretné teljesen megérteni:

* a rendszerarchitektúrát;
* a Python kódot;
* a TypeScript kódot;
* a Pine Scriptet;
* az adatbázist;
* a trading fogalmakat;
* az SMC-stratégiát;
* a backtest működését;
* a statisztikai mérőszámokat;
* a gépi tanulást;
* az AI szerepét és korlátait.

Ezért minden fontos megoldást oktatási céllal is dokumentálj.

A magyarázatok nyelve magyar legyen. A kód, az osztálynevek, változónevek, API-nevek és technikai azonosítók angolul legyenek.

Minden fejlesztési fázishoz készüljön egy dokumentum:

`docs/learning/phase-XX-<topic>.md`

Minden ilyen dokumentum tartalmazza:

1. Mit építettünk?
2. Miért erre van szükség?
3. Hogyan működik a háttérben?
4. Milyen alternatívák léteznek?
5. Miért ezt az alternatívát választottuk?
6. Milyen trading fogalmak kapcsolódnak hozzá?
7. Milyen hibák vagy félreértések fordulhatnak elő?
8. Mely fájlokat érdemes elolvasnia a tulajdonosnak?
9. Hogyan lehet manuálisan kipróbálni?
10. Egy rövid gyakorlófeladatot a tulajdonos számára.

Ne használj indokolatlanul bonyolult absztrakciókat. A tisztaság és tanulhatóság fontosabb, mint a túlzott technikai „okosság”.

## 4. Dokumentációs struktúra

Hozd létre legalább a következő struktúrát:

```text
AGENTS.md
README.md
ARCHITECTURE.md

docs/
├── index.md
├── PLANS.md
├── glossary/
│   ├── trading-glossary.md
│   ├── ai-ml-glossary.md
│   └── software-glossary.md
├── strategy/
│   ├── strategy-specification.md
│   ├── market-structure.md
│   ├── fair-value-gaps.md
│   ├── liquidity.md
│   ├── setup-scoring.md
│   └── risk-management.md
├── architecture/
│   ├── system-context.md
│   ├── backend.md
│   ├── frontend.md
│   ├── data-model.md
│   ├── webhook-flow.md
│   └── ml-pipeline.md
├── contracts/
│   ├── tradingview-webhook.md
│   └── setup-event-schema.md
├── learning/
├── decisions/
├── exec-plans/
│   ├── active/
│   └── completed/
└── operations/
    ├── local-development.md
    ├── paper-trading.md
    ├── security.md
    └── troubleshooting.md
```

Használj Mermaid-diagramokat a folyamatok és komponensek bemutatásához.

A dokumentáció legyen a rendszer működésének hiteles forrása. Ha változik a működés, frissítsd a kapcsolódó dokumentumot is.

## 5. Technológiai stack

Alapértelmezett technológiák:

### Backend

* Python 3.12 vagy frissebb stabil verzió;
* FastAPI;
* Pydantic;
* SQLAlchemy 2;
* Alembic;
* PostgreSQL;
* `uv` vagy más egységes, dokumentált Python dependency manager;
* pytest;
* Ruff;
* mypy vagy pyright;
* strukturált logging.

### Frontend

* React;
* Vite;
* TypeScript strict mode;
* TanStack Query;
* React Router;
* Ant Design;
* chart megjelenítéshez egy indokolt és dokumentált könyvtár;
* Vitest;
* React Testing Library;
* Playwright.

### TradingView

* Pine Script v6;
* külön indicator és strategy változat, amennyiben mindkettő indokolt;
* JSON-formátumú alert payload;
* kizárólag megerősített és reprodukálható jelek.

### Adatbázis

* PostgreSQL;
* Alembic migrációk;
* UUID elsődleges kulcsok;
* UTC időbélyegek;
* idempotens webhook-feldolgozás;
* auditálható állapotváltozások.

### Fejlesztői környezet

* Docker Compose;
* `.env.example`;
* Makefile vagy egységes task runner;
* GitHub Actions;
* lokálisan egy paranccsal indítható fejlesztői környezet.

Az MVP legyen moduláris monolit. Ne hozz létre korán indokolatlan microservice-architektúrát.

Az ML-modul kezdetben maradjon ugyanazon Python projekten belül jól elkülönített modul. Csak bizonyított szükség esetén váljon külön szolgáltatássá.

## 6. Javasolt repository-struktúra

Indulj az alábbihoz hasonló szerkezetből, de a repository aktuális állapota alapján indokoltan módosíthatod:

```text
apps/
├── api/
│   ├── src/
│   │   └── smc_assistant/
│   │       ├── api/
│   │       ├── application/
│   │       ├── domain/
│   │       ├── infrastructure/
│   │       ├── analytics/
│   │       └── ml/
│   └── tests/
└── web/
    ├── src/
    └── tests/

tradingview/
├── indicators/
├── strategies/
├── libraries/
└── examples/

infra/
├── docker/
└── github/

scripts/
docs/
```

A backend rétegei:

* `domain`: tiszta üzleti és trading fogalmak;
* `application`: use case-ek és folyamatvezérlés;
* `infrastructure`: adatbázis, külső szolgáltatások és adapterek;
* `api`: HTTP API és webhook;
* `analytics`: statisztikai elemzés;
* `ml`: feature engineering, training és inference.

A domain logika lehetőség szerint ne függjön a FastAPI-tól, SQLAlchemytől vagy külső AI-szolgáltatótól.

## 7. Stratégiai alap

A projekt egy **SMC/ICT-inspired Range–Change–Execution rendszerből** indul ki.

Ne állítsd, hogy ez Craig Percoco teljes vagy hivatalos stratégiájának pontos másolata. A projekt egy formalizált, tesztelhető értelmezést valósít meg.

A stratégia három fő szakasza:

### Range

Magasabb idősíkon meg kell határozni:

* a fontos swing high és swing low pontokat;
* a market structure irányát;
* a dealing range-et;
* a magasabb idősíkú BOS és CHoCH eseményeket;
* az érintetlen FVG-zónákat;
* a fontos likviditási célokat;
* a premium és discount területeket.

### Change

Alacsonyabb idősíkon meg kell keresni:

* a liquidity sweepet;
* az első lehetséges karakterváltást;
* a CHoCH eseményt;
* az erős displacementet;
* az új Fair Value Gap kialakulását.

### Execution

A rendszer belépési tervet készít:

* FVG-visszateszt;
* konfigurálható FVG-belépési szint;
* invalidációs pont;
* stop loss;
* célár;
* várható risk–reward;
* setup pontszám;
* setup elutasításának okai.

## 8. A trading fogalmak formalizálása

Az SMC-fogalmaknak többféle értelmezése létezik. Ezért minden fogalomhoz készíts:

* emberi definíciót;
* algoritmikus definíciót;
* konfigurálható paramétereket;
* bullish példát;
* bearish példát;
* edge case-eket;
* unit teszteket.

Legalább az alábbi fogalmakat kezeld:

### Swing high és swing low

Induló megoldásként használj megerősített pivot logikát konfigurálható bal és jobb oldali gyertyaszámmal.

A pivot csak akkor tekinthető ismertnek, amikor a szükséges jobb oldali gyertyák már lezárultak.

Ne jelenítsd meg úgy a történelmi charton, mintha a pivot már a tényleges pivotgyertyánál ismert lett volna.

### BOS

A Break of Structure alapértelmezésben:

* meglévő struktúra irányába történő;
* megerősített swing szintet áttörő;
* konfigurálható bufferrel rendelkező;
* gyertyazárással megerősített

struktúratörés.

### CHoCH

A Change of Character alapértelmezésben az aktuális struktúrával ellentétes irányú első jelentős megerősített struktúratörés.

Dokumentáld világosan, hogy a CHoCH önmagában nem garantál trendfordulót.

### Fair Value Gap

Háromgyertyás modell:

Bullish FVG lehetséges, amikor az első gyertya high értéke kisebb a harmadik gyertya low értékénél.

Bearish FVG lehetséges, amikor az első gyertya low értéke nagyobb a harmadik gyertya high értékénél.

Legyen konfigurálható:

* minimális abszolút méret;
* minimális tickméret;
* ATR-hez viszonyított minimális méret;
* belépési százalék;
* teljes vagy részleges mitigation;
* maximális életkor;
* első visszateszt követelménye.

### Liquidity sweep

Induló formalizálás:

* az ár kanóccal átlép egy korábbi megerősített swing szintet;
* ugyanaz vagy egy későbbi, szigorúan meghatározott gyertya visszazár a szint mögé;
* opcionálisan szükséges displacement vagy CHoCH megerősítés.

### Displacement

Legyen több komponensből számítható:

* gyertyatest az ATR-hez képest;
* teljes gyertyatartomány az ATR-hez képest;
* body-to-range arány;
* egymást követő irányazonos gyertyák;
* volumeneltérés, ha rendelkezésre áll.

### Risk–reward és R-multiple

Dokumentáld és implementáld:

```text
initialRisk = abs(entryPrice - stopLoss)
plannedReward = abs(takeProfit - entryPrice)
riskReward = plannedReward / initialRisk
realizedR = realizedProfitOrLoss / initialRisk
```

Vegyél figyelembe:

* commissiont;
* slippage-et;
* funding költséget, ha később releváns;
* részleges zárásokat.

## 9. Setup pontozás

Az első működő változat ne gépi tanulást használjon, hanem determinisztikus pontozást.

Példa komponensek:

* magasabb idősíkú bias egyezése;
* liquidity sweep megléte;
* CHoCH minősége;
* displacement erőssége;
* FVG mérete;
* FVG frissessége;
* FVG mitigáltsága;
* session;
* volumen;
* minimum risk–reward;
* közeli ellenoldali likviditás;
* fontos gazdasági esemény jelölése, ha később van adatforrás;
* setupok közötti korreláció;
* piaci rezsim.

A teljes pont legyen 0 és 100 között.

Minden pontszámhoz tartozzon:

* komponensenkénti részpontszám;
* pozitív indokok;
* negatív indokok;
* elutasítási okok;
* használt stratégia-verzió;
* használt konfiguráció-verzió.

A pontozás legyen reprodukálható. Azonos input és azonos konfiguráció azonos eredményt adjon.

## 10. TradingView-integráció

A rendszer ne függjön kizárólag vizuális chartképektől.

Elsőként hozz létre egy saját Pine Script prototípust, amely:

* megerősített swingeket jelöl;
* BOS és CHoCH eseményt jelöl;
* FVG-zónákat kezel;
* liquidity sweepet jelöl;
* displacement értéket számít;
* alert payloadot hoz létre;
* ugyanazt a domainnyelvet használja, mint a backend.

Készíts külön dokumentumot a felhasználó meglévő indikátorainak felmérésére:

`docs/strategy/indicator-inventory.md`

Az inventory tartalmazza indikátoronként:

* név;
* készítő;
* nyílt vagy zárt forrású;
* milyen plotot publikál;
* milyen alertet támogat;
* használható-e `input.source()` kapcsolaton keresztül;
* újra kell-e implementálni a logikáját;
* repaintelhet-e;
* a rendszer mely feature-éhez használható.

Ne próbáld meg megkerülni zárt forrású indikátorok védelmét.

Amíg a konkrét indikátorlista nem ismert, használj saját referencialogikát és mock webhook payloadokat.

A Pine Script:

* ne használjon jövőbeli adatot;
* ne használjon nem megerősített HTF-adatot történelmi eredményként;
* alertet alapértelmezésben lezárt gyertyán küldjön;
* egyértelműen dokumentálja a jel felismerésének tényleges időpontját;
* kerülje a repaintinget;
* tartalmazzon debug megjelenítési módot.

## 11. Webhook contract

Hozz létre verziózott JSON contractot.

Példa:

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
  "direction": "LONG",
  "marketStructure": {
    "htfTimeframe": "15",
    "htfBias": "BULLISH",
    "bos": false,
    "choch": true,
    "liquiditySweep": true
  },
  "fvg": {
    "lower": 65120.0,
    "upper": 65240.0,
    "equilibrium": 65180.0,
    "sizeAtrRatio": 0.42,
    "mitigationPercent": 0.0
  },
  "execution": {
    "entry": 65180.0,
    "stopLoss": 64980.0,
    "takeProfit": 65780.0,
    "riskReward": 3.0
  },
  "features": {
    "atr": 285.0,
    "relativeVolume": 1.7,
    "displacementScore": 0.81,
    "session": "NEW_YORK"
  }
}
```

Követelmények:

* Pydantic validáció;
* JSON Schema;
* OpenAPI-dokumentáció;
* deduplikáció `eventId` alapján;
* nyers payload megőrzése;
* hibás payloadok biztonságos naplózása;
* gyors HTTP-válasz;
* ne történjen hosszú ML-művelet a webhook kérésben;
* feldolgozási állapot legyen követhető.

A webhookban soha ne szerepeljen tőzsdei API-kulcs, jelszó vagy más érzékeny hitelesítő adat.

## 12. Adatmodell

Tervezd meg legalább az alábbi entitásokat:

* `TradingInstrument`;
* `StrategyVersion`;
* `StrategyConfiguration`;
* `WebhookEvent`;
* `MarketStructureEvent`;
* `FairValueGap`;
* `SetupCandidate`;
* `SetupScore`;
* `TradePlan`;
* `SimulatedTrade`;
* `TradeExecution`;
* `TradeOutcome`;
* `FeatureSnapshot`;
* `ModelVersion`;
* `ModelPrediction`;
* `JournalEntry`;
* `AuditEvent`.

Fontos követelmények:

* minden döntés visszavezethető legyen az inputadatokra;
* a történelmi score ne változzon meg egy új konfiguráció miatt;
* a strategy és model verzió mindig legyen eltárolva;
* egy setup újrapontozható legyen új modellverzióval;
* a régi predikciók maradjanak meg;
* minden időpont UTC-ben legyen tárolva;
* a frontend jelenítse meg a felhasználó helyi időzónájában.

Készíts ER-diagramot.

## 13. Market data és backtest

Első adatforrásként implementálj OHLCV CSV-importot.

Ne scrape-elj TradingView-adatot.

Hozz létre `MarketDataProvider` interfészt, amely mögé később több adapter illeszthető:

* CSV;
* nyilvános exchange API;
* lokálisan tárolt parquet;
* későbbi fizetős adatforrás.

A backtest motor:

* időrendben dolgozzon;
* egyetlen ponton se használjon jövőbeli adatot;
* kezelje a stop és célár sorrendjének bizonytalanságát egy gyertyán belül;
* legyen konfigurálható konzervatív fill policy;
* számoljon commissionnel és slippage-dzsel;
* rögzítse a kihagyott setupokat is;
* tárolja az MFE és MAE értékeket;
* különítse el az in-sample és out-of-sample időszakot;
* támogasson walk-forward tesztet.

Készíts legalább egy szintetikus OHLCV adatsort, amelyen determinisztikusan tesztelhetők:

* bullish BOS;
* bearish BOS;
* CHoCH;
* bullish FVG;
* bearish FVG;
* liquidity sweep;
* stop loss;
* take profit;
* timeout.

## 14. Outcome engine

A rendszer képes legyen egy setup eredményének automatikus megállapítására.

Induló címkék:

* `WIN`;
* `LOSS`;
* `BREAK_EVEN`;
* `TIMEOUT`;
* `CANCELLED`;
* `INVALIDATED`;
* `NOT_TRIGGERED`.

Támogass egy konfigurálható triple-barrier jellegű megközelítést:

* felső barrier: célár;
* alsó barrier: stop;
* időbeli barrier: maximális barszám vagy időtartam.

Dokumentáld, hogy ez hogyan lesz később a supervised learning célváltozója.

## 15. Automatikus trading journal

Minden setuphoz tárold:

* a jel létrejöttének idejét;
* instrumentumot;
* timeframe-et;
* directiont;
* trading sessiont;
* market structure állapotot;
* FVG-adatokat;
* liquidity sweepet;
* displacementet;
* score-t;
* belépési tervet;
* tényleges vagy szimulált eredményt;
* realized R-t;
* MFE-t;
* MAE-t;
* felhasználói megjegyzést;
* screenshot URL vagy fájlhivatkozás opcionális helyét;
* manuális felülbírálást;
* felülbírálás indokát.

A journalből legyenek számíthatók:

* win rate;
* average win R;
* average loss R;
* expectancy;
* profit factor;
* maximum drawdown;
* longest losing streak;
* session szerinti eredmény;
* instrumentum szerinti eredmény;
* setup-komponens szerinti eredmény;
* score-bucket szerinti eredmény;
* long és short eredmény külön;
* strategy version szerinti eredmény.

## 16. Gépi tanulási követelmények

Ne kezdj neurális hálóval vagy reinforcement learninggel.

Az ML-fejlesztés sorrendje:

1. Determinisztikus rule score.
2. Megbízható outcome labeling.
3. Tiszta és auditálható dataset.
4. Egyszerű baseline modell.
5. Időalapú validáció.
6. Kalibráció.
7. Összetettebb modell csak akkor, ha igazolhatóan jobb.

Első baseline modellek:

* dummy classifier;
* logisztikus regresszió;
* döntési fa vagy Random Forest;
* gradient boosting csak későbbi összehasonlításként.

Az ML target első verziója például:

```text
1 = a setup a meghatározott időablakon belül előbb érte el a take profitot, mint a stop losst
0 = előbb érte el a stop losst, vagy a konfiguráció szerint sikertelen lett
```

Később támogatható többosztályos target is.

Kötelező ML-védelem:

* semmilyen jövőbeli feature nem kerülhet a tanítási adatokba;
* ne legyen véletlen train-test split idősoros adaton;
* használj időrendi vagy walk-forward splitet;
* a scaler és feature engineering csak a training adaton tanuljon;
* ne optimalizáld a test set alapján a paramétereket;
* a tesztidőszak maradjon érintetlen a végső kiértékelésig;
* legyen összehasonlítás a rule score és az ML között;
* kis dataset esetén a rendszer figyelmeztessen, és ne mutasson hamis bizonyosságot;
* tárold a modell feature-listáját, paramétereit és training időszakát;
* a modellek legyenek reprodukálhatók random seed és konfiguráció alapján.

Mérőszámok:

* ROC AUC csak kiegészítőként;
* precision;
* recall;
* F1;
* Brier score;
* kalibrációs görbe;
* top-score setupok precision értéke;
* expectancy score bucketenként;
* profit factor;
* maximum drawdown;
* commission és slippage utáni eredmény.

A valós üzleti kérdés ne az legyen, hogy „mennyire pontos a modell?”, hanem:

> Az ML-szűrő javítja-e a korábban definiált stratégia out-of-sample expectancyjét és kockázati mutatóit?

## 17. AI/LLM magyarázati réteg

Az LLM ne döntsön közvetlenül a belépésről, és ne módosíthassa a determinisztikus kockázati limiteket.

Feladata:

* strukturált setup természetes nyelvű magyarázata;
* pontszám komponenseinek összefoglalása;
* journal heti összefoglalása;
* ismétlődő hibák kiemelése;
* hasonló korábbi setupok bemutatása;
* tanulási segítség.

Az LLM bemenete strukturált legyen. Ne kapjon korlátlanul nyers külső szöveget vagy titkos adatot.

Legyen szolgáltatófüggetlen interfész:

* `ExplanationProvider`;
* determinisztikus template-alapú fallback;
* opcionális OpenAI adapter;
* fake provider tesztekhez.

Az alkalmazás LLM nélkül is legyen teljesen használható.

A setup számszerű score-ja ne az LLM válaszából származzon.

## 18. Kockázati korlátok

Az első kiadás kizárólag:

* elemzés;
* alert-fogadás;
* backtest;
* journal;
* paper trading;
* manuális jóváhagyásra előkészített trade plan

funkciókat tartalmazzon.

Ne implementálj automatikus valódi tőzsdei order executiont addig, amíg a felhasználó ezt külön, egyértelműen nem kéri.

Készíts determinisztikus risk policy modult, amely később is független marad az ML-től.

Alapvető konfigurálható szabályok:

* maximum risk per trade;
* maximum napi veszteség;
* maximum egymást követő veszteség;
* minimum risk–reward;
* maximum egyidejű pozíció;
* korrelált instrumentumok kezelése;
* cooldown;
* setup score minimum;
* kereskedési session korlátozása.

Az AI soha ne léphesse át ezeket a limiteket.

## 19. Frontend dashboard

Készíts áttekinthető webes felületet legalább az alábbi oldalakkal:

### Dashboard

* legfontosabb teljesítménymutatók;
* aktuális setupok;
* score eloszlás;
* equity curve paper trading alapján;
* drawdown;
* legutóbbi események.

### Setup lista

* szűrés instrumentumra;
* timeframe-re;
* directionre;
* outcome-ra;
* sessionre;
* score tartományra;
* strategy versionre;
* dátumra.

### Setup részletező

* eredeti webhook;
* market structure;
* FVG;
* liquidity sweep;
* displacement;
* részpontszámok;
* teljes score;
* rule explanation;
* opcionális AI explanation;
* trade plan;
* outcome;
* MFE/MAE;
* audit trail.

### Journal

* setupok és trade-ek;
* saját jegyzet;
* manuális értékelés;
* „megkötöttem / kihagytam” jelölés;
* manuális döntés és rendszerjavaslat összehasonlítása.

### Analytics

* expectancy;
* win rate;
* profit factor;
* drawdown;
* session bontás;
* instrumentum bontás;
* setup feature bontás;
* score bucket bontás;
* strategy version összehasonlítás;
* rule score kontra ML score.

### Strategy settings

* csak verziózott konfiguráció;
* régi eredmények ne íródjanak felül;
* változtatás előtt mutasd meg, mi változik;
* legyen audit trail.

A felület elsődlegesen desktop használatra készüljön, de legyen reszponzív.

## 20. API-k

Induló endpointok:

```text
GET  /health
GET  /ready

POST /api/v1/webhooks/tradingview

GET  /api/v1/setups
GET  /api/v1/setups/{id}
POST /api/v1/setups/{id}/rescore
POST /api/v1/setups/{id}/journal

GET  /api/v1/trades
GET  /api/v1/analytics/summary
GET  /api/v1/analytics/by-session
GET  /api/v1/analytics/by-score-bucket

POST /api/v1/backtests
GET  /api/v1/backtests/{id}

POST /api/v1/ml/datasets
POST /api/v1/ml/train
GET  /api/v1/ml/models
POST /api/v1/ml/models/{id}/evaluate
```

Ne készítsd el az összes endpointot egyszerre. Fázisonként csak az aktuálisan szükségeseket implementáld.

## 21. Tesztelés

Minden domainfogalomhoz legyen unit teszt.

Kötelező tesztszintek:

* domain unit tests;
* application service tests;
* repository integration tests PostgreSQL-lel;
* API tests;
* webhook contract tests;
* migration tests;
* frontend component tests;
* frontend API integration tests;
* minimum egy Playwright happy path;
* Pine Script manuális tesztleírás;
* backtest determinisztikus tesztek;
* ML leakage tesztek;
* ML reproducibility tesztek.

Különösen teszteld:

* duplikált webhook;
* sorrenden kívül érkező esemény;
* hibás timeframe;
* stop és take profit ugyanazon gyertyán;
* hiányos volumenadat;
* nulla vagy negatív risk;
* invalid entry/stop/target sorrend;
* FVG teljes mitigation;
* FVG részleges mitigation;
* későn megerősített pivot;
* HTF-adat időzítése;
* setup újrapontozása;
* régi strategy version megőrzése.

## 22. Minőségkapuk

Egy mérföldkő csak akkor kész, ha:

* a kód formázott;
* lint sikeres;
* type check sikeres;
* unit tesztek sikeresek;
* integrációs tesztek sikeresek, ahol releváns;
* migráció létrejött, ha szükséges;
* dokumentáció frissült;
* nincs véletlenül commitolt secret;
* nincs nyilvánvaló future leakage;
* nincs indokolatlan TODO a kritikus útvonalon;
* a README alapján egy új fejlesztő el tudja indítani.

Ne rejts el hibákat általános exception handlinggel. A hibák legyenek konkrétak és diagnosztizálhatók.

## 23. Git és változtatások kezelése

Dolgozz kis, áttekinthető változtatásokban.

Ha a környezet engedi és a Git megfelelően konfigurált:

* készíts logikus, atomi commitokat;
* használj beszédes angol commit message-eket;
* ne módosíts egyszerre egymástól független területeket;
* minden commit legyen tesztelhető állapotban.

Ne force pusholj.

Ne módosíts vagy törölj felhasználói kódot indoklás nélkül.

Minden jelentős architekturális döntéshez hozz létre ADR-t:

`docs/decisions/ADR-XXXX-<decision>.md`

## 24. Fejlesztési fázisok

### Phase 0 – Discovery és bootstrap

* repository felmérése;
* AGENTS.md;
* ExecPlan;
* dokumentációs váz;
* stack véglegesítése;
* Docker Compose;
* backend és frontend skeleton;
* CI;
* hello-world health check;
* első learning dokumentum.

### Phase 1 – Domain modell

* trading glossary;
* strategy specification;
* swing, BOS, CHoCH, FVG, sweep és displacement modellek;
* tiszta domain implementáció;
* unit tesztek;
* szintetikus példák.

### Phase 2 – Webhook ingestion

* verziózott contract;
* webhook endpoint;
* validáció;
* idempotencia;
* PostgreSQL persistence;
* audit;
* mock TradingView payload;
* integrációs tesztek.

### Phase 3 – Pine Script prototype

* swingek;
* BOS;
* CHoCH;
* FVG;
* liquidity sweep;
* displacement;
* alert JSON;
* debug mód;
* non-repainting dokumentáció;
* manuális TradingView tesztleírás.

### Phase 4 – Rule-based setup scoring

* részpontszámok;
* score 0–100;
* elutasítási szabályok;
* strategy configuration versioning;
* explanation;
* tesztek.

### Phase 5 – Outcome és backtest

* OHLCV import;
* market data abstraction;
* trade simulation;
* triple barrier;
* commission;
* slippage;
* MFE;
* MAE;
* analytics.

### Phase 6 – Frontend és journal

* dashboard;
* setup lista;
* setup részletező;
* journal;
* analytics;
* frontend tesztek.

### Phase 7 – Paper trading workflow

* élő TradingView webhook;
* automatikus outcome frissítés;
* értesítési adapter;
* napi és heti összesítő;
* operational dokumentáció.

### Phase 8 – ML dataset és baseline

* feature schema;
* dataset builder;
* leakage audit;
* időalapú split;
* dummy baseline;
* logisztikus regresszió;
* kiértékelés;
* model versioning.

### Phase 9 – ML setup filter

* rule score kontra ML összehasonlítás;
* kalibrált valószínűség;
* score threshold elemzés;
* walk-forward evaluation;
* magyarázhatóság;
* shadow mode inference.

### Phase 10 – AI explanation

* provider abstraction;
* template fallback;
* opcionális LLM adapter;
* setup magyarázat;
* heti journal elemzés;
* biztonsági kontrollok.

### Phase 11 – Hardening

* security review;
* observability;
* backup és restore dokumentáció;
* performance tesztek;
* end-to-end teszt;
* deployment dokumentáció;
* végső architecture review.

Ne ugorj közvetlenül ML-re a megbízható adatgyűjtés és labeling elkészülte előtt.

## 25. Első végrehajtási feladat

Most hajtsd végre a következőket:

1. Vizsgáld meg a repositoryt.
2. Készíts rövid összefoglalót a jelenlegi állapotról.
3. Hozd létre vagy frissítsd az `AGENTS.md` fájlt.
4. Hozd létre a dokumentációs könyvtárstruktúrát.
5. Hozd létre a `docs/PLANS.md` fájlt.
6. Hozd létre a teljes projekt aktív ExecPlanjét.
7. Hozd létre a Phase 0 részletes mérföldköveit.
8. Scaffoldold a backendet és a frontendet.
9. Készíts Docker Compose konfigurációt PostgreSQL-lel.
10. Készíts `.env.example` fájlt valódi secret nélkül.
11. Implementálj backend health endpointot.
12. Implementálj egy minimális frontend státuszoldalt, amely megjeleníti a backend állapotát.
13. Állítsd be a lintet, type checket és teszteket.
14. Készíts GitHub Actions workflow-t.
15. Futtasd a releváns ellenőrzéseket.
16. Frissítsd az ExecPlant a tényleges eredmények alapján.
17. Készíts magyar nyelvű `docs/learning/phase-00-bootstrap.md` dokumentumot.
18. Ezután, amennyiben nincs külső akadály, folytasd a Phase 1 első mérföldkövével.

## 26. Minden munkamenet végi beszámoló

Minden befejezett munkamenet végén ebben a formában számolj be:

### Elkészült

Konkrétan mely funkciók és fájlok készültek el?

### Hogyan működik?

Magyarul magyarázd el a háttérlogikát.

### Trading fogalmak

Milyen trading fogalmak kerültek elő, és pontosan mit jelentenek?

### Technikai fogalmak

Milyen új szoftveres, adatbázisos vagy AI-fogalmak kerültek elő?

### Ellenőrzés

Milyen parancsokat futtattál, és mi lett az eredményük?

### Manuális kipróbálás

Pontosan milyen parancsokkal és lépésekkel tudom kipróbálni?

### Fontos fájlok

Mely fájlokat olvassam el a megértéshez?

### Döntések és feltételezések

Milyen döntéseket vagy alapértelmezéseket alkalmaztál?

### Kockázatok és nyitott kérdések

Mi nincs még kész, és mi lehet problémás?

### Következő mérföldkő

Mi az aktív ExecPlan következő konkrét feladata?

## 27. Alapelvek

Mindig tartsd be:

* Először mérhető stratégia, utána AI.
* Először paper trading, utána esetleges valódi végrehajtás.
* Először egyszerű baseline, utána összetett modell.
* Ne keverd össze a jó backtestet a bizonyított jövőbeli profitabilitással.
* Ne használj jövőbeli adatot.
* Ne engedj repaintelő logikát dokumentálatlanul.
* Ne optimalizálj a test setre.
* Ne használj LLM-et determinisztikus számítás helyett.
* Minden score legyen magyarázható.
* Minden eredmény legyen visszavezethető.
* Minden fontos döntés legyen verziózott.
* Minden kritikus logikához készüljön teszt.
* Minden fejlesztési fázis tanítsa is a repository tulajdonosát.

Kezdd el most a repository felmérésével és a Phase 0 végrehajtásával.
