# Frontend

A frontend React, Vite és TypeScript strict mode alapú. Az adatlekérést és a
mutation utáni cache-frissítést TanStack Query, a működési felület elemeit Ant
Design biztosítja. Az ikonok a Lucide készletből érkeznek.
Az Ant Design 5 React 19 kompatibilitási csomagja az alkalmazás belépési
pontján töltődik be; a későbbi Ant Design 6 migráció ezt szükségtelenné teszi.

Az aktuális dashboard három munkaterületből áll:

- backend kapcsolat és verzió;
- pontozott setup lista, szűrés és részletező drawer;
- backtest futáslista, összesítő mutatók, outcome lista és részletező drawer.

Az új backtest modal szerkeszthető szintetikus setup JSON-nal és OHLCV CSV-vel
indul. A kliens a `POST /api/v1/backtests` végpontot hívja, majd siker esetén
érvényteleníti a futás- és outcome-cache-t. A futásazonosítót a böngésző UUID-ként
generálja; az API idempotencia- és ütközési szabályai maradnak a hiteles védelem.

A táblák kis képernyőn a saját keretükben vízszintesen görgethetők. A fő flex
tartalom és panelek `min-width: 0` beállítása megakadályozza, hogy a táblák
minimális szélessége az egész oldalt széthúzza.

Következő frontend területek: journal, bővebb analytics és strategy settings.
