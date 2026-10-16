# Agent instructions

Single source of truth for AI coding agents (Claude Code, GitHub Copilot, others).
`CLAUDE.md` and `.github/copilot-instructions.md` point here, so edit only this file.

## Writing documentation

Read this section before you create or change any `.md` file (docs, README, guides).
If your tool supports skills, use the `write-docs` skill ([.claude/skills/write-docs/SKILL.md](.claude/skills/write-docs/SKILL.md)); it runs these rules as a checklist.

Reference example: [docs/conversations.md](docs/conversations.md). Match its style.

### Where
- Topic docs go in `docs/`, named in lowercase (`concepts.md`, `conversations.md`).
- Topic docs are numbered by reading order in the title (`# 🧭 1 · Title`) and in the `README.md` docs table. `troubleshooting.md`, `portal-tour.md` and `glossary.md` are reference docs and stay unnumbered. File names stay unnumbered.
- Link to the code instead of copying it. Use relative links, for example `[foundry.bicep](../infra/modules/foundry.bicep)`.
- Quote only the short snippet the reader needs (a policy line, a JSON block).

### Structure (information flow)
1. `# 🛡️ Title` as a question or plain statement.
2. A `> 💡 **TL;DR:**` callout with the answer in 2–3 sentences, plus a small table if it helps.
3. A "big picture" (mermaid diagram) before the details.
4. Numbered sections that follow the real order of events (call in, agent, tools, observability).
5. Optional or "what if" topics last, clearly marked as not implemented.
- Separate sections with `---`.
- Put each fact in the section where the reader needs it. Don't explain the same thing twice.

### Style
- Use emojis sparingly, as signposts, not decoration:
  - One emoji in the `#` title and in `##` headings such as `## 🗺️ The big picture`. Numbered sections use plain numbers (`## 1 · What you provide`), not keycap emojis. No emojis in `###` headings.
  - Callouts start with one emoji (`> 💡`, `> ⚠️`, `> 🚫`).
  - Status markers carry meaning and may appear anywhere: ✅ / ❌ (yes / no), ⚠️ (caution), 🧪 (preview), ❓ (not checked), 🔎 (likely cause, not reproduced).
  - No other emojis: none in table headers or cells, bullets, link text, mermaid nodes or running text.
- Prefer tables for comparisons and lookups, bullets for short lists, code blocks for config, XML and commands.
- Short sentences. Say what the thing does, then why.
- Use exact names from the repo (`STARK_PROJECT_ENDPOINT`, `stark.json`, `agent_reference`). Check them in the code before you write them down.
- Say what is demo-grade, not deployed or not planned. Never describe an idea as if it were implemented.
- Diagrams are mermaid. Keep them to one flow each.

### Before you finish
- Re-read the document top to bottom for information flow.
- Check that every link and file name exists.
- Keep `README.md` links to new docs up to date.

## Code and notebooks

- Python only (3.11+). Notebooks live in `notebooks/NN_name.ipynb` and import `notebooks/stark_helpers.py`.
- Every Foundry SDK call must match the current Microsoft Learn docs. Foundry moves fast: mark preview features as preview in notebook, doc and story.
- Config comes from `.env` (written by the azd `postprovision` hook, template in `.env.example`). Never hard-code endpoints or keys.
- Notebooks clean up what they create (agent versions, conversations, datasets) unless the next chapter needs it.
- Every chapter follows one template: `# NN · Title` with the story hook, a concept table and a "Deep dive" doc link; a setup cell (`import sys; sys.path.insert(0, '.')` + `from stark_helpers import *`); numbered sections `## 1 · …`; then, in this order, `## 👀 In the portal` (skip when there is nothing to see), `## 🧹 Clean up` (say so when there is nothing to delete), `## 🎯 Recap` ending with `> 💡 Next: …`.
- Shared logic lives in `stark_helpers.py` / `stark_docs.py`, not copied between notebooks: `run_functions` (function-call loop), `ask_agent` (MCP approvals), `skill_body`, `criterion` / `item_schema` / `agent_target` (evaluations), `arm` / `account_path` (ARM calls), `delete_agent` / `delete_dataset`. Show a mechanism inline once, in the chapter that teaches it (the loop in 05), then use the helper.
