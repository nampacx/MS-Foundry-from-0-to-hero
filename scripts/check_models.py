"""List which models from infra/config/stark.json exist in a region (needs `az login`).

Usage: python scripts/check_models.py [location]      (default: swedencentral)
Foundry model names and versions change often: run this before `azd up` and edit stark.json if a model is missing.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "infra" / "config" / "stark.json").read_text(encoding="utf-8"))


def main() -> None:
    location = sys.argv[1] if len(sys.argv) > 1 else "swedencentral"
    az = shutil.which("az") or "az"
    proc = subprocess.run([az, "cognitiveservices", "model", "list", "-l", location, "-o", "json"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"Could not list models (az login? permission?):\n{proc.stderr or proc.stdout}")
    index: dict[str, set[str]] = {}
    for m in json.loads(proc.stdout):
        index.setdefault(m["model"]["name"].lower(), set()).add(m["model"]["version"])
    print(f"Models in {location}:")
    for m in CONFIG["models"]:
        versions = index.get(m["model"].lower(), set())
        if not versions:
            status = "NOT FOUND in this region/subscription"
        elif m["version"] in versions:
            status = f"OK (version {m['version']})"
        else:
            status = f"VERSION MISMATCH: declared {m['version']}, available {', '.join(sorted(versions))}"
        print(f"  {m['name']:<24} {m['model']:<24} {status}")


if __name__ == "__main__":
    main()
