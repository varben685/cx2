# Setup event schema

Ez a dokumentum a belső setup események sémájának helye. Phase 2-ben a
TradingView webhook contractból Pydantic modellek készülnek, majd ezek alapján
exportálható JSON Schema jön létre.

Alapelv: a belső eseményeknek auditálhatónak, verziózottnak és
újrapontozhatónak kell lenniük.

## Aktuális állapot

Az első külső contract elkészült:

- `apps/api/src/smc_assistant/contracts/tradingview.py`

A belső setup esemény séma külön lépésben készül majd, amikor a webhook
payloadból már alkalmazásszintű `SetupCandidate` objektumot képezünk.
