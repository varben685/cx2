# Webhook flow

```mermaid
sequenceDiagram
    participant TV as TradingView
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Live as Live orchestration
    participant Paper as Paper trading service

    TV->>API: POST /api/v1/webhooks/tradingview
    API->>API: Pydantic validation
    API->>DB: payload + globálisan egyedi eventId
    alt SETUP_CANDIDATE
        API->>Live: score és setup mentés
        Live->>Paper: risk gate és PENDING létrehozás
    else MARKET_PRICE
        API->>Live: idempotencia ellenőrzés
        Live->>Paper: egyező aktív trade-ek frissítése
    end
    Paper->>DB: snapshot + append-only event
    API-->>TV: gyors 202 válasz feldolgozási összesítővel
```

A webhook kérésben nincs ML vagy külső market-data hívás. Az aktuális szinkron
út csak lokális validációt, pontozást, risk policyt és adatbázis-műveleteket
végez. Nagy terheléshez később queue/outbox worker szükséges.
