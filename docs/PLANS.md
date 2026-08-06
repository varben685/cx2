# ExecPlan szabályok

Az ExecPlan egy élő, auditálható végrehajtási terv. A célja, hogy a projekt
ne sodródjon: mindig látszódjon, mi készült el, mi van folyamatban, és mi a
következő mérhető mérföldkő.

## Helye

- Aktív terv: `docs/exec-plans/active/full-project.md`.
- Befejezett tervek: `docs/exec-plans/completed/`.

## Kötelező tartalom

Minden ExecPlan tartalmazza:

- cél;
- hatókör;
- mérföldkövek;
- ellenőrzési parancsok;
- dokumentációs követelmények;
- kockázatok és nyitott kérdések;
- állapotnapló.

## Állapotjelölések

- `[ ]`: nincs elkezdve.
- `[~]`: folyamatban.
- `[x]`: elkészült és ellenőrzött.
- `[!]`: blokkolt vagy részben ellenőrzött.

## Mérföldkő lezárása

Egy mérföldkő csak akkor jelölhető késznek, ha:

- a kapcsolódó kód elkészült;
- a releváns tesztek sikeresek;
- lint és type check sikeres vagy dokumentáltan környezeti okból blokkolt;
- a dokumentáció frissült;
- nincs ismert future leakage vagy repainting kockázat a kritikus úton;
- az ExecPlan tartalmazza a tényleges eredményt.

## Frissítési szabály

Minden munkamenet végén frissíteni kell az aktív ExecPlant. Ha egy mérföldkő
közben változik a terv, a változás okát röviden rögzíteni kell.

