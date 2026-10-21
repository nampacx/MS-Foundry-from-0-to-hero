"""skills_provider: run the jarvis-skills hosted agent as a plain script and see which skills the model loads.

The agent itself lives in src/jarvis-skills/main.py (Agent Framework SkillsProvider, chapter 09). This script builds
the same agent on the repo's skills/ folder, without a server or a deploy, and prints the skill tools the model
called. That is the fast loop for writing a new skill: edit skills/<name>/SKILL.md, re-run, read the tool calls.

Run:  python samples/skills_provider.py                     (two demo questions)
      python samples/skills_provider.py "your question"
Needs STARK_PROJECT_ENDPOINT and STARK_CHAT_MODEL in .env (azd up writes them) and `az login`.
"""
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# src/jarvis-skills is a deploy folder, not a package, so load its main.py by path.
_spec = importlib.util.spec_from_file_location("jarvis_skills", ROOT / "src" / "jarvis-skills" / "main.py")
jarvis_skills = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jarvis_skills)

DEMO_QUESTIONS = [
    "The arc reactor is making a high-pitched whine and the floor is getting warm. What now?",
    "How is the fabrication bay doing?",
]


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
    agent = jarvis_skills.build_agent(ROOT / "skills")
    for question in questions:
        result = await agent.run(question)
        print(f"\n> {question}")
        for call in skill_calls(result) or ["(no skill tool called)"]:
            print(f"  tool: {call}")
        print(result.text)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or DEMO_QUESTIONS))
