# Frontend

A frontend React, Vite és TypeScript strict mode alapú. Az adatlekérést és a
mutation utáni cache-frissítést TanStack Query, a működési felület elemeit Ant
Design biztosítja. Az ikonok a Lucide készletből érkeznek.
Az Ant Design 5 React 19 kompatibilitási csomagja az alkalmazás belépési
pontján töltődik be; a későbbi Ant Design 6 migráció ezt szükségtelenné teszi.

Az aktuális dashboard öt munkaterületből áll:

- backend kapcsolat és verzió;
- pontozott setup lista, szűrés és részletező drawer;
- paper trading létrehozó, pozíciólista és execution drawer;
- backtest futáslista, összesítő mutatók, outcome lista és részletező drawer;
- döntési journal lista, létrehozó/szerkesztő modal és revíziótörténetes drawer.

Az új backtest modal szerkeszthető szintetikus setup JSON-nal és OHLCV CSV-vel
indul. A kliens a `POST /api/v1/backtests` végpontot hívja, majd siker esetén
érvényteleníti a futás- és outcome-cache-t. A futásazonosítót a böngésző UUID-ként
generálja; az API idempotencia- és ütközési szabályai maradnak a hiteles védelem.

A táblák kis képernyőn a saját keretükben vízszintesen görgethetők. A fő flex
tartalom és panelek `min-width: 0` beállítása megakadályozza, hogy a táblák
minimális szélessége az egész oldalt széthúzza.

A journal csak olyan setupot kínál fel új bejegyzéshez, amelyhez még nincs
napló. Létrehozás és szerkesztés után a TanStack Query frissíti a listát, a
részletezőt és a revíziókat. A mobil drawer legfeljebb a viewport szélessége.

A kiválasztott backtest futás alatt a teljesítményelemzés külön Query cache-t
használ. Reszponzív SVG equity curve, stabil KPI-rács és tabokra bontott táblák
mutatják a kockázatot és a csoportokat. Backtest vagy journal mutation után az
érintett analytics cache érvénytelenedik.

A paper trading panel az elfogadott, még nem használt setupokat kínálja fel. A
mutationök után a trade- és eseménycache frissül; a részletező csak az aktuális
állapotban engedélyezett árfrissítés, manuális zárás vagy visszavonás műveletet
mutatja. A trade lista és a megnyitott execution log öt másodpercenként frissül,
így az élő webhook állapotváltozásai automatikusan megjelennek. Széles listák
mobilon lokálisan görgethetők.

Következő frontend területek: összesítők és strategy settings.
