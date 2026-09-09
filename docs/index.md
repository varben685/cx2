# Dokumentációs index

Ez a könyvtár az `smc-ai-trading-assistant` működésének hiteles forrása.

## Fő dokumentumok

- [PLANS.md](PLANS.md): ExecPlan szabályok.
- [Aktív ExecPlan](exec-plans/active/full-project.md): teljes projektterv.
- [Fejlesztési napló](project/development-log.md): aktuális állapot és következő lépés.
- [Eredeti projektbrief](project/original-project-brief.md): a teljes indító utasítás.
- [Phase 00 learning](learning/phase-00-bootstrap.md): bootstrap magyarázat.
- [Phase 01 learning](learning/phase-01-domain-model.md): domain modell és pivot alapok.
- [Phase 02 learning](learning/phase-02-webhook-contract.md): TradingView webhook contract.
- [Phase 03 learning](learning/phase-03-pine-prototype.md): Pine Script prototípus.
- [Phase 04 learning](learning/phase-04-setup-scoring.md): rule-based setup scoring.
- [Phase 05 learning](learning/phase-05-outcome-backtest.md): outcome, persistence és analytics.
- [Phase 06 learning](learning/phase-06-backtest-frontend.md): backtest futások és outcome-ok frontend folyamata.
- [Phase 06 journal](learning/phase-06-journal.md): verziózott döntési napló és frontend folyamat.
- [Phase 06 analytics](learning/phase-06-analytics.md): equity, drawdown, bontások és döntési összevetés.
- [Phase 07 paper trading](learning/phase-07-paper-trading.md): risk policy, pozícióállapot és execution log.
- [Phase 07 live webhook](learning/phase-07-live-paper-webhooks.md): automatikus setup és idempotens árfrissítés.
- [Backtest analytics API](contracts/backtest-analytics.md): mutatók és lekérdezési szabályok.
- [Backtest futtatás](contracts/backtests.md): CSV-batch, mentés és outcome lekérdezés.
- [Trading journal API](contracts/journal.md): journal létrehozás, szerkesztés és revíziók.
- [Paper trading API](contracts/paper-trading.md): szimulált végrehajtás, risk gate és állapotgép.
- [Szintetikus OHLCV példák](strategy/synthetic-examples.md): Phase 1 integrált mini chart.

## Területek

- `glossary/`: trading, AI/ML és szoftveres fogalomtár.
- `strategy/`: SMC/ICT-inspired stratégiai formalizálás.
- `architecture/`: rendszerkomponensek és adatáramlás.
- `contracts/`: webhook és esemény JSON contractok.
- `learning/`: fázisonkénti oktatási dokumentumok.
- `decisions/`: ADR-ek.
- `operations/`: lokális fejlesztés, paper trading, biztonság, hibakeresés.
- `project/`: projektbrief és fejlesztési állapotnapló.
