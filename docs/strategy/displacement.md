# Displacement

A displacement erős, irányított ármozgást jelent. Az első implementáció nem
vizuális benyomásból dönt, hanem komponensekre bontott, determinisztikus score-t
számol.

## Komponensek

- `bodyAtrRatio`: gyertyatest mérete az előző gyertyákból számolt ATR-hez képest.
- `rangeAtrRatio`: teljes gyertyatartomány az előző gyertyák ATR-éhez képest.
- `bodyToRangeRatio`: a gyertyatest aránya a teljes range-en belül.
- `consecutiveDirectionalCandles`: egymást követő azonos irányú gyertyák száma.
- `volumeRatio`: aktuális volumen az előző gyertyák átlagvolumenéhez képest, ha
  rendelkezésre áll.

## ATR szabály

Az ATR a vizsgált gyertya előtti gyertyákból készül:

```text
atr = average(trueRange[candleIndex - atrPeriod : candleIndex])
```

A vizsgált gyertya nem része az ATR számításnak. Ez fontos, mert egy nagy
displacement gyertya különben saját magát emelné be az összehasonlítási alapba.

## Score

Minden komponens 0 és 1 közötti részpontszámot kap:

```text
componentScore = min(componentValue / threshold, 1)
```

A végső score súlyozott átlag. Ha volumenadat hiányzik, a volumen komponens
kimarad, és a score a rendelkezésre álló komponensek súlyai alapján
normalizálódik.

## Edge case-ek

- Ha nincs elég múltbeli gyertya ATR-hez, az ATR-alapú komponensek kimaradnak.
- Ha volumen hiányzik, nincs volumen büntetés vagy hamis volumen jel.
- Doji gyertya nem számít irányított displacementnek a consecutive komponensben.
- A displacement önmagában nem belépési jel, csak setup-minőségi komponens.

## Kapcsolódó kód

- `apps/api/src/smc_assistant/domain/displacement.py`
- `apps/api/tests/test_displacement.py`

