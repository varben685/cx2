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
