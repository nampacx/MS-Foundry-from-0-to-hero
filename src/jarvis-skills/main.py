"""jarvis-skills: J.A.R.V.I.S. as a Foundry *hosted agent* that loads skills on demand (Agent Framework SkillsProvider).

jarvis-hosted pastes every SKILL.md into its instructions (direct injection), so every call pays for every skill.
Here the model only sees each skill's name and description. It calls `load_skill` when a skill fits,
`read_skill_resource` for extra files and `run_skill_script` for code. Those calls show up in the traces.

Run locally:  azd ai agent run      Deploy:  azd deploy jarvis-skills      Call:  azd ai agent invoke jarvis-skills "hello"
Without a server: python samples/skills_provider.py (same agent, prints which skill tools the model called).
"""
import os
from pathlib import Path
from typing import Annotated

from agent_framework import (
    Agent,
    AggregatingSkillsSource,
    FileSkillsSource,
    InlineSkill,
    InMemorySkillsSource,
    SkillFrontmatter,
    SkillsProvider,
)
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

INSTRUCTIONS = (
    "You are J.A.R.V.I.S., Tony Stark's workshop assistant. Be concise, dry and helpful. "
    "Use the available skills when they match the task; never guess workshop facts."
)

WORKSHOP = {
    "arc reactor": "online, 3.0 GW, last service 2026-09-30",
    "fabrication bay": "busy, 6 hours until the queue is empty",
    "hangar": "idle, 12 suits stored",
}

# A code-defined skill: same SKILL.md shape, but built in Python. Its resource and script run in-process.
# It replaces jarvis-hosted's workshop_status tool, so the model only learns about it when it needs it.
workshop_skill = InlineSkill(
    frontmatter=SkillFrontmatter(
        name="workshop-status",
        description="Live status of workshop systems (arc reactor, fabrication bay, hangar). Use for any status question.",
    ),
    instructions="Read the `systems` resource to see what exists, then run the `status` script for the system asked about.",
)


@workshop_skill.resource
def systems() -> str:
    """The workshop systems J.A.R.V.I.S. can report on."""
    return ", ".join(WORKSHOP)


@workshop_skill.script
def status(system: Annotated[str, Field(description="One of the names from the systems resource.")]) -> str:
    """Get the status of one workshop system."""
    return WORKSHOP.get(system.strip().lower(), f"unknown system '{system}', known: {', '.join(WORKSHOP)}")


def env(name: str, local_fallback: str) -> str:
    """Hosted: the platform (or azure.yaml `env:`) sets `name`. Local run: fall back to the STARK_* key in the repo's .env."""
    return os.environ.get(name) or os.environ[local_fallback]


def build_agent(skills_dir: Path, **agent_options) -> Agent:
    """J.A.R.V.I.S. with the SKILL.md files in `skills_dir` plus the code-defined workshop-status skill."""
    source = AggregatingSkillsSource([
        FileSkillsSource(skills_dir),  # skills/*/SKILL.md, the same files chapter 07 uploads to Foundry
        InMemorySkillsSource([workshop_skill]),
    ])
    client = FoundryChatClient(
        project_endpoint=env("FOUNDRY_PROJECT_ENDPOINT", "STARK_PROJECT_ENDPOINT"),
        model=env("MODEL_DEPLOYMENT_NAME", "STARK_CHAT_MODEL"),
        credential=DefaultAzureCredential(),
    )
    return Agent(
        client=client,
        instructions=INSTRUCTIONS,
        context_providers=[SkillsProvider(
            source,
            # All three skill tools need approval by default. These skills are this repo's own files and code, so
            # skip it. For skills from elsewhere keep approval on, at least for run_skill_script.
            disable_load_skill_approval=True,
            disable_read_skill_resource_approval=True,
            disable_run_skill_script_approval=True,
        )],
        **agent_options,
    )


def main() -> None:
    from agent_framework_foundry_hosting import ResponsesHostServer  # here, so samples/ runs without the host package

    # sync_skills.py (azd predeploy) copies the repo's skills/ here; the ZIP only contains this folder.
    agent = build_agent(Path(__file__).parent / "skills", default_options={"store": False})  # the host keeps the history
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
