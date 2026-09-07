# ADR-0004: Setuphoz kötött, verziózott journal snapshotok

## Státusz

Elfogadva, 2026-09-08.

## Kontextus

A journalnak vissza kell adnia, hogy a döntés pillanatában mit látott a
rendszer és a felhasználó. A setup, a pontozási szabály vagy az outcome később
változhat, miközben a felhasználói jegyzetet és értékelést szerkeszteni kell.
Párhuzamos böngészőlapok esetén egy régi mentés nem írhatja felül észrevétlenül
az újabbat.

## Döntés

- Egy setuphoz legfeljebb egy journal tartozik.
- Létrehozáskor a teljes setup, forrás webhook és kapcsolt outcome snapshotként
  bekerül a journalba.
- Az aktuális állapot a `journal_entries` táblában marad a gyors listázáshoz.
- Minden mentett állapot külön sor a `journal_entry_revisions` táblában; a
  régi verziókat nem módosítjuk.
- Frissítéskor kötelező az optimista zárolásra használt `expectedRevision`.
- PostgreSQL alatt sorzár és közös tranzakció védi az aktuális állapot és az
  új revízió együtt írását.
- Outcome megadása nélkül a legfrissebb, azonos eventId-jú eredmény kapcsolódik.
  A kapcsolat későbbi outcome létrejöttekor nem változik automatikusan.

## Következmények

A döntési kontextus reprodukálható és a szerkesztési történet auditálható.
Cserébe a snapshotok minden revízióban ismétlődnek, ezért később retention,
tömörítés vagy külön immutable/mutable adattárolás válhat szükségessé.

Az első verzióban nincs journal törlés és nincs későbbi outcome újrakapcsolás.
A séma továbbra is `metadata.create_all` útvonalon készül; éles migrációhoz
Alembic szükséges.
