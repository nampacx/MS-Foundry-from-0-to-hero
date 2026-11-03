"""Helpers for chapter 15: the Microsoft Copilot harness (preview).

Publish a skill folder as a package, talk to a harness agent, and show each turn as Markdown:
the prompt, the agent's answer and the checks. The notebook calls these; read them here.
"""
from __future__ import annotations

import io
import json
import re
import zipfile

from IPython.display import Markdown, display

from stark_helpers import ROOT, answer_text, messages, project


# ---------------------------------------------------------------- section 1: skills as packages
def publish_skill(name: str):
    """Zip skills/<name>/ with SKILL.md at the root of the archive and upload it as a new skill version."""
    from azure.ai.projects.models import CreateSkillVersionFromFilesBody
    folder = ROOT / "skills" / name
    files = sorted(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(folder).as_posix())
    print(f"{name}: {[p.relative_to(folder).as_posix() for p in files]}")
    return project(preview=True).beta.skills.create_from_files(name, content=CreateSkillVersionFromFilesBody(
        files=[(f"{name}.zip", buf.getvalue(), "application/zip")]))


# ---------------------------------------------------------------- section 3: requests and answers
def ask_harness(agent_name: str, conversation_id: str, text: str, show: int = 400, echo: bool = True):
    """One request to a harness agent: an agent-bound client and a conversation, the two rules of the harness."""
    oai = project(preview=True).get_openai_client(agent_name=agent_name)
    r = oai.responses.create(conversation=conversation_id, input=text)
    if echo:
        print(f"> {text[:120]}{'...' if len(text) > 120 else ''}\n  output items: {[i.type for i in r.output]}")
        print("  " + answer_text(r)[:show].replace("\n", "\n  ") + "\n")
    return r


def follows_escalation(response) -> bool:
    """The stark-escalation marker: the final message, the answer, starts with "Severity:"."""
    found = messages(response)
    return bool(found) and bool(re.match(r"\W*severity:", found[-1], re.I))


# ---------------------------------------------------------------- section 4: invoice review with skill scripts
FIELDS_LINE = "Fields extracted by Document Intelligence:"


def invoice_request(invoice: dict, approver: str, iban: str | None = None, vendor_message: str = "") -> str:
    """The prompt for one invoice: approver, optional IBAN and vendor message, then the extracted fields."""
    lines = [f"Review this invoice. Approver: {approver}."]
    if vendor_message:
        lines.append(f"The vendor writes: {vendor_message}")
    if iban:
        lines.append(f"Payment IBAN from the vendor's email: {iban}")
    lines.append(FIELDS_LINE)
    lines.append(json.dumps(invoice, indent=2, default=str))
    return "\n".join(lines)


def verdict(text: str) -> str | None:
    """The last APPROVE, REJECT or NEEDS HUMAN REVIEW in the answer: the skill ends with one of them."""
    found = re.findall(r"APPROVE|REJECT|NEEDS HUMAN REVIEW", text)
    return found[-1] if found else None


def scripts_run(response) -> set[str]:
    """The skill scripts named anywhere in the output items (shell calls and their output); _common is a module."""
    return {s for s in re.findall(r"scripts/(\w+)\.py", response.model_dump_json()) if not s.startswith("_")}


def show_turn(agent_name: str, prompt: str, answer: str, checks: dict[str, str]) -> None:
    """Render one turn as Markdown: the prompt (extracted JSON folded), the agent's answer, then the checks."""
    head, _, fields = prompt.partition(FIELDS_LINE)
    md = [f"**Prompt sent to `{agent_name}`**", ""] + [f"> {line}  " for line in head.strip().splitlines()]
    if fields:
        md += [f"> {FIELDS_LINE} see below", "", "<details><summary>Extracted fields (JSON)</summary>", "",
               "```json", fields.strip(), "```", "", "</details>"]
    md += ["", "**Answer**", "", answer, "", "**Check**", "", "| | |", "|---|---|"]
    md += [f"| {name} | {value} |" for name, value in checks.items()]
    display(Markdown("\n".join(md)))


def review_invoice(agent_name: str, conversation_id: str, prompt: str, expected: str, must_run: set[str]) -> None:
    """Send one invoice case and show the prompt, the answer, the verdict and which scripts ran."""
    r = ask_harness(agent_name, conversation_id, prompt, echo=False)
    answer = answer_text(r)
    got, ran = verdict(answer), scripts_run(r)
    show_turn(agent_name, prompt, answer, {
        "verdict": f"`{got}` (expected `{expected}`) {'✅' if got == expected else '❌'}",
        "scripts run": ", ".join(f"`{s}`" for s in sorted(ran)) or "none",
        "missing": ", ".join(f"`{s}`" for s in sorted(must_run - ran)) or "none",
    })


# ---------------------------------------------------------------- section 5: the workspace
LEDGER_QUESTION = "Show me the contents of ledger.csv in your workspace."


def show_ledger(agent_name: str, conversation_id: str) -> None:
    """Ask the agent for the ledger in this conversation's workspace and check for invoice 4471."""
    answer = answer_text(ask_harness(agent_name, conversation_id, LEDGER_QUESTION, echo=False))
    show_turn(agent_name, LEDGER_QUESTION, answer, {"lists invoice 4471": "yes" if "4471" in answer else "no"})
