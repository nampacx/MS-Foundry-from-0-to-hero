# 📝 Changelog

All notable changes to this repo. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Newest first; each release lists what changed for someone who runs the notebooks or reads the docs.

## [Unreleased]

### Added
- Chapter 07, section 6: a marker test that reads the skill from the toolbox with `resources/read` and compares an answer with and without it, to prove a toolbox skill is really used. 🧪
- Hosted agent `jarvis-skills` (`src/jarvis-skills`, new `azure.yaml` service): J.A.R.V.I.S. that loads skills on demand with Agent Framework's `SkillsProvider` (the `skills/` files plus a code-defined `workshop-status` skill) instead of pasting them into the instructions. Chapter 09 section 4 deploys it and prints which skill tools the model called; the old section 4 is now section 5. `azd deploy` without a service name now deploys it too. Not deployed on a live project yet.
- `samples/skills_provider.py`: runs the `jarvis-skills` agent as a plain script, no deploy, and prints which skill tools the model called. The fast loop for drafting a skill. Explained in [mcp-skills.md](docs/mcp-skills.md) section 4, with pointers from chapter 07, `story.md` and the glossary.
- `CHANGELOG.md` and the rule in `AGENTS.md` that every change adds a line here.

### Changed
- Fewer emojis in docs, README, story and notebooks: only in titles, `##` headings, callouts and status markers. The rule is in `AGENTS.md`.
- Chapter 07: the GitHub Copilot harness section moves from section 6 to section 7.
- `mcp-skills.md` section 4: the delivery table says whether each mode reads the local `skills/` files or a Foundry skill version.

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
