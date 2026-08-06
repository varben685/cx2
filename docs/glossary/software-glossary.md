# Szoftveres fogalomtár

## Modular monolith

Egy deployolható alkalmazás, amely belül jól elkülönített modulokra oszlik.
Az MVP-ben ez egyszerűbb és tanulhatóbb, mint a korai microservice bontás.

## Idempotencia

Ugyanazon művelet többszöri végrehajtása nem okoz többszörös mellékhatást.
Webhookoknál az `eventId` alapján deduplikálunk.

## Contract

Két rendszer közötti adatcsere formális megállapodása. Itt a TradingView JSON
payload és a backend Pydantic modellje együtt adja.

## CI

Continuous Integration. Automatikus ellenőrzések futtatása push vagy pull
request esetén.

