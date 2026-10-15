"""Shared helpers for the STARK notebooks: config, Foundry clients, KQL with retry, small printers."""
from __future__ import annotations

import os
import time
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

REQUIRED = ["STARK_PROJECT_ENDPOINT", "STARK_CHAT_MODEL", "STARK_JUDGE_MODEL", "STARK_FAST_MODEL"]


def cfg(name: str, default: str | None = None) -> str:
    """Read a setting from .env / the environment; fail with a hint instead of a KeyError."""
    value = os.environ.get(name, default)
    if value is None or value == "":
        raise SystemExit(f"{name} is not set. Run `azd up` (it writes .env) or copy .env.example to .env.")
    return value


def check_env() -> dict[str, str]:
    """Return the required settings; raise a friendly error when something is missing."""
    return {k: cfg(k) for k in REQUIRED}


_credential = None
_projects: dict[bool, object] = {}


def credential():
    global _credential
    if _credential is None:
        from azure.identity import DefaultAzureCredential
        _credential = DefaultAzureCredential()
    return _credential


def project(preview: bool = False):
    """The `AIProjectClient` (agents, datasets, evaluations, connections, telemetry).

    `preview=True` opts in to preview operations such as `project.beta.skills` (chapter 07).
    """
    if preview not in _projects:
        from azure.ai.projects import AIProjectClient
        kwargs = {"allow_preview": True} if preview else {}
        _projects[preview] = AIProjectClient(endpoint=cfg("STARK_PROJECT_ENDPOINT"), credential=credential(), **kwargs)
    return _projects[preview]


def openai_client(**kwargs):
    """OpenAI client bound to the project (Responses, Conversations, Evals, Vector stores).

    `agent_name="..."` binds it to one agent, so `responses.create(...)` talks to that agent.
    """
    return project().get_openai_client(**kwargs)


def model(kind: str = "chat") -> str:
    """Deployment name for 'chat' | 'judge' | 'fast' | 'embedding'."""
    return cfg({"chat": "STARK_CHAT_MODEL", "judge": "STARK_JUDGE_MODEL",
                "fast": "STARK_FAST_MODEL", "embedding": "STARK_EMBEDDING_MODEL"}[kind])


def kql(query: str, hours: float = 1, workspace_id: str | None = None):
    """Run a KQL query on the Log Analytics workspace behind Application Insights; returns a DataFrame."""
    import pandas as pd
    from azure.monitor.query import LogsQueryClient, LogsQueryStatus

    client = LogsQueryClient(credential())
    res = client.query_workspace(workspace_id or cfg("STARK_LOG_WORKSPACE_ID"), query,
                                 timespan=timedelta(hours=hours))
    if res.status != LogsQueryStatus.SUCCESS:
        raise RuntimeError(f"KQL failed: {res.partial_error}")
    table = res.tables[0]
    return pd.DataFrame(table.rows, columns=list(table.columns))


def kql_wait(query: str, hours: float = 1, tries: int = 12, delay: int = 30, min_rows: int = 1):
    """Like kql(), but retries: telemetry takes a few minutes to arrive in Log Analytics."""
    df = None
    for attempt in range(1, tries + 1):
        try:
            df = kql(query, hours)
            if len(df) >= min_rows:
                return df
        except Exception as exc:  # noqa: BLE001 - table may not exist yet on a fresh workspace
            print(f"  attempt {attempt}: {exc}")
        print(f"  waiting for telemetry ({attempt}/{tries})...")
        time.sleep(delay)
    return df


def banner(text: str) -> None:
    print(f"\n=== {text} ===")


def show_output(response) -> None:
    """Print the id, model and text of a Responses API result."""
    print(f"id={response.id}  model={getattr(response, 'model', '?')}")
    print(response.output_text)


def sh(command: str) -> str:
    """Run a shell command (azd, az, python scripts), print and return its output."""
    import subprocess
    proc = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=ROOT)
    out = (proc.stdout + proc.stderr).strip()
    print(out)
    if proc.returncode != 0:
        print(f"[exit code {proc.returncode}]")
    return out


def agent_ref(agent) -> dict:
    """`extra_body` that points a response at an agent (name or agent object)."""
    name = getattr(agent, "name", agent)
    return {"agent_reference": {"name": name, "type": "agent_reference"}}


