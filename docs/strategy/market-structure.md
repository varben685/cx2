# Market structure

A market structure a swing high és swing low sorozatokból épül. A rendszer csak
megerősített pivotokat használ, így nem úgy kezeli a történelmi adatot, mintha
a pivot már a pivotgyertya pillanatában ismert lett volna.

## Induló paraméterek

- `leftBars`: bal oldali megerősítő gyertyák száma.
- `rightBars`: jobb oldali megerősítő gyertyák száma.
- `breakBuffer`: minimális áttörési buffer.
- `closeConfirmation`: gyertyazárás szükséges-e.

