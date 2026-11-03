"""Helpers for chapter 17: the A2A capstone (preview).

Show what came back over A2A, and ask the orchestrator while its new role assignment propagates. Each turn is shown
as Markdown: the prompt, the whole answer and a check table. The notebook calls these; read them here.
"""
from __future__ import annotations

import time

from stark_harness import show_turn, verdict
from stark_helpers import answer_text, ask_agent, messages, tool_calls

__all__ = ["show_a2a_replies", "ask_orchestrator"]


# ---------------------------------------------------------------- section 3: a reply over A2A
def show_a2a_replies(agent_name: str, question: str, replies: list) -> None:
    """Show the text of every A2A `StreamResponse`, joined, with the payload kinds (message, task, ...) as a check."""
    from a2a.helpers import get_stream_response_text
    texts = [get_stream_response_text(r) for r in replies]
    answer = "\n\n".join(t for t in texts if t) or "(no text)"
    show_turn(f"{agent_name} over A2A", question, answer, {
        "replies": str(len(replies)),
        "payload": ", ".join(f"`{r.WhichOneof('payload')}`" for r in replies) or "none",
        "last verdict keyword": f"`{verdict(answer)}`",
    })


# ---------------------------------------------------------------- section 5: the whole system
def ask_orchestrator(agent_name: str, question: str, conversation_id: str, tries: int = 3, wait_s: int = 45) -> None:
    """Ask the orchestrator; retry while the role assignment propagates (403), then show the turn and its tool calls."""
    for attempt in range(1, tries + 1):
        try:
            response = ask_agent(agent_name, question, conversation=conversation_id)
            break
        except Exception as exc:
            print(f"attempt {attempt} of {tries}: {type(exc).__name__}: {exc}")
            if attempt == tries:
                raise
            time.sleep(wait_s)
    calls = tool_calls(response)
    final = (messages(response) or [""])[-1]
    show_turn(agent_name, question, answer_text(response), {
        "tool calls": ", ".join(f"`{c}`" for c in calls) or "none",
        "MCP call": "yes" if any(c.startswith("mcp_call") for c in calls) else "no",
        "item type that names A2A": "yes" if any("a2a" in c.lower() for c in calls) else "no",
        "last verdict keyword (final message)": f"`{verdict(final)}`",
    })
