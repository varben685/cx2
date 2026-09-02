import json
from pathlib import Path

from smc_assistant.contracts.tradingview import TradingViewWebhookPayload


def main() -> None:
    schema = TradingViewWebhookPayload.model_json_schema(by_alias=True)
    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / "docs/contracts/generated/tradingview-webhook.schema.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
