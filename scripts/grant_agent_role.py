"""Let a hosted agent use Foundry Tools (Document Intelligence, Content Understanding, Vision), chapter 15.

A hosted agent runs under its OWN Entra identity, not yours. Locally your user has the *Cognitive Services User* role on the
Foundry resource (rbac.bicep assigns it); the deployed agent does not, so its Document Intelligence calls fail until you grant it.

Usage:  python scripts/grant_agent_role.py [agent-name]        (default: invoice-workflow)
Needs `az login` and permission to create role assignments on the resource group.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
AZ = shutil.which("az") or "az"
ROLE = "Cognitive Services User"


def main(agent_name: str) -> int:
    sub, rg = os.environ.get("AZURE_SUBSCRIPTION_ID"), os.environ.get("AZURE_RESOURCE_GROUP")
    account, endpoint = os.environ.get("STARK_FOUNDRY_ACCOUNT"), os.environ.get("STARK_PROJECT_ENDPOINT")
    if not all((sub, rg, account, endpoint)):
        sys.exit("Run `azd up` first (it writes .env).")
    try:
        agent = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential()).agents.get(agent_name=agent_name)
    except Exception as exc:  # noqa: BLE001
        print(f"Agent '{agent_name}' not found ({type(exc).__name__}). Deploy it first: azd deploy {agent_name}")
        return 1
    principal = agent.instance_identity.principal_id
    scope = f"/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}"
    out = subprocess.run([AZ, "role", "assignment", "create", "--assignee-object-id", principal, "--assignee-principal-type",
                          "ServicePrincipal", "--role", ROLE, "--scope", scope, "-o", "none"], capture_output=True, text=True,
                         env={**os.environ, "MSYS_NO_PATHCONV": "1"})
    if out.returncode == 0 or "already exists" in (out.stderr or ""):
        print(f"'{ROLE}' is assigned to '{agent_name}' ({principal}) on {account}. Allow a minute for it to take effect.")
        return 0
    print("Could not assign the role:\n" + out.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "invoice-workflow"))
