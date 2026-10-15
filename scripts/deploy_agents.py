"""Deploy declarative prompt agents from agents/*.yaml (chapter 08).

Usage:
    python scripts/deploy_agents.py --dry-run             # resolve ${VARS} and print what would be created
    python scripts/deploy_agents.py                       # create a new version of every agent in agents/
    python scripts/deploy_agents.py agents/jarvis.yaml    # only one file
    python scripts/deploy_agents.py --delete jarvis       # delete all versions of an agent

YAML fields: name, kind (prompt), description, model, instructions | instructions_file, tools[].
Tool types: code_interpreter, web_search, file_search (vector_store_ids), mcp (server_label, server_url,
project_connection_id, require_approval, allowed_tools), a2a (project_connection_id), function (name, description, parameters).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")


def substitute(value):
    """Replace ${VAR} in every string of a nested structure; fail loudly on unset variables."""
    if isinstance(value, str):
        def repl(m):
            name = m.group(1)
            if not os.environ.get(name):
                raise SystemExit(f"${{{name}}} is not set (see .env / .env.example)")
            return os.environ[name]
        return VAR.sub(repl, value)
    if isinstance(value, list):
        return [substitute(v) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v) for k, v in value.items()}
    return value


def load_spec(path: Path) -> dict:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    if spec.get("instructions_file"):
        spec["instructions"] = (path.parent / spec.pop("instructions_file")).read_text(encoding="utf-8").strip()
    for field in ("name", "model", "instructions"):
        if not spec.get(field):
            raise SystemExit(f"{path}: missing '{field}'")
    if spec.get("kind", "prompt") != "prompt":
        raise SystemExit(f"{path}: only kind: prompt is deployed by this script (hosted agents use azd, chapter 09)")
    return substitute(spec)


def build_tool(spec: dict):
    from azure.ai.projects import models as m

    t = spec["type"]
    if t == "code_interpreter":
        return m.CodeInterpreterTool()
    if t == "web_search":
        return m.WebSearchPreviewTool()
    if t == "file_search":
        return m.FileSearchTool(vector_store_ids=spec["vector_store_ids"])
    if t == "mcp":
        kwargs = {k: spec[k] for k in ("server_label", "server_url", "require_approval", "project_connection_id", "allowed_tools") if k in spec}
        return m.MCPTool(**kwargs)
    if t == "a2a":
        return m.A2ATool(project_connection_id=spec["project_connection_id"])
    if t == "function":
        return m.FunctionTool(name=spec["name"], description=spec.get("description", ""),
                              parameters=spec["parameters"], strict=spec.get("strict", True))
    raise SystemExit(f"unknown tool type '{t}'")


def deploy(project, spec: dict):
    from azure.ai.projects.models import PromptAgentDefinition

    definition = PromptAgentDefinition(
        model=spec["model"],
        instructions=spec["instructions"],
        tools=[build_tool(t) for t in spec.get("tools", [])] or None,
    )
    agent = project.agents.create_version(agent_name=spec["name"], definition=definition,
                                          description=spec.get("description"))
    print(f"  deployed {agent.name} version {agent.version}")
    return agent


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="*", help="agent YAML files (default: agents/*.yaml)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--delete", metavar="NAME", help="delete all versions of this agent")
    args = p.parse_args()

    if args.delete:
        sys.path.insert(0, str(ROOT / "notebooks"))
        from stark_helpers import project
        for v in list(project().agents.list_versions(agent_name=args.delete)):
            project().agents.delete_version(agent_name=args.delete, agent_version=v.version)
            print(f"  deleted {args.delete} version {v.version}")
        return

    files = [Path(f) for f in args.files] or sorted((ROOT / "agents").glob("*.yaml"))
    specs = [load_spec(f) for f in files]
    if args.dry_run:
        for s in specs:
            print(json.dumps(s, indent=2))
        return
    sys.path.insert(0, str(ROOT / "notebooks"))
    from stark_helpers import project
    for s in specs:
        print(f"{s['name']}:")
        deploy(project(), s)


if __name__ == "__main__":
    main()
