"""azd postprovision hook: write .env for the notebooks from the azd environment values."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = [
    "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP", "AZURE_LOCATION",
    "STARK_FOUNDRY_ACCOUNT", "STARK_FOUNDRY_PROJECT", "STARK_PROJECT_ENDPOINT", "STARK_ACCOUNT_ENDPOINT",
    "STARK_APPINSIGHTS", "STARK_LOG_WORKSPACE_ID",
    "STARK_CHAT_MODEL", "STARK_JUDGE_MODEL", "STARK_FAST_MODEL", "STARK_EMBEDDING_MODEL",
]
OPTIONAL = ["STARK_MCP_FUNCTION", "STARK_MCP_URL", "STARK_ENABLE_CU"]  # empty when the feature is off


def main() -> None:
    missing = [k for k in KEYS if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"azd did not provide: {', '.join(missing)}. Run `azd provision` first.")
    lines = [f"{k}={os.environ[k]}\n" for k in KEYS] + [f"{k}={os.environ.get(k, '')}\n" for k in OPTIONAL]
    (ROOT / ".env").write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {ROOT / '.env'} (git-ignored). Open notebooks/00_setup_workshop.ipynb next.")


if __name__ == "__main__":
    main()
