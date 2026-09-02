# Szintetikus OHLCV példák

A Phase 1 lezárásához létrejött egy kicsi, determinisztikus OHLCV adatsor. A
célja nem realisztikus piaci szimuláció, hanem az, hogy a domain fogalmak
együtt, reprodukálható módon tesztelhetők legyenek.

## Hol található?

- Kód: `apps/api/src/smc_assistant/domain/synthetic_examples.py`
- Integrált teszt: `apps/api/tests/test_phase1_synthetic_examples.py`

## Mini chart

| Index | Open | High | Low | Close | Volume | Oktatási szerep |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 98.0 | 100.0 | 95.0 | 99.0 | 100.0 | induló gyertya |
| 1 | 99.0 | 105.0 | 96.0 | 104.0 | 100.0 | korai swing high |
| 2 | 103.0 | 103.0 | 94.0 | 95.0 | 100.0 | confirmed swing low |
| 3 | 98.0 | 107.0 | 97.0 | 106.0 | 100.0 | confirmed swing high |
| 4 | 100.0 | 104.0 | 93.0 | 93.5 | 100.0 | bearish BOS |
| 5 | 108.0 | 118.0 | 108.0 | 117.0 | 200.0 | bullish BOS, bullish CHoCH, bullish FVG, displacement |
| 6 | 95.0 | 100.0 | 92.0 | 96.0 | 120.0 | bullish liquidity sweep |
| 7 | 104.0 | 105.0 | 95.0 | 96.0 | 120.0 | bearish FVG |

## Milyen eseményeket várunk?

- Swing low: index 2, price 94.0, confirmed at index 3.
- Swing high: index 3, price 107.0, confirmed at index 4.
- Bearish BOS: index 4, a 94.0 swing low záróáras törése.
- Bullish BOS: index 5, a 107.0 swing high záróáras törése.
- Bullish CHoCH: index 5, mert bearish kontextus után bullish structure break
  érkezik.
- Bullish FVG: index 3 és 5 között, 107.0-108.0 zónában.
- Bullish liquidity sweep: index 6, a 94.0 swing low alá szúrás és fölé
  visszazárás.
- Bearish FVG: index 5 és 7 között, 105.0-108.0 zónában.
- Displacement: index 5, erős bullish elmozdulás magasabb volumennel.

## Fontos tanulság

Ez az adatsor szándékosan kicsi és éles mozgásokat tartalmaz. A cél az, hogy a
fogalmakat izoláltan és determinisztikusan lehessen ellenőrizni. Nem célja, hogy
profitábilis stratégia vagy valós piaci eloszlás mintája legyen.
