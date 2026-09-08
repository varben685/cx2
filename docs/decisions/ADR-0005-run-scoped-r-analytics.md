# ADR-0005: Futáshoz kötött, fix R-alapú teljesítményelemzés

## Státusz

Elfogadva, 2026-09-08.

## Kontextus

Az outcome-ok több backtest futásból származhatnak, ugyanaz az esemény eltérő
költség- vagy holding konfigurációval többször is szerepelhet. A számlaméret és
a trade-enként kockáztatott pénzösszeg még nincs modellezve, miközben a
drawdownhoz stabil sorrend és egyértelmű mértékegység kell.

## Döntés

- A részletes jelentéshez kötelező egy mentett `runId`; külön futások nem
  keverednek.
- Az equity curve fix kockázati egységekben, a nettó R értékek összegeként
  készül. Nem használ kamatos újrabefektetést és nem állít pénzalapú hozamot.
- A lezárt trade-ek sorrendje exit time, majd outcome UUID. A maximum drawdown
  az addigi kumulált R-csúcstól mért legnagyobb pozitív távolság.
- A score- és komponensbontás a mentett backtest inputból, a válaszban megadott
  verziójú determinisztikus score-ral készül.
- A journal-döntések az event/setup azonosítóval kapcsolódnak. A kihagyott
  setup backtest outcome-ja counterfactual eredmény, nem tényleges kötés.
- A frontend egyetlen `report` választ használ, a név szerint elvárt session-
  és score-bucket végpont ugyanennek a számításnak részhalmazát adja.

## Következmények

A mutatók reprodukálhatók és nem keverik a különböző futási konfigurációkat.
A teljes R-görbe jól használható stratégia-összehasonlításra, de számlaszintű
drawdownhoz később pozícióméret, induló tőke, párhuzamos trade és compounding
szabály szükséges. A scoring verzió implementációját változatlanul meg kell
őrizni vagy új verzió alatt módosítani.
