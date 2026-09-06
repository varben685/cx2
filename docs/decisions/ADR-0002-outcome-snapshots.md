# ADR-0002: Futásonként megőrzött outcome snapshotok

## Státusz

Elfogadva, 2026-09-06.

## Kontextus

Ugyanaz a setup több költségmodellel és tartási ablakkal is kiértékelhető.
Az eredményeket össze kell tudni hasonlítani a korábbi számítás felülírása
nélkül. Az offline backtest nem igényel korábban befogadott webhookot.

## Döntés

- Minden eredmény UUID azonosítót és a hívó által adott futásazonosítót kap.
- A `(run_id, event_id)` az idempotencia kulcsa. Az első mentés nyer;
  eltérő input vagy konfiguráció új futásazonosítót igényel.
- A teljes terv, konfiguráció, eredmény és verzióadat egy JSONB snapshotban
  marad együtt. A lista kulcsmezői külön SQL oszlopokba kerülnek.
- Pydantic `TypeAdapter` szerializálja és visszaolvasáskor validálja a típusos
  application/domain dataclassokat. A domain SQL-független marad.
- Az `event_id` logikai kapcsolat, nincs webhook/setup foreign key kényszer.
- Az értékelés a betöltött gyertyák SHA-256 lenyomatát is megőrzi.
- A mentési use case a hiányos megfigyelési ablakból származó timeoutot vagy
  nem aktiválódott eredményt visszautasítja.

## Alternatívák

Egy setuphoz egy felülírható eredmény egyszerűbb lenne, de elveszítené a régi
backtestet. Minden részmező külön relációs oszlopként megkönnyítene bizonyos
aggregációkat, viszont az első lépésben sok sémaváltozást igényelne. Később
a gyakran aggregált mezők mérés alapján külön oszlopba emelhetők.

## Következmények

A retry nem hoz létre duplikált eredményt, és a korábbi nettó R, MFE/MAE,
valamint a számítás beállításai megmaradnak. Egy futás egységes konfigurációját
egyelőre a hívó szervezi; külön backtest-run entitás még nincs.

Az adatlenyomat nem tárolja a gyertyákat, ezért a forrásfájl megőrzése kell a
reprodukáláshoz. Az automatikus élő kiértékelés és a felületi megjelenítés
későbbi lépés. A sémalétrehozás a repo meglévő `create_all` mintáját követi;
Alembic átálláskor ezt a táblát is be kell vonni.
