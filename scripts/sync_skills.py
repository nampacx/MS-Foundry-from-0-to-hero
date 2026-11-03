"""azd predeploy hook: copy files the hosted agents need into their projects (chapters 07, 09, 15 and 16).

- skills/            -> src/jarvis-hosted/skills and src/invoice-workflow/skills (direct skill injection),
                        src/jarvis-skills/skills (loaded on demand by SkillsProvider),
                        src/jarvis-harness/skills (published as Foundry skills by azd, chapter 15)
- data/docs/*.pdf    -> src/invoice-workflow/data/docs (the sample invoices the workflow reads)
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fresh_copy(src: Path, dst: Path, pattern: str | None = None) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    if pattern is None:
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))   # skill scripts: no bytecode in the archive
    else:
        dst.mkdir(parents=True)
        for f in src.glob(pattern):
            shutil.copy2(f, dst / f.name)


for agent in ("jarvis-hosted", "jarvis-skills", "invoice-workflow", "jarvis-harness"):
    dst = ROOT / "src" / agent / "skills"
    fresh_copy(ROOT / "skills", dst)
    print(f"Copied {sum(1 for _ in dst.rglob('SKILL.md'))} skill(s) to {dst}")

invoices = ROOT / "src" / "invoice-workflow" / "data" / "docs"
fresh_copy(ROOT / "data" / "docs", invoices, "invoice-*.pdf")
print(f"Copied {sum(1 for _ in invoices.glob('*.pdf'))} invoice(s) to {invoices}")
