# ADR-0007: Idempotent live paper webhooks

## Status

Accepted, 2026-09-09.

## Context

A TradingView ugyanazt az alertet hálózati retry miatt többször is elküldheti.
A setup és az árfrissítés egyaránt állapotváltozást okozhat, ezért a duplikált
kérés nem hozhat létre második trade-et és nem növelheti újra a revisiont.

## Decision

A közös webhook végpont `eventType` diszkriminátorral fogad
`SETUP_CANDIDATE` és `MARKET_PRICE` payloadot. Az `eventId` globálisan egyedi,
és mindkét típus a `webhook_events` repository `save_if_absent` műveletét
használja. Market price csak első mentéskor frissít trade-et. Régi, duplikált
setup új trade-et nem indít.

Az automatikus trade-létrehozás konfigurálható, de mindig a backend risk
policyján halad át. A market price symbol, exchange és timeframe együttessel
illeszkedik az aktív trade-ekhez.

## Consequences

- A webhook retry mellékhatás szempontjából idempotens.
- Egy event ID nem használható két eseménytípushoz; ütközéskor `409` jár.
- A szinkron feldolgozás egyszerű és gyors a jelenlegi kis terhelésen.
- A market event mentése és a több trade frissítése még nem egy tranzakció.
  Production retryhoz outbox/worker és feldolgozási státusz szükséges.
