"""Create or update the azd environment of src/jarvis-harness from .env (chapter 17).

src/jarvis-harness is its own azd project (the Copilot harness needs newer Foundry extensions than the root
azure.yaml pins). It provisions nothing: its services deploy into the project that the root `azd up` created.
This script copies the values those `azure.ai.*` services read into an azd environment named `stark-harness`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "src" / "jarvis-harness"
ENV_NAME = "stark-harness"
AZD = shutil.which("azd") or "azd"

load_dotenv(ROOT / ".env")


def azd(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    out = subprocess.run([AZD, *args], capture_output=True, text=True, cwd=HARNESS)
    if check and out.returncode != 0:
        sys.exit(f"azd {' '.join(args[:2])} failed:\n{out.stdout}{out.stderr}")
    return out


def main() -> None:
    need = ["AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP", "AZURE_LOCATION",
            "STARK_FOUNDRY_ACCOUNT", "STARK_FOUNDRY_PROJECT", "STARK_PROJECT_ENDPOINT", "STARK_CHAT_MODEL"]
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        sys.exit(f".env has no {', '.join(missing)}. Run `azd up` in the repo root first.")
    e = os.environ
    project_id = (f"/subscriptions/{e['AZURE_SUBSCRIPTION_ID']}/resourceGroups/{e['AZURE_RESOURCE_GROUP']}"
                  f"/providers/Microsoft.CognitiveServices/accounts/{e['STARK_FOUNDRY_ACCOUNT']}"
                  f"/projects/{e['STARK_FOUNDRY_PROJECT']}")
    values = {   # the same names the root infra/azd/main.bicep outputs for the azure.ai.* hosts
        "AZURE_SUBSCRIPTION_ID": e["AZURE_SUBSCRIPTION_ID"],
        "AZURE_RESOURCE_GROUP": e["AZURE_RESOURCE_GROUP"],
        "AZURE_LOCATION": e["AZURE_LOCATION"],
        "AZURE_AI_ACCOUNT_NAME": e["STARK_FOUNDRY_ACCOUNT"],
        "AZURE_AI_PROJECT_NAME": e["STARK_FOUNDRY_PROJECT"],
        "AZURE_AI_PROJECT_ID": project_id,
        "AZURE_AI_PROJECT_ENDPOINT": e["STARK_PROJECT_ENDPOINT"],
        "FOUNDRY_PROJECT_ENDPOINT": e["STARK_PROJECT_ENDPOINT"],
        "STARK_PROJECT_ENDPOINT": e["STARK_PROJECT_ENDPOINT"],
        "STARK_CHAT_MODEL": e["STARK_CHAT_MODEL"],
    }

    if azd("env", "select", ENV_NAME, check=False).returncode != 0:
        azd("env", "new", ENV_NAME, "--subscription", e["AZURE_SUBSCRIPTION_ID"],
            "--location", e["AZURE_LOCATION"], "--no-prompt")
    for key, value in values.items():
        azd("env", "set", key, value)
    print(f"azd environment '{ENV_NAME}' in {HARNESS.relative_to(ROOT)} is ready ({len(values)} values).")


if __name__ == "__main__":
    main()
