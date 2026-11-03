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
- Shared logic lives in `stark_helpers.py` / `stark_docs.py`, not copied between notebooks: `run_functions` (function-call loop), `ask_agent` (MCP approvals), `skill_body`, `criterion` / `item_schema` / `agent_target` (evaluations), `arm` / `account_path` (ARM calls), `delete_agent` / `delete_dataset`, `messages` / `answer_text` / `final_message` / `mark` (reading a reply). Show a mechanism inline once, in the chapter that teaches it (the loop in 05), then use the helper. Helpers that only some chapters need go into their own module next to the notebooks (`stark_replies.py` for 04–09, `stark_evals.py`, `stark_guardrails.py`, `stark_harness.py`, `stark_workflows.py`, `stark_a2a.py`), so the cells keep only what the reader runs; quote the call the chapter teaches as a short snippet in its markdown.

### Notebook quality (the learner's view)

Read this before you create or change a notebook. If your tool supports skills, use the `review-notebook` skill ([.claude/skills/review-notebook/SKILL.md](.claude/skills/review-notebook/SKILL.md)); it runs these rules as a checklist. Reference example: [15_copilot_harness.ipynb](notebooks/15_copilot_harness.ipynb), sections 4 and 5.

**Place and story**
- A chapter sits after every chapter it builds on and before the ones that build on it. List what it imports, reuses and refers to before you pick its number.
- Never say an earlier chapter "showed" something unless it still does. After a move or a removed section, grep for every chapter number and file name.
- Chapters get whole numbers. To insert one, renumber the chapters after it instead of using `14.5` or `14b`: file names would sort wrong (`14_5_…` lists before `14_ultron…`) and break the `NN_name.ipynb` convention. Then update the README tables, `story.md` acts, the docs reading order, every "chapter NN" mention and the open pull request's title and text.

**One experiment per cell**
- Each experiment (a case, a step) gets a markdown cell with `### Case X · Title` or `### Step N · Title`, then **Goal:** (what it proves), an input table and **Expected:** (the concrete outcome), then one short code cell.
- Order experiments so each changes one thing: the same question in two conversations before the same invoice in two conversations.
- Name the state an experiment depends on, and let the first cell of a sequence create it (case A opens its own conversation). Re-running a cell must not change its result; when it would, say so in the markdown.

**Show what the model gets and says**
- Build every prompt in the case cell with named arguments (`invoice_request(pym_invoice, approver="Pepper Potts", iban=...)`), and show the full prompt in the output. Fold bulky data (`<details>`) instead of cutting it.
- Show the agent's whole answer, rendered as Markdown with `display(Markdown(...))`: VS Code cuts long plain-text output, rich output it keeps. Join multiple messages with blank lines (`output_text` glues them together). Never truncate the answer.
- The committed notebook has no outputs, so it must read well on GitHub: put one example of what the reader will see (a sample prompt, a sample check table) in the markdown.
- End each turn with a small check table: the result next to the expected one (✅ / ❌ only where there is a right answer, `yes` / `no` where both are valid), plus what ran and what is missing.
- Helpers that display return nothing, so a cell never ends with a raw `Response(...)` repr.

**Checks on model output**
- Check the final message, not the first: agents often send a preamble ("I'll check ..."). Take the last verdict keyword, not the first.
- Deterministic rules (arithmetic, lookups, duplicates, thresholds) belong in code or skill scripts, not in the model and not in the expected text. When a live run disagrees with **Expected:**, find out which of the three is wrong (code, rule, expectation) before you change one.

**Names and code**
- Names used in more than one cell say what they hold: `sdk_conversation`, `pym_invoice`, `SDK_AGENT_NAME` (a string) vs `sdk_agent` (an object). No `pp`, `conv17`, `r` across cells, and no chapter numbers in names that survive a renumbering.
- Cells keep data and calls. Functions go to a helper module (see above), each with a one-line docstring; markdown links the file the first time a helper appears.

**Facts, not guesses**
- A live run turns ❓ into facts: write down what it showed (item types, paths, values) and keep ❓ only for what is still unchecked.
- After every change to code or output, re-read each markdown cell that describes it: sample prompts, tables of output parts, helper names, expected outcomes. They go stale silently.
- Before a commit, strip outputs and local kernel metadata from notebooks, and delete files your local test runs left behind.

## Changelog

`CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Keep it up to date in the same commit as the change:

- Add one line under `## [Unreleased]` for every change a reader notices: a notebook, doc, script, helper, infra or deploy change. Skip typo and formatting-only fixes.
- File it under `### Added`, `### Changed`, `### Fixed` or `### Removed`. Create the heading when it is missing.
- Write for the reader, not the commit log: name the chapter, doc or file and say what is different for them. No commit hashes.
- Mark preview features with 🧪, as everywhere else.
- If a later change in the same release replaces an `[Unreleased]` line, edit that line instead of adding a second one.
- Never edit a released section. Releasing (renaming `[Unreleased]` to `[x.y] – YYYY-MM-DD`) is the maintainer's call.
