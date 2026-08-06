# ADR-0001: Moduláris monolit MVP

## Státusz

Elfogadva.

## Kontextus

A projekt több területet érint: webhook, domain logika, scoring, journal,
backtest, frontend, ML és LLM magyarázat. Korai microservice bontás növelné az
üzemeltetési és oktatási komplexitást.

## Döntés

Az MVP moduláris monolitként indul. A backend egy Python projekt, belül tiszta
rétegekkel: `domain`, `application`, `infrastructure`, `api`, `analytics`, `ml`.

## Következmények

Egyszerűbb lokális fejlesztés és tanulhatóság. Később csak bizonyított
skálázási vagy ownership igény esetén bontunk külön szolgáltatást.

