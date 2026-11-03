"""Helpers for chapter 16: workflows with Microsoft Agent Framework.

Run a workflow, collect its streamed events and show the run as Markdown: the task, what each step said, the answer
and a small check table. The notebook keeps the agents, executors and builders (the topology); the plumbing is here.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

from IPython.display import Markdown, display

from stark_helpers import openai_client

__all__ = ["INVOICE_VERDICTS", "BOARD_DECISION", "collect_run", "last_keyword", "render_run", "show_run", "show_board",
           "show_route", "show_briefing", "show_outputs", "run_handoff", "ask_hosted"]
INVOICE_VERDICTS = r"APPROVE|REJECT|NEEDS HUMAN REVIEW"   # the last line of the invoice-review checklist
BOARD_DECISION = r"DECISION:\s*(?:approve|reject)"          # how the review board's security officer ends


# ---------------------------------------------------------------- collecting a run
@dataclass
class Step:
    """One stretch of streamed text from one agent: `kind` is "step" (intermediate) or "final" (workflow output)."""
    author: str
    kind: str
    text: str = ""
    last_chunk_s: float = 0.0


@dataclass
class WorkflowRun:
    """What one streamed run produced: the agents' steps, plain-text outputs of code steps, the executors in order."""
    task: str
    steps: list[Step] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    path: list[str] = field(default_factory=list)
    seconds: float = 0.0


def _text(data) -> str | None:
    """Plain text of a workflow output: a string, or anything with `.text`; None for other shapes (message lists)."""
    if isinstance(data, str):
        return data
    text = getattr(data, "text", None)
    return text if isinstance(text, str) else None


async def collect_run(workflow, task: str, group_by_author: bool = False) -> WorkflowRun:
    """Run a workflow with streaming and collect its events. `group_by_author` merges interleaved parallel streams."""
    from agent_framework import AgentResponseUpdate
    run, started = WorkflowRun(task), time.time()
    async for event in workflow.run(task, stream=True):
        data = event.data
        if event.type == "executor_invoked" and event.executor_id not in run.path:
            run.path.append(event.executor_id)
        elif event.type in ("output", "intermediate") and isinstance(data, AgentResponseUpdate):
            if not data.text:
                continue
            kind = "final" if event.type == "output" else "step"
            candidates = run.steps if group_by_author else run.steps[-1:]   # parallel streams interleave
            step = next((s for s in reversed(candidates) if (s.author, s.kind) == (data.author_name, kind)), None)
            if step is None:
                step = Step(data.author_name, kind)
                run.steps.append(step)
            step.text += data.text
            step.last_chunk_s = time.time() - started
        elif event.type == "output" and _text(data):
            run.outputs.append(_text(data))
    run.seconds = time.time() - started
    return run


# ---------------------------------------------------------------- showing a run
def last_keyword(text: str, pattern: str = INVOICE_VERDICTS) -> str | None:
    """The last match of `pattern` in the text: agents explain first and end with the verdict."""
    found = re.findall(pattern, text or "")
    return found[-1] if found else None


def _block(text: str) -> list[str]:
    """Markdown for one step's text: JSON (structured output) as a code block, anything else as it is."""
    try:
        return ["```json", json.dumps(json.loads(text), indent=2), "```"]
    except ValueError:
        return [text.strip()]


def _quote(text: str) -> list[str]:
    """A prompt as a Markdown quote, line by line."""
    return [f"> {line}  " for line in text.strip().splitlines()]


def _table(checks: dict[str, str]) -> list[str]:
    """A two-column check table."""
    return ["", "**Check**", "", "| | |", "|---|---|"] + [f"| {k} | {v} |" for k, v in checks.items()]


def _expected(got, expected) -> str:
    """`got` next to the expected value (one value or a tuple of acceptable ones), with ✅ / ❌."""
    options = expected if isinstance(expected, tuple) else (expected,)
    shown = " or ".join(f"`{o}`" for o in options)
    return f"`{got}` (expected {shown}) {'✅' if got in options else '❌'}"


def render_run(run: WorkflowRun, checks: dict[str, str]) -> None:
    """Show a collected run as Markdown: the task, every step in order, the answer, then the checks."""
    md = ["**Task**", ""] + _quote(run.task)
    for step in run.steps:
        md += ["", f"**{'final' if step.kind == 'final' else 'step'} · `{step.author}`**", ""] + _block(step.text)
    for out in run.outputs:
        md += ["", "**Output (code step)**", "", out.strip()]
    display(Markdown("\n".join(md + _table(checks))))


