"""Delete everything the workshop created: `azd down --purge` (Foundry accounts are soft-deleted, so purge)."""
import shutil
import subprocess
import sys

azd = shutil.which("azd") or "azd"
sys.exit(subprocess.call([azd, "down", "--purge", "--force"]))
