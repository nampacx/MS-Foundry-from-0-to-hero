# 📖 The Story of STARK

> *"Sometimes you gotta run before you can walk."* – Tony Stark 🦾

Tony Stark did not build J.A.R.V.I.S. in one night. He started with a clumsy robot arm, taught it to remember, gave it a body of tools, made it prove itself, learned the hard way what happens without guardrails, and finally let a team of minds work together. **Microsoft Foundry** is the workshop; the notebooks are the build log.

```
🔧 00 setup → 🤖 01 Dummy → 💬 02 memory → 📈 03 instruments → 🧥 04–09 J.A.R.V.I.S. → 🧪 10–11 F.R.I.D.A.Y. → 🔬 12–13 senses → ⚠️ 14 Ultron → 🌐 15–16 Vision
```

Technical background lives in [docs/](docs/): [architecture](docs/architecture.md), [conversations](docs/conversations.md), [observability](docs/observability.md).

## 🎬 Act I · The Workshop – Dummy and U

### 🔧 00 · `00_setup_workshop` – The garage
What a Foundry resource, project, endpoint and deployment are, and how `azd up` builds them. Checks your `.env`, lists deployments and does a smoke test. **Run first.**

### 🤖 01 · `01_dummy_first_call` – Dummy's first call
The Responses API and Chat Completions, instructions, streaming, structured output (JSON schema), what a response contains, and embeddings.

### 💬 02 · `02_conversations` – Giving Dummy a memory
Models forget. Manual history, `previous_response_id` chains (and forking), durable **conversations** with items, `store=False`, and cleanup. See [docs/conversations.md](docs/conversations.md).

### 📈 03 · `03_tracing_and_monitoring` – The lab instruments
OpenTelemetry tracing into Application Insights, custom spans, finding the traces in Application Insights, and KQL for tokens and latency (Foundry shows traces per agent from chapter 04). See [docs/observability.md](docs/observability.md).

## 🧥 Act II · The Suit – J.A.R.V.I.S.
Dummy answered; J.A.R.V.I.S. *acts*. Background: [docs/agents.md](docs/agents.md), [docs/agents-yaml.md](docs/agents-yaml.md), [docs/mcp-a2a-skills.md](docs/mcp-a2a-skills.md).

### 🧥 04 · `04_jarvis_prompt_agent` – The first agent
A prompt agent from code: `create_version`, talking through conversations and `agent_reference`, versions (roll out a new personality without touching clients), templated instructions with structured inputs, streaming.

### 🛠️ 05 · `05_tools_function_and_builtin` – Hands
Who runs a tool? **Function calling** (your code, in a loop), **code interpreter** (Foundry sandbox), **file search** (vector store over the workshop handbook), **web search** (with a data-boundary warning).

### 🔌 06 · `06_mcp_tools` – Plug into any toolbox
MCP servers as tools: the public Microsoft Learn server with approvals and `allowed_tools`, then our own **`stark-mcp`** Azure Function behind a project connection (the key never enters the agent). Tool output is untrusted input.

### 📜 07 · `07_agent_skills` 🧪 – A procedure, not a tool
Author a `SKILL.md`, upload versions, promote the default, attach it to a toolbox, read it as an MCP resource, and download it into a hosted agent.

### 📄 08 · `08_agents_from_yaml` – Agents as files
`agents/*.yaml` + `scripts/deploy_agents.py` (dry run, deploy, new version per run) and the azd `azure.yaml` route (`azure.ai.agent` services).

### 🏗️ 09 · `09_hosted_agent` – Your code, Foundry's runtime
A hosted agent built with Microsoft Agent Framework: run locally with `azd ai agent run`, deploy with `azd deploy`, call it like any agent, and see the escalation skill in its answers.

## 🧪 Act III · The Lab – F.R.I.D.A.Y.
*"Does it actually work?"* Background: [docs/datasets-evals.md](docs/datasets-evals.md).

### 🧪 10 · `10_datasets_and_evals` – Prove it
Upload a versioned dataset, define an evaluation (task adherence, intent resolution, coherence, violence), run it against an agent, read per-item reasons, fix the instructions, run again, compare pass rates, and add a CI-style quality gate. Also: scoring saved responses against ground truth (F1).

### 💬 11 · `11_conversation_and_trace_evals` 🧪 – Judge the whole conversation
Conversation-level evaluators on a dataset of multi-turn chats (the frustrating one fails), then evaluation of real, traced conversations from Application Insights (by id and by agent filter), and continuous evaluation.

## 🔬 Act IV · The Senses
Not everything is a language model. Background: [docs/foundry-tools.md](docs/foundry-tools.md).

### 👁️ 12 · `12_senses_ocr_read` – Reading the world
Text from a photographed whiteboard (Vision Read, with drawn bounding boxes) and from PDFs (Document Intelligence `prebuilt-read` and `prebuilt-layout` with tables and Markdown), plus a tiny OCR check you can assert.

### 🧾 13 · `13_senses_document_intelligence` – From pixels to data
`prebuilt-invoice` and `prebuilt-receipt` with confidence thresholds and arithmetic checks, Content Understanding analyzers (prebuilt and a custom schema with extract/generate/classify fields), and the whole thing as an **agent tool**.

## ⚠️ Act V · The Warning – Ultron
Background: [docs/guardrails.md](docs/guardrails.md).

### ⚠️ 14 · `14_ultron_guardrails_redteam` 🧪 – What happens without guardrails
A safe indirect prompt-injection demo (an email tells the agent to transfer money), four defences compared (naive, hardened instructions, approval gate, least privilege), a guardrail with Prompt Shields attached to an agent, and the AI Red Teaming Agent.

## 🌐 Act VI · The Avengers – Vision
Background: [docs/workflows.md](docs/workflows.md), [docs/mcp-a2a-skills.md](docs/mcp-a2a-skills.md).

### 🔀 15 · `15_workflows` – A plan, not a prompt
Agent Framework workflows: a **sequential** invoice pipeline (Document Intelligence tool → reviewer with the invoice-review skill → reporter), a **group chat** review board, a **handoff** topology, the pipeline as **declarative YAML**, and how to run a workflow in Foundry.

### 🌐 16 · `16_vision_a2a_capstone` 🧪 – The Avengers assemble
`friday-finance` exposed over **A2A v1.0** (agent card, A2A SDK client), `jarvis-orchestrator` calling her with the A2A tool and our MCP server, role assignment, an evaluation gate on the whole system, and teardown.

## 🧰 Helper
[`notebooks/stark_helpers.py`](notebooks/stark_helpers.py) holds the shared code: `project()`, `openai_client()`, `model()`, `ask_agent()` (with MCP approvals), `kql_wait()`, and the evaluation helpers. [`notebooks/stark_docs.py`](notebooks/stark_docs.py) wraps the document services.

## 🏁 The moral
Models answer, **agents act**, **evaluations prove**, **monitoring watches**, **guardrails protect** and **protocols (MCP, A2A)** connect. You need all of them to go from Dummy to Vision.