async def show_run(workflow, task: str, expected=None, verdict_from: str = "reviewer",
                   verdict_pattern: str = INVOICE_VERDICTS) -> None:
    """Run a workflow and show every step; check the last verdict keyword of the step `verdict_from`."""
    run = await collect_run(workflow, task)
    said = "\n".join(s.text for s in run.steps if s.author == verdict_from)
    got = last_keyword(said, verdict_pattern)
    checks = {"steps": " → ".join(f"`{s.author}`" for s in run.steps) or "none",
              f"verdict of `{verdict_from}`": _expected(got, expected) if expected else f"`{got}`",
              "time": f"{run.seconds:.0f}s"}
    render_run(run, checks)


async def show_board(workflow, question: str) -> None:
    """Run the group chat and show every turn; the security officer ends with DECISION: approve or reject."""
    await show_run(workflow, question, verdict_from="security", verdict_pattern=BOARD_DECISION)


async def show_route(workflow, task: str, expected_path: str | None = None) -> None:
    """Run the threshold router and show the facts it read, the answer and the path the edges chose."""
    run = await collect_run(workflow, task)
    path = " -> ".join(run.path)
    checks = {"path": f"`{path}`" + (f" (expected `{expected_path}`) {'✅' if path == expected_path else '❌'}"
                                     if expected_path else ""),
              "time": f"{run.seconds:.0f}s"}
    render_run(run, checks)


async def show_briefing(workflow, task: str) -> None:
    """Run the concurrent briefing: each specialist's report, J.A.R.V.I.S.'s merge and when each one finished."""
    run = await collect_run(workflow, task, group_by_author=True)
    checks = {f"`{s.author}` finished after": f"{s.last_chunk_s:.0f}s" for s in run.steps}
    checks["whole run"] = f"{run.seconds:.0f}s"
    render_run(run, checks)


def show_outputs(task: str, outputs: list) -> None:
    """Show the outputs of a non-streamed run (`result.get_outputs()`) as Markdown, one paragraph each."""
    texts = [_text(o) if _text(o) is not None else str(o) for o in outputs]
    md = ["**Task**", ""] + _quote(task) + ["", f"**Outputs** ({len(texts)})", ""]
    md += ["\n\n".join(t.strip() for t in texts) or "none"]
    display(Markdown("\n".join(md)))


# ---------------------------------------------------------------- section 4: handoff with scripted user turns
async def run_handoff(workflow, user_turns: list[str]) -> None:
    """Play scripted user turns through a handoff workflow and show who answered each one."""
    from agent_framework import AgentResponseUpdate
    from agent_framework.orchestrations import HandoffAgentUserRequest
    turns = list(user_turns)
    transcript: list[list[str]] = []      # [speaker, text], in order
    answered_by: list[list] = []          # [user message, agents that spoke after it]

    def user_says(text: str) -> None:
        """Add a user turn to the transcript and the check table."""
        transcript.append(["user", text])
        answered_by.append([text, []])

    user_says(turns.pop(0))
    responses = None
    while True:
        pending = []
        if responses is None:
            stream = workflow.run(transcript[0][1], stream=True)
        else:
            stream = workflow.run(responses=responses, stream=True)
        async for event in stream:
            data = event.data
            if event.type == "request_info" and isinstance(data, HandoffAgentUserRequest):
                pending.append(event)   # the workflow pauses and waits for the user
            elif event.type == "output" and isinstance(data, AgentResponseUpdate) and data.text:
                if transcript[-1][0] != data.author_name:
                    transcript.append([data.author_name, ""])
                    answered_by[-1][1].append(data.author_name)
                transcript[-1][1] += data.text
        if not pending:
            break
        if turns:
            user_says(turns.pop(0))
            responses = {p.request_id: HandoffAgentUserRequest.create_response(transcript[-1][1]) for p in pending}
        else:   # no scripted turn left: end the chat
            responses = {p.request_id: HandoffAgentUserRequest.terminate() for p in pending}
    md = []
    for speaker, text in transcript:
        md += [f"**{speaker}**", ""] + (_quote(text) if speaker == "user" else [text.strip()]) + [""]
    md += ["**Check**", "", "| user message | answered by |", "|---|---|"]
    md += [f"| {m} | {', '.join(f'`{s}`' for s in who) or 'nobody'} |" for m, who in answered_by]
    display(Markdown("\n".join(md)))


# ---------------------------------------------------------------- section 6: hosted workflows
def ask_hosted(agent_name: str, text: str) -> None:
    """One request to a hosted agent through a bound client, in a conversation it deletes afterwards; show the answer."""
    from stark_harness import answer_text
    bound = openai_client(agent_name=agent_name)
    conversation = bound.conversations.create()
    started = time.time()
    try:
        response = bound.responses.create(conversation=conversation.id, input=text)
    finally:
        bound.conversations.delete(conversation.id)
    md = [f"**Prompt sent to `{agent_name}`**", ""] + _quote(text) + ["", "**Answer**", "", answer_text(response)]
    display(Markdown("\n".join(md + _table({"time": f"{time.time() - started:.0f}s"}))))
