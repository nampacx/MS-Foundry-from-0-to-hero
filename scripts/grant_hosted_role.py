"""Give the signed-in user the Foundry Project Manager role on the project (needed to deploy hosted agents, chapter 09).

The role was renamed (Azure AI Project Manager -> Foundry Project Manager); the role id did not change, so we try both names.
Needs `az login` and permission to create role assignments (Owner / User Access Administrator on the resource group).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
AZ = shutil.which("az") or "az"


def az(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([AZ, *args], capture_output=True, text=True)


def main() -> int:
    sub, rg = os.environ.get("AZURE_SUBSCRIPTION_ID"), os.environ.get("AZURE_RESOURCE_GROUP")
    account, project = os.environ.get("STARK_FOUNDRY_ACCOUNT"), os.environ.get("STARK_FOUNDRY_PROJECT")
    if not all((sub, rg, account, project)):
        sys.exit("Run `azd up` first (it writes .env).")
    me = az("ad", "signed-in-user", "show", "--query", "id", "-o", "tsv")
    if me.returncode != 0:
        sys.exit(f"Cannot resolve the signed-in user:\n{me.stderr}")
    scope = (f"/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}/projects/{project}")
    for role in ("Foundry Project Manager", "Azure AI Project Manager"):
        out = az("role", "assignment", "create", "--assignee-object-id", me.stdout.strip(), "--assignee-principal-type", "User",
                 "--role", role, "--scope", scope, "-o", "json")
        if out.returncode == 0:
            print(f"Assigned '{role}' on {project}.")
            return 0
        if "already exists" in (out.stderr or ""):
            print(f"'{role}' is already assigned.")
            return 0
    print("Could not assign the role:\n" + out.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
