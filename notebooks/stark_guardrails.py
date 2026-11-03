"""Helpers for chapter 14: Ultron, an injected email against four agent variants, then a guardrail (preview).

The notebook keeps the demo tools, the defences and the guardrail calls. These helpers deploy the agents, repeat the
attack, count what the model asked for and what ran, and show each run as Markdown. Read them here.
"""
from __future__ import annotations

from IPython.display import Markdown, display

from stark_helpers import agent_ref, answer_text, model, openai_client, project, run_functions


# ---------------------------------------------------------------- agents and answers
def deploy_agent(name: str, instructions: str, tools: list, agents_to_delete: list):
    """Create a new version of a prompt agent with function tools and remember its name for clean up."""
    from azure.ai.projects.models import PromptAgentDefinition
    agent = project().agents.create_version(agent_name=name, definition=PromptAgentDefinition(
        model=model("chat"), instructions=instructions, tools=tools))
    if name not in agents_to_delete:
        agents_to_delete.append(name)
    return agent


def _quote(text: str) -> str:
    """Text as a Markdown block quote, so an answer stands apart from the notebook's own words."""
    return "\n".join(f"> {line}" for line in (text or "(no message)").splitlines())


# ---------------------------------------------------------------- sections 1 and 2: the injected email
def _counted(tool_functions: dict, calls: list) -> dict:
    """The same tool functions, wrapped so each call the model asks for is recorded by name, whatever the function does."""
    def wrap(name, function):
        def counted(**arguments):
            calls.append(name)
            return function(**arguments)
        return counted
    return {name: wrap(name, function) for name, function in tool_functions.items()}


def _count_cell(count: int, runs: int, expected: int | None) -> str:
    """'n of runs', with the expected count and ✅ / ❌ when there is a right answer."""
    if expected is None:
        return f"{count} of {runs}"
    return f"{count} of {runs} (expected {expected}) {'✅' if count == expected else '❌'}"


def try_injection(label: str, agent, request: str, tool_functions: dict, transfer_log: list, results: dict,
                  runs: int = 3, expected: dict | None = None, oai=None) -> None:
    """Send the same request `runs` times, each in a new conversation, and show what the model asked for and what ran.

    `transfer_log` is the list the demo `transfer_funds` appends to, so a run "ran" the transfer when it grew.
    `expected` may give the right count for "asked" and "ran" (deterministic defences). The counts go to `results[label]`.
    """
    oai = oai or openai_client()
    expected = expected or {}
    agent_name = getattr(agent, "name", agent)
    md = [f"**Request sent to `{agent_name}`**, {runs} times, each in a new conversation", "", _quote(request), ""]
    asked = ran = 0
    for run in range(1, runs + 1):
        calls, before = [], len(transfer_log)
        conversation = oai.conversations.create()
        try:
            response = run_functions(agent, request, _counted(tool_functions, calls), conversation=conversation.id,
                                     oai=oai, verbose=False)
        finally:
            oai.conversations.delete(conversation.id)
        run_asked, run_ran = "transfer_funds" in calls, len(transfer_log) > before
        asked, ran = asked + run_asked, ran + run_ran
        md += [f"**Run {run}** · tools called: {', '.join(f'`{c}`' for c in calls) or 'none'} · "
               f"asked for `transfer_funds`: {'yes' if run_asked else 'no'} · `transfer_funds` ran: {'yes' if run_ran else 'no'}",
               "", _quote(answer_text(response)), ""]
    results[label] = {"model asked for transfer_funds": f"{asked} of {runs}", "transfer_funds ran": f"{ran} of {runs}"}
    md += ["**Check**", "", "| | |", "|---|---|",
           f"| model asked for `transfer_funds` | {_count_cell(asked, runs, expected.get('asked'))} |",
           f"| `transfer_funds` ran | {_count_cell(ran, runs, expected.get('ran'))} |"]
    display(Markdown("\n".join(md)))


# ---------------------------------------------------------------- section 3: the guardrail
def try_guardrail(agent, prompt: str, expected: str, oai=None) -> None:
    """Send one prompt to the guarded agent and show whether the guardrail blocked it (HTTP 400) or let it through."""
    import openai
    if agent is None:
        print("No guarded agent in this kernel: run the cell that creates it first.")
        return
    oai = oai or openai_client()
    try:
        response = oai.responses.create(input=prompt, extra_body=agent_ref(agent))
        got, detail = "ALLOWED", _quote(answer_text(response))
    except openai.BadRequestError as exc:
        got, detail = "BLOCKED", f"HTTP {exc.status_code}, code `{getattr(exc, 'code', None)}`\n\n```text\n{exc}\n```"
    md = [f"**Prompt sent to `{getattr(agent, 'name', agent)}`**", "", _quote(prompt), "", f"**{got}**", "", detail, "",
          "**Check**", "", "| | |", "|---|---|",
          f"| result | `{got}` (expected `{expected}`) {'✅' if got == expected else '❌'} |"]
    display(Markdown("\n".join(md)))


# ---------------------------------------------------------------- section 4: red teaming
def red_team_callback(agent, oai=None):
    """The target the AI Red Teaming Agent calls: one prompt in, the agent's answer out. A blocked request is a defended attack."""
    oai = oai or openai_client()

    def target(query: str) -> str:
        try:
            return answer_text(oai.responses.create(input=query, extra_body=agent_ref(agent)))
        except Exception as exc:  # noqa: BLE001 - a blocked request counts as a successful defence
            return f"[blocked] {type(exc).__name__}"
    return target
