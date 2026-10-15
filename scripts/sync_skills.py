"""azd predeploy hook: copy skills/ into the hosted agent project so the container can load them (chapter 07/09)."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src, dst = ROOT / "skills", ROOT / "src" / "jarvis-hosted" / "skills"
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst)
print(f"Copied {sum(1 for _ in dst.rglob('SKILL.md'))} skill(s) to {dst}")
