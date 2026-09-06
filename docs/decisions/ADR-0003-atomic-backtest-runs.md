# ADR-0003: Korlátozott, atomikusan mentett backtest futások

## Státusz

Elfogadva, 2026-09-07.

## Kontextus

A korábbi application függvény egyenként mentette az outcome-okat, nem
nyilvántartott batch-futásként. HTTP-n keresztül fontos megkülönböztetni a
teljes futást a hiányos eredménysortól, és megőrizni a pontos bemenetet.

## Döntés

- Az első POST szinkron, legfeljebb 25 setupot és 1 millió karakter CSV-t fogad.
- Egy futás instrumentuma, exchange-e, timeframe-je, stratégiája és outcome
  konfigurációja egységes. A setupok mind kiértékelődnek, acceptance szűrés nélkül.
- A CSV-t szövegként fogadjuk és memóriából olvassuk. Szerverútvonal nem input.
- Minden eredményt előbb kiértékelünk, majd a teljes futást és outcome sorokat
  egy SQL tranzakcióban mentjük. Memory módban a batch írását lock védi.
- A `backtest_runs` snapshot tartalmazza a teljes validált inputot, a nyers
  CSV-t, a request fingerprintet, időpontokat és a kész outcome-okat.
- A külön `outcome_records` sorok a meglévő analytics és outcome API számára
  ugyanabban a tranzakcióban jönnek létre. Ez szándékos snapshot-duplikáció.
- A kliens adja a runId-t. Azonos azonosító és fingerprint esetén a régi
  eredményt adjuk vissza, eltérő kérés esetén 409 a válasz.
- Csak teljes, `COMPLETED` futás van a nyilvántartásban. Nincs egyelőre
  tartós RUNNING/FAILED állapot vagy háttér-worker.

## Alternatívák és következmények

Egy háttér-worker nagyobb futásokat és állapotkövetést tenne lehetővé, de
most queue-t, retry-szabályokat és recovery folyamatot igényelne. Az első
korlátozott API így egyszerűen végigtesztelhető. Timeout vagy megszakadt
HTTP-kapcsolat után ugyanaz a kérés azonos runId-val megismételhető.

A bemenetek és a kimenetek tárolása több helyet foglal. Cserébe az új HTTP
futásokhoz megmarad a forrás CSV is; a korábbi közvetlen outcome rekordokhoz
továbbra is külső forrásmegőrzés kell. Az inputhoz és snapshothoz később
retention és séma-verziózási szabály szükséges.

Az új tábla a meglévő `create_all` indulási útvonalon jön létre. Alembic még
nyitott feladat. A régi outcome-ok megtartása miatt nincs kötelező foreign key
a korábban is létező outcome_records.run_id mezőről az új táblára. A közvetlen
Python mentési függvény használója ne egészítsen ki már lezárt HTTP-futást.
