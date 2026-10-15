# Agent instructions

Single source of truth for AI coding agents (Claude Code, GitHub Copilot, others).
`CLAUDE.md` and `.github/copilot-instructions.md` point here, so edit only this file.

## Writing documentation

Read this section before you create or change any `.md` file (docs, README, guides).
If your tool supports skills, use the `write-docs` skill ([.claude/skills/write-docs/SKILL.md](.claude/skills/write-docs/SKILL.md)); it runs these rules as a checklist.

Reference example: [docs/architecture.md](docs/architecture.md). Match its style.

### Where
- Topic docs go in `docs/`, named in lowercase (`architecture.md`, `conversations.md`).
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
- 🎨 Use colour and emojis: one emoji per heading, emoji columns in tables, and callouts (`> 💡`, `> ⚠️`, `> 🚫`).
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
