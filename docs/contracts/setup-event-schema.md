# Setup event schema

Ez a dokumentum a belső setup események sémájának helye. Phase 2-ben a
TradingView webhook contractból Pydantic modellek készülnek, majd ezek alapján
exportálható JSON Schema jön létre.

Alapelv: a belső eseményeknek auditálhatónak, verziózottnak és
újrapontozhatónak kell lenniük.

