"""Helpers for chapters 04 to 09: show a reply and check which tools and skills it used.

Show one turn as Markdown (the prompt, the tool calls, the whole answer, the checks), find the stark-escalation
markers in the final message, and list the skills a hosted agent loaded. The notebooks call these; read them here.
"""
from __future__ import annotations

import json
import re

from IPython.display import Markdown, display

from stark_helpers import answer_text, final_message


# ---------------------------------------------------------------- chapters 04 to 09: show one turn
def tool_items(response) -> list[str]:
    """Every output item that is not a message or reasoning: function calls with their arguments, other tools by type."""
    found = []
    for item in response.output:
        if item.type in ("message", "reasoning"):
            continue
        if item.type == "function_call":
            found.append(f"`{item.name}` {item.arguments}")
        else:
            label = getattr(item, "name", None) or getattr(item, "server_label", None)
            found.append(f"`{item.type}`" + (f" ({label})" if label else ""))
    return found


def mcp_calls(response) -> list[str]:
    """Names of the MCP tools the agent called (`mcp_call` items), in order."""
    return [item.name for item in response.output if item.type == "mcp_call"]


def show_reply(prompt: str, response, checks: dict[str, str] | None = None, *, to: str | None = None,
               instructions: str | None = None, inputs: dict | None = None) -> None:
    """Render one turn as Markdown: the prompt (and structured inputs or folded instructions), the tool calls,
    the whole answer and the checks."""
    md = [f"**Prompt sent to `{to}`**" if to else "**Prompt**", ""] + [f"> {line}  " for line in prompt.strip().splitlines()]
    if inputs is not None:
        md += ["", f"`structured_inputs`: `{json.dumps(inputs, ensure_ascii=False)}`"]
    if instructions:
        md += ["", f"<details><summary>Instructions ({len(instructions)} characters)</summary>", "",
               "````text", instructions, "````", "", "</details>"]
    calls = tool_items(response)
    md += ["", "**Tool calls:** " + (", ".join(calls) if calls else "none")]
    md += ["", "**Answer**", "", answer_text(response) or "_(no message)_"]
    if checks:
        md += ["", "**Check**", "", "| | |", "|---|---|"] + [f"| {name} | {value} |" for name, value in checks.items()]
    display(Markdown("\n".join(md)))


def _judge(found, expected) -> str:
    """`yes` / `no` (or the value), plus the expected one with ✅ / ❌ when there is a right answer."""
    shown = ("yes" if found else "no") if isinstance(found, bool) else (f"`{found}`" if found else "none")
    if expected is None:
        return shown
    want = ("yes" if expected else "no") if isinstance(expected, bool) else f"`{expected}`"
    return f"{shown} (expected {want}) {'✅' if found == expected else '❌'}"


# ---------------------------------------------------------------- chapters 07 and 09: the stark-escalation markers
def escalation_markers(response) -> dict:
    """The markers stark-escalation leaves in the final message: `Severity: <level>` first, and a floor (version 2)."""
    final = final_message(response)
    level = re.match(r"\W*severity:\W*(\w+)", final, re.I)
    return {"severity first": bool(re.match(r"\W*severity:", final, re.I)),
            "severity": level.group(1).lower() if level else None,
            "names a floor": "floor" in final.lower()}


def escalation_checks(response, expected: dict | None = None) -> dict[str, str]:
    """The markers as check-table rows; markers in `expected` get ✅ / ❌, the others plain `yes` / `no`."""
    expected = expected or {}
    return {f"{marker} (final message)": _judge(found, expected.get(marker))
            for marker, found in escalation_markers(response).items()}


# ---------------------------------------------------------------- chapter 09: skills on demand and the status tool
def loaded_skills(response) -> list[str]:
    """The skills the model loaded: the `skill_name` argument of every `load_skill` call (Agent Framework SkillsProvider)."""
    names = []
    for item in response.output:
        if item.type == "function_call" and item.name == "load_skill":
            try:
                names.append(json.loads(item.arguments).get("skill_name", "?"))
            except (TypeError, ValueError):
                names.append(str(item.arguments))
    return names


def skill_checks(response, expected_skill: str) -> dict[str, str]:
    """Check-table row: did the model load the skill the question needs?"""
    loaded = loaded_skills(response)
    shown = ", ".join(f"`{name}`" for name in loaded) or "none"
    return {"skills loaded": f"{shown} (expected `{expected_skill}`) {'✅' if expected_skill in loaded else '❌'}"}


def status_checks(response) -> dict[str, str]:
    """Check-table row: does the final message carry the arc reactor's 3.0 GW from the WORKSHOP table in main.py?"""
    return {"reports `3.0 GW` (final message)": _judge("3.0 GW" in final_message(response), True)}
