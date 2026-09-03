# Setup scoring

Az első működő pontozás determinisztikus. A cél 0 és 100 közötti reprodukálható
score, komponensenkénti indoklással.

## Kezdeti komponensek

- HTF bias egyezése: 20 pont.
- CHoCH megléte: 20 pont.
- Liquidity sweep megléte: 15 pont.
- Displacement erőssége: 20 pont.
- FVG mérete ATR-hez képest: 10 pont.
- Session: 10 pont.
- Minimum risk-reward: 5 pont.

Minden score mellé pozitív indokok, negatív indokok, elutasítási okok,
strategy version és configuration version kerül.

## Első determinisztikus szabály

Az első implementáció helye:

- `apps/api/src/smc_assistant/domain/setup_scoring.py`

Alapértelmezett verziók:

- strategy version: `smc-rce-v1`
- scoring config version: `rule-score-v1`

Hard reject okok:

- `HTF_BIAS_CONFLICT`: a magasabb idősík bias ellentétes a setup irányával.
- `MISSING_CHOCH`: nincs karakterváltás.
- `RISK_REWARD_TOO_LOW`: a risk-reward kisebb, mint a minimum.
- `SCORE_BELOW_THRESHOLD`: az összpontszám kisebb, mint az elfogadási küszöb.

A semleges HTF bias nem hard reject, hanem fél HTF bias pontot ad. Ez azért
fontos, mert a Pine prototípusban a bias bootstrap kontextus, nem önálló setup
jel.

## Alapértelmezett küszöbök

- acceptance threshold: `70`
- minimum risk-reward: `2.0`
- displacement target score: `0.65`
- FVG size/ATR target: `0.25`

Az értékek szándékosan konfigurációban élnek, hogy később ugyanazt a setupot
újra lehessen pontozni egy másik config verzióval.
