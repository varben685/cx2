# ADR-0006: Risk-gated paper trade állapotgép

## Státusz

Elfogadva, 2026-09-08.

## Kontextus

A projektnek élő setupokból paper trading pozíciókat kell követnie, de valódi
tőzsdei végrehajtás nem engedélyezett. A frontend által számolt pozícióméret vagy
szabadon átírható állapot nem lenne auditálható, és megkerülhetné a kockázati
korlátokat.

## Döntés

- Minden trade a backend `paper-risk-v1` policy jóváhagyása után jön létre.
- A backend számolja a risk amountot, quantityt, PnL-t és realizált R-t.
- Az állapotgép csak `PENDING -> OPEN -> CLOSED` és `PENDING -> CANCELLED`
  átmenetet enged.
- Automatikus stop/target zárás a tervezett barrier árat, manuális zárás a kapott
  exit árat használja.
- Az aktuális trade snapshot mellett minden változás append-only eseményként
  kerül tárolásra; az update optimista revisionszámmal védett.
- Egy alkalmazásfolyamaton belül a risk-check és trade-létrehozás sorosított,
  hogy a párhuzamos kérések se lépjék túl az aktív pozíciólimitet.
- A risk context nem az API lapozott listájából, hanem a teljes repository
  állományból épül, így listalimit nem gyengítheti a policy-t.
- A szolgáltatás csak szimuláció. Nincs broker adapter és nincs valódi order
  execution.

## Következmények

A pozícióéletciklus reprodukálható, a risk policy nem kerülhető meg a
frontendből, és memory, SQLite, illetve PostgreSQL módban ugyanaz a contract.
Az első verzió még kézi ármegfigyelést használ, egy kérésben egy állapotátmenetet
végez, és nem modellez fill slippage-et, commissiont, részleges teljesülést vagy
gap kockázatot. Ezeket későbbi adapterverzióban kell hozzáadni.
Több API worker esetén a globális pozíciólimit adatbázisszintű zárolást igényel.
