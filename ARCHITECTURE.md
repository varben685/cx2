# Architektúra

Az MVP moduláris monolitként indul. A backend egy Python/FastAPI alkalmazás,
a frontend egy React/Vite SPA, az adatbázis PostgreSQL.

```mermaid
flowchart LR
    TV[TradingView alert] --> API[FastAPI webhook API]
    API --> APP[Application services]
    APP --> DOMAIN[Domain logic]
    APP --> DB[(PostgreSQL)]
    APP --> SCORE[Rule scoring]
    APP --> JOURNAL[Trading journal]
    WEB[React dashboard] --> API
    ML[ML module] --> DB
    EXPLAIN[Explanation provider] --> APP
```

## Rétegek

- `domain`: SMC fogalmak, score komponensek, risk számítások.
- `application`: webhook feldolgozás, setup workflow, outcome labeling.
- `infrastructure`: SQLAlchemy repositoryk, külső adapterek.
- `api`: HTTP és webhook contract.
- `analytics`: journal és teljesítménymutatók.
- `ml`: baseline modellek és időalapú validáció.

## Fontos korlát

Az LLM magyarázhat, összefoglalhat és taníthat, de nem számolhatja a setup
pontszámot és nem lépheti át a risk policy limiteket.

