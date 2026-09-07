# Phase 06: Verziózott trading journal

## 1. Elkészült

A setupból egy szerkeszthető döntési napló hozható létre. A backend memória és
PostgreSQL repositoryt, REST végpontokat, snapshotokat és revíziótörténetet ad;
a dashboard listáz, létrehoz, részletez és szerkeszt.

## 2. Hogyan működik?

A felhasználó kiválaszt egy még nem naplózott setupot. A szerver ellenőrzi a
setupot és annak eredeti webhookját, majd opcionálisan kapcsolja a legfrissebb
azonos eseményhez tartozó outcome-ot. Ezután immutable piaci kontextust és
szerkeszthető döntési mezőket ment. Frissítéskor az aktuális revízió szükséges,
így egy régi böngészőlap nem írhatja felül csendben az újabb adatot.

## 3. Trading fogalmak

- `TAKEN`: a setup alapján a kötést végrehajtottuk.
- `SKIPPED`: a setup megjelent, de tudatosan kihagytuk.
- `Manual override`: a végső döntés eltért a rendszer javaslatától.
- `MFE/MAE`: a kötés legnagyobb kedvező és kedvezőtlen kitérése R-ben.
- `Net R`: költségek utáni realizált eredmény az induló kockázat arányában.

## 4. Technikai fogalmak

- `Snapshot`: az adat történeti másolata, amelyet a forrás későbbi változása
  nem módosít.
- `Optimistic locking`: frissítés csak az elvárt aktuális verzióval lehetséges.
- `Append-only revision`: minden mentés új történeti rekord, a régi érintetlen.
- `Foreign key`: adatbázis-kapcsolat, amely megakadályozza az árva journal sort.

## 5. Ellenőrzés

A domain, HTTP API, memória-, SQLite- és PostgreSQL repository teszteken futott.
A frontend lista, részletező, létrehozás és revíziózott szerkesztés tesztelt.
Valós Docker API/PostgreSQL smoke során a setup, backtest, automatikus outcome
kapcsolás, journal létrehozás, frissítés és két revízió visszaolvasása sikerült.

## 6. Manuális kipróbálás

Nyisd meg a `http://localhost:5173` oldalt, és görgess a `Döntési napló`
részhez. Az `Új bejegyzés` gombbal válassz setupot, töltsd ki a döntést és a
megjegyzést, majd ments. A szem ikonnal nyisd meg a részleteket, a
`Szerkesztés` gombbal pedig hozz létre új revíziót.

## 7. Fontos fájlok

- `application/journal.py`: use case, snapshot és outcome-kapcsolás.
- `infrastructure/sql_journal.py`: tranzakció és revíziótárolás.
- `api/journal.py`: REST contract és hibakódok.
- `JournalPanel.tsx`: teljes journal felhasználói folyamat.
- `docs/contracts/journal.md`: végpontok és validációs szabályok.

## 8. Döntések és feltételezések

Egy setup egy döntési egység, ezért egyetlen journal tartozik hozzá. A kapcsolt
outcome létrehozáskor rögzül; nem változik meg attól, hogy ugyanahhoz az
eseményhez később új backtest készül. A lista a legutóbb frissített bejegyzést
mutatja először.

## 9. Kockázatok és nyitott kérdések

A teljes kontextus minden revízióban ismétlődik, ami hosszú távon tárhelyet
igényel. Még nincs törlés, valódi képfeltöltés, lapozás, felhasználói jogosultság
vagy Alembic migráció. Az automatikus outcome-kapcsolás csak már létező
eredményt talál meg.

## 10. Következő mérföldkő

A journalra és outcome-okra épülő analytics: equity curve, drawdown, sorozatok,
session/instrumentum bontás és a manuális döntések összehasonlítása a rendszer
javaslataival.
