# ADR-0008: Live paper outcome-ok és best-effort értesítés

## Állapot

Elfogadva, 2026-09-09.

## Kontextus

A paper trade állapotgép már auditálhatóan lezárja vagy visszavonja az
ügyleteket, de ezek eddig nem kerültek be a közös outcome és journal
folyamatba. A backtest outcome modell run azonosítót követel, az első
értesítési cél pedig még nem külső szolgáltatás, hanem üzemeltetési napló.

## Döntés

- Minden `CLOSED` és `CANCELLED` paper trade automatikusan `OutcomeRecord` lesz.
- A live paper eredmények stabil, fenntartott run azonosítót használnak:
  `00000000-0000-0000-0000-000000000007`.
- Az idempotencia kulcsa továbbra is a run és a TradingView `eventId` párja.
- A provenance hash az append-only paper execution eventekből készül.
- A már létező journal új revízióval kapja meg az outcome snapshotot.
- Az értesítési port cserélhető; az első adapter strukturált logbejegyzést ír.
- Értesítési hiba nem fordítja vissza a sikeres trade- és outcome-mentést, hanem
  külön audit eseményt eredményez.
- A reconcile végpont pótolja a részleges hiba miatt hiányzó outcome rekordot.

## Következmények

A backtest és live eredmények ugyanazzal az analytics-kompatibilis modellel
vizsgálhatók, mégsem keverednek egy futásba. A mostani értesítés best effort:
külső csatorna előtt tartós outbox és retry mechanizmus szükséges. A live
MFE/MAE pontosságát a TradingView price eventek sűrűsége korlátozza.
