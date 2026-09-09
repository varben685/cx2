import json
from pathlib import Path

from pydantic import TypeAdapter

from smc_assistant.contracts.tradingview import TradingViewIncomingPayload


def main() -> None:
    schema = TypeAdapter(TradingViewIncomingPayload).json_schema(by_alias=True)
    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / "docs/contracts/generated/tradingview-webhook.schema.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
