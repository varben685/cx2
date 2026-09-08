# Paper trading API

## Hatókör

Ez a contract kizárólag szimulált végrehajtást ír le. Egyetlen végpont sem küld
valódi ordert brókerhez vagy tőzsdéhez.

## Állapotgép

`PENDING -> OPEN -> CLOSED`

`PENDING -> CANCELLED`

A létrehozott trade pending limit terv. LONG esetén az entry vagy alacsonyabb,
SHORT esetén az entry vagy magasabb megfigyelt ár nyitja meg. Nyitott állapotban
a stop vagy target elérése a tervezett barrier áron zár. Manuális zárás csak
`OPEN`, visszavonás csak `PENDING` állapotban engedélyezett.

Egy ármegfigyelés legfeljebb egy állapotátmenetet végez. A price endpoint nem
helyettesít valós tick- vagy gyertyaadat-szolgáltatót.

## Végpontok

- `POST /api/v1/paper-trades`: trade terv létrehozása elfogadott setupból.
- `GET /api/v1/paper-trades`: lista, opcionális `status`, `symbol`, `limit` szűréssel.
- `GET /api/v1/paper-trades/{tradeId}`: aktuális snapshot.
- `POST /api/v1/paper-trades/{tradeId}/market-price`: ár megfigyelése.
- `POST /api/v1/paper-trades/{tradeId}/close`: manuális zárás.
- `POST /api/v1/paper-trades/{tradeId}/cancel`: pending terv visszavonása.
- `GET /api/v1/paper-trades/{tradeId}/events`: append-only execution log.

Létrehozási példa:

```json
{
  "setupId": "BTCUSDT-1-1767225660000-LONG",
  "accountBalance": 10000,
  "riskPercent": 1
}
```

Árfrissítés:

```json
{
  "price": 65180
}
```

Manuális zárás:

```json
{
  "exitPrice": 65320
}
```

## Pozícióméret

`riskAmount = accountBalance * riskPercent / 100`

`quantity = riskAmount / abs(entryPrice - stopLoss)`

`realizedR = realizedPnl / riskAmount`

LONG PnL: `(exitPrice - entryPrice) * quantity`. SHORT PnL:
`(entryPrice - exitPrice) * quantity`.

## Risk policy

A `paper-risk-v1` a létrehozás előtt ellenőrzi:

- a setup elfogadottságát és minimum score-ját;
- a maximum trade kockázatot és minimum tervezett R:R arányt;
- az engedélyezett sessiont;
- a pending és open pozíciók maximumát;
- az UTC nap szerinti realizált veszteséget;
- az egymást követő veszteségeket;
- az instrumentum cooldownját;
- a konfigurált korrelációs csoport nyitott pozícióit.

A policy a teljes paper trade állományból épít kontextust; az API listázási
limitje nem csonkolhatja a kockázati számítást.

Elutasításkor nincs paper trade rekord, az API `422` választ és audit eseményt
ad. Setup hiányra `404`, duplikációra vagy tiltott állapotátmenetre `409` jár.

## Persistence

A `paper_trades` tábla az aktuális immutable snapshotot és revisionszámot, a
`paper_trade_events` minden létrehozást, ármegfigyelést és állapotátmenetet
sorrendhelyesen tárol. Az update optimista revisionszámmal védett. Az egy
API-folyamaton belüli létrehozás sorosított; több workerhez később
adatbázisszintű kockázati zárolás szükséges.
