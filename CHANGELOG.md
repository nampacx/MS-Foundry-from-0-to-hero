# 📝 Changelog

All notable changes to this repo. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Newest first; each release lists what changed for someone who runs the notebooks or reads the docs.

## [Unreleased]

### Added
- Chapter 17 `17_copilot_harness.ipynb` 🧪: J.A.R.V.I.S. as a prompt agent on the new Microsoft Copilot harness. It uploads the `stark-escalation` and `invoice-review` skill folders as zip packages (`create_from_files`), creates the agent with `MicrosoftCopilotHarness()` and pinned `SkillReference`s, keeps the harness shell on for the skill scripts and switches off subagents. Section 4 extracts two invoice PDFs with Document Intelligence and sends four invoices, each built to trip a different `invoice-review` script, then lists which scripts the agent ran. Section 5 shows the per-conversation workspace with the duplicate ledger. Not run on a live project yet.
- `invoice-review` skill: five standard-library scripts the Copilot harness runs with its shell tool (`check_invoice.py`, `vendor_check.py`, `iban_check.py`, `ledger.py`, `approval_limit.py`), plus `assets/` with the vendor master, approval limits and an example invoice. `SKILL.md` lists the exact commands, adds the vendor, IBAN and duplicate checks, and tells agents without shell (chapters 15, 16, `jarvis-hosted`) to say those checks were not run. `jarvis-skills` sees the scripts but has no script runner, so it can't run them.
- `src/jarvis-harness/azure.yaml` 🧪: the same agent as its own azd project (`azure.ai.skill` services for both skills, `azure.ai.agent` with `harness.type: microsoft_copilot_preview`), deployed into the existing STARK project with `azd deploy --all`. `scripts/harness_env.py` fills its azd environment from `.env`; `sync_skills.py` now also copies `skills/` there, without `__pycache__`. The agent keeps shell on for the skill scripts.
- [copilot-harness.md](docs/copilot-harness.md) (doc 16): what the harness changes, the four building blocks from the 2026-10-28 announcement, authoring options, request rules, skills that run scripts, workspace, azd deploy, security, limits and sandbox prices from 2026-12-01.
- [hosted-agents.md](docs/hosted-agents.md): long-running resilience for hosted agents (generally available) as a not-implemented option, and a pointer to the Copilot harness for agents that need no loop of their own.
- Chapter 07, section 6: a marker test that reads the skill from the toolbox with `resources/read` and compares an answer with and without it, to prove a toolbox skill is really used. 🧪
- Hosted agent `jarvis-skills` (`src/jarvis-skills`, new `azure.yaml` service): J.A.R.V.I.S. that loads skills on demand with Agent Framework's `SkillsProvider` (the `skills/` files plus a code-defined `workshop-status` skill) instead of pasting them into the instructions. Chapter 09 section 4 deploys it and prints which skill tools the model called; the old section 4 is now section 5. `azd deploy` without a service name now deploys it too. Not deployed on a live project yet.
- `samples/skills_provider.py`: runs the `jarvis-skills` agent as a plain script, no deploy, and prints which skill tools the model called. The fast loop for drafting a skill. Explained in [mcp-skills.md](docs/mcp-skills.md) section 4, with pointers from chapter 07, `story.md` and the glossary.
- Chapter 15, section 1: a threshold router. The extractor answers in a fixed JSON shape, and conditional edges (`Case` / `Default`) in your code send the invoice to automatic approval, the reviewer or escalation, without a model choosing the path. Explained in [workflows.md](docs/workflows.md). Not run on a live project yet.
- `CHANGELOG.md` and the rule in `AGENTS.md` that every change adds a line here.

### Changed
- `mcp-skills.md`, glossary and troubleshooting: the harness is the Microsoft Copilot harness (`MicrosoftCopilotHarness`, `microsoft_copilot_preview`), a public preview. The old GitHub Copilot harness name is gone from the docs.
- `requirements.txt` needs `azure-ai-projects>=2.9.0` (for `MicrosoftCopilotHarness`). pip then picks `agent-framework-foundry` 1.10.1, because later versions pin `azure-ai-projects<2.8.0`; a comment in the file and a troubleshooting row explain the warning.
- Fewer emojis in docs, README, story and notebooks: only in titles, `##` headings, callouts and status markers. The rule is in `AGENTS.md`.
- `mcp-skills.md` section 4: the delivery table says whether each mode reads the local `skills/` files or a Foundry skill version.

### Removed
- Chapter 07: the Copilot harness section (the old section 7, default runtime vs. harness side by side). Chapter 17 covers the harness, and chapter 07's delivery table links there.

### Fixed
- Chapter 07 names the Python API for MCP skills (`SkillsProvider` with `MCPSkillsSource` 🧪) instead of the C# `UseMcpSkills`.

## [0.1] – 2026-10-15

First release: a story-driven Microsoft Foundry tutorial, from a first model call to a team of agents. Merged in [nampacx/MS-Foundry-from-0-to-hero#1](https://github.com/nampacx/MS-Foundry-from-0-to-hero/pull/1) and [nampacx/MS-Foundry-from-0-to-hero#2](https://github.com/nampacx/MS-Foundry-from-0-to-hero/pull/2).

### Added
- Infrastructure: one `azd up` deploys a Foundry resource and project with models, Application Insights, Log Analytics and role assignments (Bicep), and writes `.env`.
- Chapters 00–16 as notebooks: models and conversations, tracing, prompt agents, tools, MCP, skills 🧪, agents from YAML, hosted agents, datasets and evaluations, OCR and Document Intelligence, guardrails and red teaming 🧪, workflows, and the A2A capstone 🧪.
- Hosted agents `jarvis-hosted`, `invoice-workflow` and `morning-briefing` (`azure.ai.agent` services in `azure.yaml`). `invoice-workflow` and `morning-briefing` were deployed and called on a live project.
- The repo's own MCP server `stark-mcp` (`src/stark-mcp`), shared helpers in `notebooks/stark_helpers.py` and `notebooks/stark_docs.py`, and scripts for model checks, agent deployment, skill sync, MCP connection, role grants and teardown.
- Docs in reading order, from `concepts.md` to `capstone.md`, plus glossary, troubleshooting and portal tour, and `story.md` as one build log.

### Fixed
- `azd` and notebook failures found while running the chapters on a real project: pinned `azd` and Foundry extension versions, the Bicep outputs the `azure.ai.*` services need, embeddings on the account endpoint, front matter in `SKILL.md` on Windows (CRLF) checkouts, and notebooks that can be re-run.
