"""skills_provider: J.A.R.V.I.S. with Agent Framework's SkillsProvider (skills loaded on demand), run locally.

The hosted agents in src/ use *direct injection*: every SKILL.md is pasted into the instructions, so every run pays
for every skill. SkillsProvider only advertises each skill's name and description. The model calls `load_skill`
when a skill fits, `read_skill_resource` for extra files, and `run_skill_script` for code. That is the fast loop
for writing a new skill: edit skills/<name>/SKILL.md, re-run, read which skill tools were called.

Run:  python samples/skills_provider.py                     (two demo questions)
      python samples/skills_provider.py "your question"
Needs STARK_PROJECT_ENDPOINT and STARK_CHAT_MODEL in .env (azd up writes them) and `az login`.
"""
import asyncio
import json
import os
import sys
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

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

INSTRUCTIONS = (
    "You are J.A.R.V.I.S., Tony Stark's workshop assistant. Be concise, dry and helpful. "
    "Use the available skills when they match the task; never guess workshop facts."
)

DEMO_QUESTIONS = [
    "The arc reactor is making a high-pitched whine and the floor is getting warm. What now?",
    "How is the fabrication bay doing?",
]

WORKSHOP = {
    "arc reactor": "online, 3.0 GW, last service 2026-09-30",
    "fabrication bay": "busy, 6 hours until the queue is empty",
    "hangar": "idle, 12 suits stored",
}

# A code-defined skill: same SKILL.md shape, but built in Python. Its resource and script run in-process.
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


def build_agent() -> Agent:
    source = AggregatingSkillsSource([
        FileSkillsSource(ROOT / "skills"),  # skills/*/SKILL.md, the same files chapter 07 uploads to Foundry
        InMemorySkillsSource([workshop_skill]),
    ])
    client = FoundryChatClient(
        project_endpoint=os.environ["STARK_PROJECT_ENDPOINT"],
        model=os.environ["STARK_CHAT_MODEL"],
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
    )


def skill_calls(result) -> list[str]:
    """Which skill tools the model called, for example `load_skill {"skill_name": "stark-escalation"}`."""
    calls = []
    for message in result.messages:
        for content in message.contents:
            if content.type == "function_call":
                args = content.arguments if isinstance(content.arguments, str) else json.dumps(content.arguments)
                calls.append(f"{content.name} {args}")
    return calls


async def main(questions: list[str]) -> None:
    agent = build_agent()
    for question in questions:
        result = await agent.run(question)
        print(f"\n> {question}")
        for call in skill_calls(result) or ["(no skill tool called)"]:
            print(f"  tool: {call}")
        print(result.text)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or DEMO_QUESTIONS))
