"""jarvis-hosted: J.A.R.V.I.S. as a Foundry *hosted agent* (Microsoft Agent Framework + Responses protocol).

A prompt agent (chapter 04) is configuration that Foundry runs for you. A hosted agent is *your code* in a managed
container: you decide the logic, tools and libraries. Foundry gives it an endpoint, identity, scaling and tracing.

Run locally:  azd ai agent run      Deploy:  azd deploy      Call:  azd ai agent invoke "hello"
"""
import os
import re
from pathlib import Path
from typing import Annotated

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

BASE_INSTRUCTIONS = (
    "You are J.A.R.V.I.S., Tony Stark's workshop assistant. Be concise, dry and helpful. "
    "Use your tools for facts about the workshop; never guess."
)


def env(name: str, local_fallback: str) -> str:
    """Hosted: the platform (or azure.yaml `env:`) sets `name`. Local run: fall back to the STARK_* key in the repo's .env."""
    return os.environ.get(name) or os.environ[local_fallback]


def load_skills(directory: Path) -> str:
    """Direct skill injection: every skills/<name>/SKILL.md becomes extra instructions (see chapter 07)."""
    parts = []
    for skill_md in sorted(directory.glob("*/SKILL.md")):
        body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", skill_md.read_text(encoding="utf-8"), count=1, flags=re.S)  # drop front matter
        parts.append(f"\n\n## Skill: {skill_md.parent.name}\n{body.strip()}")
    return "".join(parts)


WORKSHOP = {
    "arc reactor": "online, 3.0 GW, last service 2026-09-30",
    "fabrication bay": "busy, 6 hours until the queue is empty",
    "hangar": "idle, 12 suits stored",
}


@tool(approval_mode="never_require")
def workshop_status(system: Annotated[str, Field(description="One of: arc reactor, fabrication bay, hangar.")]) -> str:
    """Get the status of a workshop system."""
    return WORKSHOP.get(system.strip().lower(), f"unknown system '{system}', known: {', '.join(WORKSHOP)}")


def main() -> None:
    client = FoundryChatClient(
        project_endpoint=env("FOUNDRY_PROJECT_ENDPOINT", "STARK_PROJECT_ENDPOINT"),
        model=env("MODEL_DEPLOYMENT_NAME", "STARK_CHAT_MODEL"),
        credential=DefaultAzureCredential(),
    )
    agent = Agent(
        client=client,
        instructions=BASE_INSTRUCTIONS + load_skills(Path(__file__).parent / "skills"),
        tools=[workshop_status],
        default_options={"store": False},  # the host keeps the conversation history
    )
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
