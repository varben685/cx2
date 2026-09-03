# Data model

Az első adatmodell részben már implementált adatbázis sémára épül. A
`webhook_events` tábla SQLAlchemy metadata alapján jön létre; a későbbi
fázisban ezt Alembic migrációkra kell cserélni.

```mermaid
erDiagram
    TradingInstrument ||--o{ WebhookEvent : receives
    WebhookEvent ||--o| SetupCandidate : creates
    SetupCandidate ||--o{ SetupScore : has
    SetupCandidate ||--o| TradePlan : plans
    TradePlan ||--o{ SimulatedTrade : simulates
    SimulatedTrade ||--o| TradeOutcome : resolves
    SetupCandidate ||--o{ JournalEntry : documents
    StrategyVersion ||--o{ StrategyConfiguration : versions
    StrategyConfiguration ||--o{ SetupScore : scores
    ModelVersion ||--o{ ModelPrediction : predicts
```

Később a többi üzleti entitás UUID elsődleges kulcsot és UTC időbélyeget kap.

## Implementált táblák

### `webhook_events`

Az első tartósított entitás a beérkező TradingView webhook esemény.

| Oszlop | Típus | Megjegyzés |
| --- | --- | --- |
| `event_id` | string(200) | Elsődleges kulcs és idempotencia kulcs. |
| `event_type` | string(80) | Jelenleg `SETUP_CANDIDATE`. |
| `source` | string(80) | Jelenleg `TRADINGVIEW`. |
| `schema_version` | string(40) | Contract verzió, jelenleg `1.0`. |
| `payload` | JSON/JSONB | A validált webhook payload camelCase JSON mezőkkel. |
| `received_at` | timestamptz | A webhook befogadásának ideje. |
| `created_at` | timestamptz | A DB rekord létrehozásának ideje. |

Az `event_id` unique constraint védi az idempotenciát. Ha ugyanaz az esemény
ismét beérkezik, a repository az elsőként mentett rekordot adja vissza.

### `setup_candidates`

A pontozott, belső setup candidate rekord. Egyelőre a TradingView webhookból
származik, és az `event_id` mezőn keresztül kapcsolódik a bejövő webhook
eseményhez.

| Oszlop | Típus | Megjegyzés |
| --- | --- | --- |
| `setup_id` | string(200) | Elsődleges kulcs. Jelenleg megegyezik az `event_id` értékkel. |
| `event_id` | string(200) | Unique kulcs és kapcsolat a `webhook_events.event_id` mezőre. |
| `schema_version` | string(40) | Külső payload contract verzió. |
| `strategy_version` | string(80) | Stratégia verzió, például `smc-rce-v1`. |
| `scoring_config_version` | string(80) | Pontozási config verzió, például `rule-score-v1`. |
| `symbol` | string(40) | Instrumentum. |
| `exchange` | string(40) | Exchange vagy `UNKNOWN`. |
| `timeframe` | string(20) | TradingView timeframe. |
| `direction` | string(20) | `LONG` vagy `SHORT`. |
| `htf_bias` | string(20) | `BULLISH`, `BEARISH` vagy `NEUTRAL`. |
| `score` | float | 0-100 közötti determinisztikus setup score. |
| `accepted` | boolean | Az aktuális scoring config szerinti döntés. |
| `components` | JSON/JSONB | Komponensenkénti score snapshot. |
| `rejection_reasons` | JSON/JSONB | Hard reject okok. |
| `positive_reasons` | JSON/JSONB | Pozitív indokok. |
| `negative_reasons` | JSON/JSONB | Negatív indokok. |
| `bar_close_time` | timestamptz | A jelhez tartozó TradingView bar zárása. |
| `received_at` | timestamptz | A webhook befogadásának ideje. |
| `created_at` | timestamptz | A DB rekord létrehozásának ideje. |

Az `event_id` unique constraint miatt ugyanaz a webhook esemény nem hoz létre
több setup candidate rekordot.