def ask_agent(agent, text, conversation: str | None = None, approve=None, oai=None, max_rounds: int = 5):
    """Send one message to an agent and answer MCP approval requests.

    `approve(item) -> bool` decides each `mcp_approval_request` (default: deny, which is the safe choice).
    Returns the final response.
    """
    oai = oai or openai_client()
    extra = agent_ref(agent)
    kwargs = {"conversation": conversation} if conversation else {}
    resp = oai.responses.create(input=text, extra_body=extra, **kwargs)
    for _ in range(max_rounds):
        requests_ = [i for i in resp.output if i.type == "mcp_approval_request"]
        if not requests_:
            break
        decisions = []
        for item in requests_:
            ok = bool(approve(item)) if approve else False
            print(f"  approval request: {item.server_label}.{getattr(item, 'name', '?')}({getattr(item, 'arguments', '')}) -> {'APPROVED' if ok else 'DENIED'}")
            decisions.append({"type": "mcp_approval_response", "approve": ok, "approval_request_id": item.id})
        resp = oai.responses.create(input=decisions, previous_response_id=resp.id, extra_body=extra)
    return resp


def tool_calls(resp) -> list[str]:
    """Names of the tool calls in a response (function, MCP, code interpreter, search, ...)."""
    names = []
    for item in resp.output:
        if item.type == "message":
            continue
        names.append(f"{item.type}:{getattr(item, 'name', '') or getattr(item, 'server_label', '')}".rstrip(":"))
    return names


def delete_agent(name: str) -> None:
    """Delete every version of an agent (ignore errors: it may not exist)."""
    try:
        for v in list(project().agents.list_versions(agent_name=name)):
            project().agents.delete_version(agent_name=name, agent_version=v.version)
        print(f"deleted agent {name}")
    except Exception as exc:  # noqa: BLE001
        print(f"skip {name}: {type(exc).__name__}")


# ---------------------------------------------------------------- evaluations
def wait_eval_run(eval_id: str, run_id: str, oai=None, every: int = 5, timeout: int = 1800):
    """Poll an evaluation run until it ends; raise unless it completed."""
    oai = oai or openai_client()
    t0 = time.time()
    while True:
        run = oai.evals.runs.retrieve(run_id=run_id, eval_id=eval_id)
        if run.status in ("completed", "failed", "canceled"):
            break
        if time.time() - t0 > timeout:
            raise TimeoutError(f"evaluation run {run_id} still {run.status} after {timeout}s")
        print(f"  {run.status} ...")
        time.sleep(every)
    if run.status != "completed":
        raise RuntimeError(f"evaluation run ended as {run.status}: {getattr(run, 'error', None)}")
    return run


def _d(obj):
    """Plain dict from an SDK model, a dict or None."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    return obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)


def eval_scores(eval_id: str, run_id: str, oai=None):
    """One row per (item, evaluator): criterion, passed, score, reason, query."""
    import pandas as pd
    oai = oai or openai_client()
    rows = []
    for item in oai.evals.runs.output_items.list(run_id=run_id, eval_id=eval_id):
        item = _d(item)
        source = _d(item.get("datasource_item"))
        for res in item.get("results") or []:
            res = _d(res)
            rows.append({"query": str(source.get("query", source.get("messages", "")))[:70], "criterion": res.get("name"),
                         "passed": res.get("passed"), "score": res.get("score"), "reason": str(res.get("reason", ""))[:110]})
    return pd.DataFrame(rows)


def pass_rates(run) -> dict[str, float]:
    """Pass rate per evaluator from a completed run."""
    out = {}
    for entry in _d(run).get("per_testing_criteria_results") or []:
        entry = _d(entry)
        name = entry.get("name") or entry.get("testing_criteria")
        total = (entry.get("passed") or 0) + (entry.get("failed") or 0)
        out[name] = round((entry.get("passed") or 0) / total, 2) if total else float("nan")
    return out


def assert_pass_rate(run, minimum: float = 0.8) -> None:
    """CI-style quality gate: raise when any evaluator's pass rate is below `minimum`."""
    rates = pass_rates(run)
    low = {k: v for k, v in rates.items() if not v >= minimum}
    print("pass rates:", rates)
    if low:
        raise AssertionError(f"quality gate failed (< {minimum}): {low}")
    print(f"quality gate passed (>= {minimum})")
