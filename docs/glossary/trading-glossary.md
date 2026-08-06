# Trading fogalomtár

## Swing high

Olyan lokális csúcspont, amelynek bal és jobb oldalán meghatározott számú
gyertya alacsonyabb high értékkel rendelkezik. A rendszer csak akkor tekinti
ismertnek, amikor a jobb oldali megerősítő gyertyák már lezárultak.

## Swing low

Olyan lokális mélypont, amelynek bal és jobb oldalán meghatározott számú
gyertya magasabb low értékkel rendelkezik.

## BOS

Break of Structure. Az aktuális struktúra irányába történő, megerősített swing
szintet áttörő struktúratörés. Alapértelmezésben gyertyazárás és buffer erősíti.

## CHoCH

Change of Character. Az aktuális struktúrával ellentétes irányú első jelentős
struktúratörés. Fontos: önmagában nem garantál trendfordulót.

## Fair Value Gap

Háromgyertyás imbalance modell. Bullish FVG akkor alakulhat ki, ha az első
gyertya high értéke kisebb, mint a harmadik gyertya low értéke. Bearish FVG
esetén az első gyertya low értéke nagyobb, mint a harmadik gyertya high értéke.

## Liquidity sweep

Az ár kanóccal átlép egy korábbi megerősített swing szintet, majd visszazár a
szint mögé. A jel gyakran stopvadászatként értelmezett likviditásfelvételt
modellez.

## Displacement

Erős, irányított ármozgás. A rendszer több komponensből becsüli: ATR-hez mért
gyertyatest, teljes tartomány, body-to-range arány, egymást követő irányazonos
gyertyák és opcionális volumeneltérés.

## Risk-reward

```text
initialRisk = abs(entryPrice - stopLoss)
plannedReward = abs(takeProfit - entryPrice)
riskReward = plannedReward / initialRisk
```

## R-multiple

```text
realizedR = realizedProfitOrLoss / initialRisk
```

Az R-multiple a profitot vagy veszteséget az eredeti kockázathoz viszonyítja.

