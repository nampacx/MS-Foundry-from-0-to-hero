"""azd postdeploy hook: create the Foundry project connection `stark-mcp` for our MCP Function.

Foundry agents must not carry secrets in their definition, so the Functions system key (mcp_extension) goes into a
project connection (custom-keys, header x-functions-key) and agents reference it by name. Needs `az login` and the azd
Foundry extension (`azd extension install microsoft.foundry`). Failure here never fails the deployment: run it again by hand.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time

AZ = shutil.which("az") or "az"
AZD = shutil.which("azd") or "azd"
CONNECTION = "stark-mcp"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> int:
    app, rg, url, endpoint = (os.environ.get(k, "") for k in
                              ("STARK_MCP_FUNCTION", "AZURE_RESOURCE_GROUP", "STARK_MCP_URL", "STARK_PROJECT_ENDPOINT"))
    if not (app and url):
        print("MCP Function not deployed (STARK_ENABLE_MCP=false?); skipping connection.")
        return 0
    key = ""
    for _ in range(10):  # the system key exists a few seconds after the first code deployment
        proc = run([AZ, "functionapp", "keys", "list", "-g", rg, "-n", app, "-o", "json"])
        if proc.returncode == 0:
            key = (json.loads(proc.stdout or "{}").get("systemKeys") or {}).get("mcp_extension", "")
        if key:
            break
        time.sleep(10)
    if not key:
        print("Could not read the mcp_extension key yet; re-run: python scripts/connect_mcp.py")
        return 0
    proc = run([AZD, "ai", "project", "set", endpoint])
    if proc.returncode != 0:
        print("Could not select the project (is the azd Foundry extension installed?):", (proc.stderr or proc.stdout).strip())
        return 0
    proc = run([AZD, "ai", "connection", "create", CONNECTION, "--kind", "remote-tool", "--target", url,
                "--auth-type", "custom-keys", "--custom-key", f"x-functions-key={key}"])
    if proc.returncode != 0:
        print("Connection not created (already exists, or the azd Foundry extension is missing):")
        print((proc.stderr or proc.stdout).strip())
        print("Manual command: azd ai connection create stark-mcp --kind remote-tool --target <STARK_MCP_URL> "
              "--auth-type custom-keys --custom-key \"x-functions-key=<mcp_extension key>\"")
    else:
        print(f"Created project connection '{CONNECTION}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
