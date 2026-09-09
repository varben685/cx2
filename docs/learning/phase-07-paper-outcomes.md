# Phase 07: live paper outcome és értesítés

## Mi készült el?

A paper trade terminális állapotát a rendszer automatikusan átfordítja a már
meglévő outcome modellre. A céláras, stopos és manuális zárás `WIN`, `LOSS`
vagy `BREAK_EVEN`, a pending visszavonás `CANCELLED` eredményt ad.

Az eredmény mentése idempotens: ugyanannak a setup eseménynek ugyanazon a live
runon csak egy outcome-ja lehet. A reconcile ezért biztonságosan többször is
futtatható. Ha a journal már létezik, új revízió készül az outcome adataival;
a felhasználói jegyzetek és címkék változatlanok maradnak.

## Miért adapter az értesítés?

Az alkalmazási réteg csak a `NotificationAdapter` portot ismeri. A jelenlegi
`LoggingNotificationAdapter` strukturált eseményt ír, később ugyanide köthető
email, Telegram vagy más csatorna anélkül, hogy a paper trade állapotgépet át
kellene írni. A `none` adapter fejlesztési és tesztelési kikapcsolást ad.

## Fontos korlátok

- A mentés és az értesítés nem egy tranzakció; az értesítés best effort.
- Nincs outbox, retry vagy kézbesítési státusz.
- A live MFE/MAE csak a megfigyelt close price pontokat látja.
- A költségmodell egyelőre nulla commissiont és slippage-et használ.

## Következő lépés

A helyi API publikus, hitelesített webhook URL-en keresztüli összekötése a
TradingView alerttel, majd valós alert payload ellenőrzése paper módban.
