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
_project = None


def credential():
    global _credential
    if _credential is None:
        from azure.identity import DefaultAzureCredential
        _credential = DefaultAzureCredential()
    return _credential


def project():
    """The `AIProjectClient` (agents, datasets, evaluations, connections, telemetry)."""
    global _project
    if _project is None:
        from azure.ai.projects import AIProjectClient
        _project = AIProjectClient(endpoint=cfg("STARK_PROJECT_ENDPOINT"), credential=credential())
    return _project


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
