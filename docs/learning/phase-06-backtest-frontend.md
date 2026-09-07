# Phase 06: Backtest frontend

## 1. Mit építettünk?

A dashboard mentett backtest futásokat és outcome-okat olvas, összesítő
mutatókat jelenít meg, részleteket nyit meg, és új szinkron backtestet indít
szerkeszthető setup JSON-ból és OHLCV CSV-ből.

## 2. Miért ezt építettük?

A Phase 5 API eddig csak HTTP kliensből volt használható. Ez a felület az első
teljes felhasználói folyamat ugyanarra a verziózott, mentett eredményre építve.

## 3. Hogyan működik?

TanStack Query lekéri a futáslistát. A kiválasztott `runId` alapján betölti az
outcome-okat. A mutation elküldi a batch inputot, majd siker után frissíti a
kapcsolódó cache-eket és az új futást választja ki.

## 4. Megvizsgált alternatívák

Felmerült a fájlfeltöltés, a külön route-ok és az automatikus setupdetektálás.
Az első szelet szövegmezőket használ, mert az API jelenlegi contractja is JSON
és CSV szöveget fogad, így új backend absztrakció nélkül végigtesztelhető.

## 5. Miért ezt választottuk?

A beépített szintetikus példa egy kattintással kipróbálható, ugyanakkor minden
input szerkeszthető. Ez kis lépésben használhatóvá teszi a meglévő API-t, és
megőrzi a későbbi fájlfeltöltés lehetőségét.

## 6. Trading fogalmak

- `Net R`: a kockázati egységben mért eredmény költségek után.
- `Expectancy`: átlagos nettó R lezárt trade-enként.
- `Profit factor`: pozitív nettó R összege osztva a veszteségek abszolút
  összegével.
- `MFE/MAE`: a pozíció legnagyobb kedvező és kedvezőtlen kitérése.

## 7. Hibák és félreértések

A mobilnézet első változatát a táblák minimális szélessége 961 px-re húzta.
A táblák már rendelkeztek belső görgetéssel, de a flex tartalom nem tudott
zsugorodni. A `min-width: 0` beállítás a megfelelő konténereken oldotta meg.
Az élő böngészős próba az Ant Design 5 React 19 figyelmeztetését is felszínre
hozta; a könyvtár hivatalos kompatibilitási csomagja az entrypointban fut.

## 8. Fontos fájlok

- `apps/web/src/BacktestsPanel.tsx`: teljes backtest felhasználói folyamat.
- `apps/web/src/backtestExample.ts`: szerkeszthető szintetikus minta.
- `apps/web/src/api.ts`: frontend API contractok és hívások.
- `apps/web/src/BacktestsPanel.test.tsx`: adat-, mutation- és hibaállapotok.

## 9. Manuális kipróbálás

Futó Docker szolgáltatások mellett nyisd meg a `http://localhost:5173` oldalt,
görgess a Backtest futások részhez, válaszd az `Új backtest` gombot, majd indítsd
el az alapmintát. A sikeres futás megjelenik a listában, az outcome sor pedig
részletező panelt nyit.

## 10. Gyakorlófeladat

Állítsd a commission és slippage mezőket nullára, generálj új Run ID-t, majd
hasonlítsd össze a nettó R eredményt az alapminta `1.937R` értékével. Gondold
végig, miért marad a bruttó outcome ugyanaz, miközben a nettó eredmény változik.
