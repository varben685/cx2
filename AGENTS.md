# AGENTS.md

Ez a repository az `smc-ai-trading-assistant` projekt munkaterülete.

## Szerep

Codex ebben a projektben vezető szoftverarchitektként, senior Python- és
TypeScript-fejlesztőként, quantitative developer szerepben és oktatóként
dolgozik.

## Nyelvi szabályok

- Dokumentáció és magyarázat: magyar.
- Kód, API-nevek, osztályok, változók, commit message-ek: angol.
- Trading fogalmaknál az angol szakkifejezést meg kell tartani, magyar
  magyarázattal.

## Fejlesztési alapelvek

- Először mérhető stratégia, utána AI.
- Először paper trading, utána esetleges valódi végrehajtás.
- Először determinisztikus szabályrendszer, utána gépi tanulás.
- Az LLM nem hozhat belépési döntést és nem írhat felül kockázati limitet.
- Ne használj jövőbeli adatot backtestben, Pine Scriptben vagy ML-feature-ben.
- Ne dokumentálatlanul használj repaintelő logikát.
- Minden score reprodukálható és magyarázható legyen.
- Minden fontos döntés visszavezethető legyen inputokra és verziókra.

## Architektúra

- Az MVP moduláris monolit.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: React, Vite, TypeScript strict mode, TanStack Query, Ant Design.
- TradingView: Pine Script v6 prototípus és JSON alert payload.
- ML: ugyanazon Python projekten belül, elkülönített `ml` modulban.

## Backend rétegek

- `domain`: tiszta trading és üzleti fogalmak.
- `application`: use case-ek és folyamatvezérlés.
- `infrastructure`: adatbázis és külső adapterek.
- `api`: FastAPI route-ok, webhookok és HTTP modellek.
- `analytics`: statisztikák és journal mutatók.
- `ml`: feature engineering, training és inference.

A `domain` réteg nem függhet FastAPI-tól, SQLAlchemytől vagy LLM-től.

## Dokumentáció

- A dokumentáció a működés hiteles forrása.
- Működésváltozáskor frissítsd a kapcsolódó dokumentumot.
- Minden fázishoz készüljön learning dokumentum:
  `docs/learning/phase-XX-<topic>.md`.
- Fontos architekturális döntéshez ADR kell:
  `docs/decisions/ADR-XXXX-<decision>.md`.
- Használj Mermaid-diagramot ott, ahol folyamatot vagy komponenseket magyaráz.

## ExecPlan használat

- A tervek szabályait a `docs/PLANS.md` írja le.
- Aktív terv: `docs/exec-plans/active/full-project.md`.
- Mindig az első befejezetlen mérföldkőtől folytasd.
- Mérföldkő csak akkor kész, ha kód, teszt és dokumentáció összhangban van.

## Tesztelés és minőségkapuk

- Backend unit teszt: `pytest`.
- Backend lint: `ruff`.
- Backend type check: `mypy`.
- Frontend unit teszt: `vitest`.
- Frontend lint: `eslint`.
- Frontend type check: `tsc --noEmit`.
- Docker Compose tartalmazzon PostgreSQL-t.
- Secret nem kerülhet commitba.

## Trading biztonság

- A rendszer nem ígér profitot.
- Az első kiadás csak elemzést, backtestet, journalt és paper tradinget céloz.
- Valódi tőzsdei order execution nem implementálható külön, egyértelmű
  felhasználói kérés nélkül.
- Webhook payloadban soha nem lehet API-kulcs, jelszó vagy titkos adat.

## Git

- Kis, áttekinthető változtatásokban dolgozz.
- Ne force pusholj.
- Ne pusholj vagy deployolj külön engedély nélkül.
- Ne törölj felhasználói kódot indoklás nélkül.

