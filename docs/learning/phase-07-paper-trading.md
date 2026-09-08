# Phase 07: Risk-gated paper trading

## 1. Elkészült

Elkészült az első teljes paper trade munkafolyamat: elfogadott setupból pending
terv hozható létre, árfrissítéssel megnyitható és stopnál vagy targetnél zárható.
Manuális zárás, visszavonás, lista, részletező és execution log is rendelkezésre
áll.

## 2. Hogyan működik?

A backend visszaolvassa a setup eredeti TradingView webhookját, abból veszi az
entry, stop, target és session értékeket. A risk policy a teljes paper trade
előzmény alapján dönt. Jóváhagyás után kiszámolja a méretet, és minden későbbi
változást revisionszámmal és külön eseménnyel ment.

## 3. Trading fogalmak

- `Risk amount`: az account balance meghatározott százaléka.
- `Quantity`: a risk amount és az entry-stop távolság hányadosa.
- `Pending`: a tervezett entry még nem teljesült.
- `Open`: a szimulált pozíció aktív.
- `Realized R`: a lezárt eredmény az induló kockázati egységhez viszonyítva.

## 4. Technikai fogalmak

- `State machine`: csak előre definiált állapotátmenetek engedélyezettek.
- `Optimistic locking`: a revision megakadályozza két párhuzamos update csendes
  felülírását.
- `Append-only event log`: a korábbi végrehajtási eseményeket nem írjuk át.
- `Risk gate`: a létrehozás előtt futó, megkerülhetetlen backend szabályrendszer.

## 5. Ellenőrzés

A tesztek lefedik a policy összes korlátját, a memory/SQLite/PostgreSQL
repositorykat, a LONG target és SHORT stop útvonalat, a manuális zárást,
visszavonást, duplikációt és hibás állapotátmenetet. Külön frontend teszt járja
végig a létrehozás és nyitás folyamatát.

## 6. Manuális kipróbálás

Nyisd meg a `http://localhost:5173` oldalt. A Paper trading panelen válassz egy
elfogadott, még nem használt setupot, add meg a szimulált account balance és
risk százalék értékét, majd hozd létre a trade-et. A szem ikonnal nyisd meg a
részletezőt és küldj entry, majd stop vagy target árat.

## 7. Fontos fájlok

- `domain/risk_policy.py`: determinisztikus kockázati korlátok.
- `application/paper_trading.py`: állapotátmenetek és számítások.
- `infrastructure/sql_paper_trades.py`: PostgreSQL/SQLite persistence.
- `api/paper_trades.py`: REST contract.
- `PaperTradingPanel.tsx`: frontend munkafolyamat.
- `docs/contracts/paper-trading.md`: részletes API és számítási szabályok.

## 8. Döntések és feltételezések

A pending terv limit belépésként viselkedik. Stop és target zárás a tervezett
barrier áron történik; manuális zárás a megadott áron. A napi veszteség UTC nap
szerint, kizárólag lezárt paper trade-ekből számolódik. Pending és open trade is
aktív pozíciónak számít a limiteknél.

## 9. Kockázatok és nyitott kérdések

Az ár most manuálisan érkezik, nincs market-data stream, részleges fill, gap,
commission, slippage vagy automatikus timeout. A korrelációs csoportok üres
alapértékkel indulnak, ezért éles papírportfólió előtt instrumentumonként kell
konfigurálni őket. Az adatbázisséma továbbra is `create_all` alapú.

## 10. Következő mérföldkő

Az élő TradingView webhook összekötése a paper trade workflow-val és az
automatikus outcome/árfrissítési adapter első verziója.
