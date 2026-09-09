# Phase 07: Live paper webhook orchestration

## 1. Elkészült

A TradingView setup webhook most automatikusan elindíthatja a paper trade
folyamatot. Ugyanazon a végponton `MARKET_PRICE` esemény is fogadható, amely az
egyező aktív trade-eket entry, stop és target alapján frissíti.

## 2. Hogyan működik?

Az `eventType` választja ki a payload contractot. Setupnál előbb megtörténik az
idempotens mentés és scoring, majd az orchestration meghívja a risk policyval
védett trade-létrehozást. Ár-eseménynél a backend előbb deduplikál, majd symbol,
exchange és timeframe alapján fan-outot végez az aktív paper trade-ekre.

## 3. Trading fogalmak

- `Price observation`: egy lezárt gyertya megfigyelt záróára.
- `Entry trigger`: a limit jellegű tervezett belépési ár elérése.
- `Barrier`: stop loss vagy take profit árszint.
- `Paper execution`: szimulált állapotváltozás, valódi megbízás nélkül.

## 4. Technikai fogalmak

- `Discriminated union`: az `eventType` alapján választott egyik contract.
- `Idempotency`: ugyanaz az `eventId` legfeljebb egyszer okoz mellékhatást.
- `Orchestration service`: több use case sorrendjét koordináló alkalmazásréteg.
- `Fan-out`: egy ár-esemény továbbítása több egyező aktív trade-nek.

## 5. Biztonsági döntések

Az automatikus út kizárólag paper trade-et kezel. Minden setup ugyanazon
backend risk gate-en megy át, mint a manuális létrehozás. Duplikált régi setup
nem indít utólag pozíciót, event type ütközés pedig explicit `409`.

## 6. Manuális kipróbálás

TradingView-ban frissítsd a Pine scriptet, kapcsold be a `Send paper price
updates` inputot, majd hozd létre újra az `Any alert() function call` alertet.
A setup válasz `paperTradeAutomation` blokkja mutatja a létrehozás eredményét.
A dashboard trade listája és a nyitott execution log öt másodpercenként frissül.

## 7. Korlátok

A price alert gyertyazáró árat küld, ezért intrabar stop/target sorrendet nem
ismer. Nincs queue/outbox retry, pending timeout, commission, slippage vagy
automatikus `OutcomeRecord` létrehozás.

## 8. Következő mérföldkő

A lezárt és visszavont paper trade-ekből automatikus, élő outcome rekord készül,
majd erre épül az első értesítési adapter.
