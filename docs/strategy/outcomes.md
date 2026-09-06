# Outcome és backtest alapok

## Cél

Az outcome engine célja, hogy egy pontozott setup candidate későbbi ármozgását
determinisztikusan és auditálhatóan címkézze. Ez az alapja a backtestnek, a
journal statisztikáknak és később az ML datasetnek.

## Első szabály: conservative triple-barrier

Az első implementáció három feltételt figyel:

- entry trigger: az ár érinti az entry szintet;
- horizontális barrier: stop loss vagy take profit érintése;
- vertikális barrier: maximális tartási gyertyaszám.

Ha az entry nem aktiválódik az `entry_timeout_bars` ablakon belül, az outcome
`NOT_TRIGGERED`.

Ha entry után a take profit érintődik először, az outcome `WIN`.

Ha entry után a stop loss érintődik először, az outcome `LOSS`.

Ha entry után egyik horizontális barrier sem érintődik a `max_holding_bars`
ablakon belül, az outcome `TIMEOUT`, az exit ár pedig az utolsó vizsgált gyertya
záróára.

## Intrabar bizonytalanság

OHLCV gyertyából nem tudjuk biztosan, hogy gyertyán belül a stop vagy a target
érintődött-e előbb. Ezért az első engine konzervatív:

- ha ugyanazon gyertyában a stop és a target is érinthető, a stop számít
  előszörinek;
- ez csökkenti az optimista backtest bias kockázatát;
- később alacsonyabb idősíkú adatokkal vagy tick adatokkal pontosítható.

## R számítás

A `realized_r` az entry és stop közötti kezdeti kockázathoz viszonyít:

- long: `(exit_price - entry_price) / initial_risk`;
- short: `(entry_price - exit_price) / initial_risk`.

Stop loss esetén ez `-1.0`, 2R take profit esetén `2.0`.

## MFE és MAE

Az outcome engine az aktivált trade útját is méri az exit vagy timeout
gyertyáig:

- `mfe_r`: maximum favorable excursion R-ben;
- `mae_r`: maximum adverse excursion R-ben;
- `max_favorable_price`: a trade irányában legkedvezőbb elért ár;
- `max_adverse_price`: a trade irányával szembeni legkedvezőtlenebb elért ár.

Long pozíciónál a high értékek adják a kedvező, a low értékek az adverse oldalt.
Short pozíciónál ez fordítva értelmeződik: a low a kedvező ár, a high az adverse
ár.

Ha az entry nem aktiválódik, akkor nincs trade út, ezért az `excursion` értéke
`null`.

## Commission és slippage

Az outcome engine külön tartja a bruttó és nettó R értéket:

- `realized_r`: költségek előtti eredmény;
- `net_realized_r`: commission és slippage után becsült eredmény;
- `costs.commission_amount`: round-trip commission becslés;
- `costs.slippage_amount`: round-trip slippage becslés;
- `costs.cost_r`: teljes költség R-ben kifejezve.

Az első modell bps-alapú és oldalankénti:

- `commission_bps_per_side`;
- `slippage_bps_per_side`.

A becslés egy egységnyi pozícióra számol: az entry és exit ár notional összegére
alkalmazza az oldalankénti bps értékeket, majd ezt osztja a kezdeti
kockázattal. Ez egyszerű, determinisztikus alap a backtesthez; később
instrumentum-specifikus fee schedule és order type szerinti slippage modell
válthatja.

## Market data input

Az első backtest input réteg OHLCV CSV-ből tud `Candle` objektumokat építeni.
Támogatott alap oszlopok:

- `time`, `timestamp` vagy `open_time`;
- opcionális `close_time`;
- `open`, `high`, `low`, `close`;
- opcionális `volume`;
- opcionális `symbol` és `timeframe` szűréshez.

Ha nincs `close_time`, akkor a provider a query vagy a provider
alapértelmezett timeframe értékéből számolja ki a gyertya záróidejét.

## Setup outcome evaluation

A TradingView payload `execution` blokkja adja az első `TradePlan` forrást:

- `direction`;
- `entry`;
- `stopLoss`;
- `takeProfit`.

Az evaluation réteg a payload `symbol`, `timeframe` és `barCloseTime` mezőiből
épít market data queryt. A backtest szelet így a setup gyertya lezárása után
indul, és az outcome engine már csak jövőbeli gyertyákon fut.

## Tartós outcome rekordok

Az `evaluate_and_save_tradingview_outcome` application függvény a kiértékelést
egy `OutcomeRepository` adapteren keresztül menti. In-memory és SQLAlchemy
(PostgreSQL/SQLite) adapter is rendelkezésre áll.

Minden rekord UUID `outcome_id` és `run_id` azonosítót kap. A hívó adja meg a
futásazonosítót: ugyanazon futás és `event_id` ismétlése az első eredményt adja
vissza, újraszámítás és felülírás nélkül. Más konfigurációval vagy frissített
adatsorral történő új értékeléshez új `run_id` szükséges.

A snapshot tartalmazza a trade tervet, teljes outcome-ot, költségeket,
MFE/MAE értékeket, tényleges konfigurációt, stratégia- és engine-verziót,
exchange-et, setup-záróidőt, UTC kiértékelési időt, gyertyaszámot és a betöltött
gyertyasor SHA-256 lenyomatát. A lenyomat adategyezőséget ellenőriz; a forrás
CSV megőrzését nem helyettesíti.

A mentési folyamat `IncompleteOutcomeError` hibát ad, ha a `NOT_TRIGGERED`
eredményhez még nem telt le az entry ablak, vagy a `TIMEOUT` eredményhez még
nincs meg a teljes tartási gyertyaszám. Ilyenkor nem jön létre rekord, és
ugyanazzal a futásazonosítóval később újra lehet próbálni. Korábban elért stop
vagy target esetén már végleges eredmény menthető. Ez a védelem a mentési
use case része; a közvetlen domain engine továbbra is a kapott adatsor
végéig értékel. A gyertyaszám önmagában nem ellenőrzi az adatfolyam hézagait.

A tárolás jelenleg explicit application hívás: a webhook fogadása és a
dashboard még nem indít automatikus outcome értékelést.
