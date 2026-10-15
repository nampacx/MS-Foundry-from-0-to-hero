"""Let a hosted agent use Foundry Tools (Document Intelligence, Content Understanding, Vision), chapter 15.

A hosted agent does not run as you. Locally your user has the *Cognitive Services User* role on the Foundry resource
(rbac.bicep assigns it); the deployed agent does not, so its Document Intelligence calls fail with `PermissionDenied`.
Two identities matter: the project's shared agent identity (used while the agent is unpublished) and the agent's own
instance identity (used once it is published). This script grants the role to both.

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
    account, project = os.environ.get("STARK_FOUNDRY_ACCOUNT"), os.environ.get("STARK_FOUNDRY_PROJECT")
    endpoint = os.environ.get("STARK_PROJECT_ENDPOINT")
    if not all((sub, rg, account, project, endpoint)):
        sys.exit("Run `azd up` first (it writes .env).")
    try:
        agent = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential()).agents.get(agent_name=agent_name)
    except Exception as exc:  # noqa: BLE001
        print(f"Agent '{agent_name}' not found ({type(exc).__name__}). Deploy it first: azd deploy {agent_name}")
        return 1

    env = {**os.environ, "MSYS_NO_PATHCONV": "1"}  # keep Git Bash from rewriting the /subscriptions/... paths
    scope = f"/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{account}"
    project_url = f"https://management.azure.com{scope}/projects/{project}?api-version=2025-06-01"
    shared = subprocess.run([AZ, "rest", "--method", "get", "--url", project_url, "--query",
                             "properties.agentIdentity.agentIdentityId", "-o", "tsv"],
                            capture_output=True, text=True, env=env).stdout.strip()
    identities = {
        "shared project agent identity": shared,
        f"'{agent_name}' instance identity": agent.instance_identity.principal_id,
    }

    failed = False
    for label, principal in identities.items():
        if not principal:
            print(f"Could not find the {label}.")
            failed = True
            continue
        out = subprocess.run([AZ, "role", "assignment", "create", "--assignee-object-id", principal,
                              "--assignee-principal-type", "ServicePrincipal", "--role", ROLE, "--scope", scope, "-o", "none"],
                             capture_output=True, text=True, env=env)
        if out.returncode == 0 or "already exists" in (out.stderr or ""):
            print(f"'{ROLE}' is assigned to the {label} ({principal}) on {account}.")
        else:
            print(f"Could not assign the role to the {label}:")
            print(out.stderr)
            failed = True
    if not failed:
        print("Allow a minute or two for the role to take effect.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "invoice-workflow"))
