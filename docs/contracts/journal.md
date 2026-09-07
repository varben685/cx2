# Trading journal API

## Cél és hatókör

A journal egy már befogadott és pontozott setup döntési naplója. Egy setuphoz
legfeljebb egy journal tartozhat. A bejegyzés létrehozáskor lemásolja a setup,
a TradingView forrásesemény és - ha elérhető - az outcome lényeges adatait,
így a későbbi stratégia- vagy pontozásmódosítás nem írja át a történeti kontextust.

Ez a folyamat nem ad le tőzsdei megbízást. A `TAKEN` és `SKIPPED` érték a
felhasználó döntésének dokumentációja.

## Végpontok

| Metódus és útvonal | Viselkedés |
| --- | --- |
| `POST /api/v1/setups/{setup_id}/journal` | Új bejegyzés, siker esetén 201. |
| `GET /api/v1/journal?limit=50&symbol=BTCUSDT&executionStatus=TAKEN` | Legutóbb frissített bejegyzések, opcionális szűrőkkel. |
| `GET /api/v1/journal/{journal_id}` | Teljes bejegyzés setup- és outcome-snapshottal. |
| `PUT /api/v1/journal/{journal_id}` | A felhasználói mezők teljes frissítése. |
| `GET /api/v1/journal/{journal_id}/revisions` | Verziók növekvő sorrendben. |

A lista legfeljebb 100 rekordot ad vissza és nem tartalmazza a nagy
`setupSnapshot` és `outcomeSnapshot` mezőket. A részletező végpont ezeket is
visszaadja.

## Írható mezők

| Mező | Szabály |
| --- | --- |
| `executionStatus` | `NOT_RECORDED`, `TAKEN` vagy `SKIPPED`; alapérték `NOT_RECORDED`. |
| `userNote` | Opcionális, legfeljebb 5000 karakter. |
| `screenshotReference` | Opcionális URL vagy fájlhivatkozás, legfeljebb 2048 karakter. |
| `manualRating` | Opcionális egész szám 1 és 5 között. |
| `manualOverride` | Jelzi, hogy a felhasználó felülbírálta a rendszer javaslatát. |
| `overrideReason` | Felülbíráláskor kötelező, egyébként nem adható meg; legfeljebb 1000 karakter. |
| `tags` | Legfeljebb 10 címke, címkénként 40 karakter. |

A szövegmezők szélső whitespace-e eltűnik. Az üres opcionális szöveg `null`
lesz, a címkék kis- és nagybetűtől függetlenül duplikációmentesek.

Létrehozáskor opcionálisan megadható az `outcomeId`. Ha hiányzik, a rendszer
az adott setup eseményazonosítójához tartozó legfrissebb outcome-ot kapcsolja.
Idegen setuphoz tartozó outcome 422 hibát ad.

Frissítéskor az `expectedRevision` kötelező. A szerver csak akkor ír, ha ez
megegyezik az aktuális verzióval; elavult kliens 409 választ kap. Minden
sikeres írás eggyel növeli a `revision` értékét és új, csak hozzáfűzhető
revíziós snapshotot hoz létre.

## Példák

```json
{
  "executionStatus": "TAKEN",
  "userNote": "Megvártam az alsó idősíkos megerősítést.",
  "manualRating": 4,
  "manualOverride": false,
  "tags": ["A+", "London"]
}
```

```json
{
  "expectedRevision": 1,
  "executionStatus": "SKIPPED",
  "userNote": "A belépés előtt megszűnt a megerősítés.",
  "screenshotReference": null,
  "manualRating": 5,
  "manualOverride": true,
  "overrideReason": "A piaci struktúra időközben megváltozott.",
  "tags": ["discipline"]
}
```

## Hibák

- `404`: setup, forrásesemény, outcome vagy journal nem található.
- `409`: a setuphoz már van journal, vagy az `expectedRevision` elavult.
- `422`: mezővalidációs hiba, illetve az outcome másik setuphoz tartozik.
