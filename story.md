# 📖 The Story of STARK

> *"Sometimes you gotta run before you can walk."* – Tony Stark

A cave. A box of scraps. A man with a deadline and one clumsy robot arm.

Tony Stark did not build J.A.R.V.I.S. in one night. He built it the hard way: a first spark, a memory, a toolbox, a test lab, a pair of eyes, a near disaster, and finally a team that could fight together. **Microsoft Foundry** is the workshop. The notebooks are the build log. You are the engineer holding the soldering iron.

```
00 setup → 01 Dummy → 02 memory → 03 instruments → 04–09 J.A.R.V.I.S. → 10–11 F.R.I.D.A.Y. → 12–13 senses → 14 Ultron → 15–16 Vision
```

> 🧭 **New to Foundry?** Read [concepts](docs/concepts.md) and [getting started](docs/getting-started.md) first. If something breaks mid-mission, open [troubleshooting](docs/troubleshooting.md).

| Act | The mission | Chapters | Field manual |
|---|---|---|---|
| I · The Workshop | wake the first machine and give it a memory | 00–03 | [concepts](docs/concepts.md) · [getting started](docs/getting-started.md) · [models](docs/models.md) · [conversations](docs/conversations.md) · [observability](docs/observability.md) |
| II · The Suit | turn a talker into a doer | 04–09 | [agents](docs/agents.md) · [tools](docs/tools.md) · [MCP and skills](docs/mcp-skills.md) · [agents as files](docs/agents-yaml.md) · [hosted agents](docs/hosted-agents.md) |
| III · The Lab | prove it works before it flies | 10–11 | [datasets and evals](docs/datasets-evals.md) |
| IV · The Senses | learn to see the world | 12–13 | [Foundry Tools](docs/foundry-tools.md) |
| V · The Warning | meet the enemy you built | 14 | [guardrails](docs/guardrails.md) |
| VI · The Avengers | stop working alone | 15–16 | [workflows](docs/workflows.md) · [A2A capstone](docs/capstone.md) |

---

## 🎬 Act I · The Workshop – Dummy and U
*It starts small. A single arm, a single question, and a lot of smoke.*

### 00 · `00_setup_workshop` – The garage
Every legend needs a garage. You raise the walls with one command (`azd up`), then learn the layout: a **Foundry resource**, a **project**, an **endpoint** and your first **deployments**. A smoke test checks that the lights come on. **Run this first.**

### 01 · `01_dummy_first_call` – Dummy's first call
One model, one question, one answer. Meet the **Responses API** and the older Chat Completions. Learn to steer with instructions, stream the words as they appear, force **structured output** into a JSON schema, peek inside a response, and turn words into numbers with **embeddings**. See [models](docs/models.md).

### 02 · `02_conversations` – Giving Dummy a memory
Dummy forgets everything between calls. You fix that three ways: send the history yourself, chain responses with `previous_response_id` (and fork a timeline), or keep a durable **conversation** of items. You also learn when to forget on purpose with `store=False`. See [conversations](docs/conversations.md).

### 03 · `03_tracing_and_monitoring` – The lab instruments
You cannot fix what you cannot see. Wire up OpenTelemetry, send spans to Application Insights, add your own attributes and hunt for your calls with **KQL**: tokens, latency, models. From chapter 04, Foundry also shows traces per agent. See [observability](docs/observability.md).

---

## 🧥 Act II · The Suit – J.A.R.V.I.S.
*Dummy answered. J.A.R.V.I.S. acts. The suit takes shape piece by piece.*

Field manuals: [agents](docs/agents.md) · [tools](docs/tools.md) · [MCP and skills](docs/mcp-skills.md) · [agents as files](docs/agents-yaml.md) · [hosted agents](docs/hosted-agents.md).

### 04 · `04_jarvis_prompt_agent` – The first agent
Your first real agent. `create_version` gives it a name and a personality. You talk to it through conversations and an `agent_reference`, ship a **new version** without touching a single client, and fill templated instructions with **structured inputs**. A short, nasty test shows why user text must never ride in those inputs. See [agents](docs/agents.md).

### 05 · `05_tools_function_and_builtin` – Hands
A mind without hands is just advice. The question is always **who runs the tool**: your code in a loop (**function calling**), a Foundry sandbox (**code interpreter**), or a **vector store** over the workshop handbook (**file search**). **Web search** comes with a data-boundary warning. See [tools](docs/tools.md).

### 06 · `06_mcp_tools` – Plug into any toolbox
Why build every tool yourself? Plug in **MCP** servers: the public Microsoft Learn server (with approvals and `allowed_tools`), then our own **`stark-mcp`** Azure Function behind a project connection. The key never touches the agent. And remember: tool output is untrusted input. See [MCP and skills](docs/mcp-skills.md).

### 07 · `07_agent_skills` (preview) – A procedure, not a tool
Some knowledge is a recipe, not a gadget. Write a `SKILL.md`, upload versions, promote the default, attach it to a toolbox, read it as an MCP resource, prove with a marker test that the model actually follows it, and pull it into a hosted agent. Writing a new skill? Draft it on the bench first: [skills_provider.py](samples/skills_provider.py) runs J.A.R.V.I.S. as a plain script and shows you which skill the model picked. Preview territory: expect rough ground. See [MCP and skills](docs/mcp-skills.md).

### 08 · `08_agents_from_yaml` – Agents as files
Blueprints belong in a vault. Define agents in `agents/*.yaml`, dry-run them, deploy them with `scripts/deploy_agents.py`, and meet the azd `azure.yaml` route (`azure.ai.agent` services). See [agents as files](docs/agents-yaml.md).

### 09 · `09_hosted_agent` – Your code, Foundry's runtime
Time to bring your own engine. Build a hosted agent with Microsoft Agent Framework, run it locally with `azd ai agent run`, deploy with `azd deploy`, and call it like any other agent. Watch the escalation skill show up in its answers. Then build a second suit, `jarvis-skills`, that keeps its skills in the drawer: Agent Framework's `SkillsProvider` shows the model only their names and hands over a skill when the model asks for it. See [hosted agents](docs/hosted-agents.md).

---

## 🧪 Act III · The Lab – F.R.I.D.A.Y.
*"Does it actually work?" A hero who cannot prove it is just a rumour.*

Field manual: [datasets and evals](docs/datasets-evals.md).

### 10 · `10_datasets_and_evals` – Prove it
Upload a versioned dataset. Define an evaluation. Run it against your agent, read why each answer passed or failed, fix the instructions, run again and compare. Add a CI-style **quality gate** so a weaker version never ships. Bonus: score saved responses against ground truth with F1.

### 11 · `11_conversation_and_trace_evals` (preview) – Judge the whole conversation
One good answer proves little. Judge **whole conversations** (the frustrating one fails), then evaluate **real traced conversations** from Application Insights, by id and by agent filter. This is where continuous evaluation begins.

---

## 🔬 Act IV · The Senses
*Not every problem is a language problem. Some are pixels.*

Field manual: [Foundry Tools](docs/foundry-tools.md).

### 12 · `12_senses_ocr_read` – Reading the world
Read a photographed whiteboard with Vision Read (bounding boxes included). Read PDFs with Document Intelligence `prebuilt-read` and `prebuilt-layout`: text, tables, Markdown. Finish with a tiny OCR check you can assert.

### 13 · `13_senses_document_intelligence` – From pixels to data
Turn invoices and receipts into typed fields with `prebuilt-invoice` and `prebuilt-receipt`. Respect **confidence** and check the arithmetic in code. Then try **Content Understanding** with a custom schema (extract, generate, classify) and wrap the whole thing as an **agent tool**.

---

## ⚠️ Act V · The Warning – Ultron
*Every creation has a shadow. This chapter shows you what it looks like, safely.*

Field manual: [guardrails](docs/guardrails.md).

### 14 · `14_ultron_guardrails_redteam` (preview) – What happens without guardrails
An email whispers to your agent: *"transfer the funds."* You stage the attack on a harmless demo function and count how often the agent obeys. Then you fight back with four defences (naive, hardened instructions, approval gate, least privilege), a **guardrail with Prompt Shields**, and the **AI Red Teaming Agent**.

---

## 🌐 Act VI · The Avengers – Vision
*One mind is powerful. Minds that cooperate are something else.*

Field manuals: [workflows](docs/workflows.md) · [A2A capstone](docs/capstone.md).

### 15 · `15_workflows` – A plan, not a prompt
Stop shouting orders at one agent. Draw a plan with Agent Framework **workflows**: a **sequential** invoice pipeline (Document Intelligence tool, then a reviewer with the invoice-review skill, then a reporter), a **threshold router** where your code, not a model, sends the invoice to auto-approval, review or escalation, a **group chat** review board, a **handoff** topology, the same pipeline as **declarative YAML**, and how to run it inside Foundry. See [workflows](docs/workflows.md).

### 16 · `16_vision_a2a_capstone` (preview) – The Avengers assemble
The finale. `friday-finance` goes public over **A2A v1.0** with an agent card. `jarvis-orchestrator` calls her through the A2A tool and our MCP server. You grant the roles, run an evaluation gate on the whole system and tear it down cleanly. See [A2A capstone](docs/capstone.md).

---

## 🧰 The toolbelt
[`notebooks/stark_helpers.py`](notebooks/stark_helpers.py) holds the shared gear: `project()`, `openai_client()`, `model()`, `ask_agent()` (with MCP approvals), `kql_wait()` and the evaluation helpers. [`notebooks/stark_docs.py`](notebooks/stark_docs.py) wraps the document services.

## 🏁 The moral
Models answer. **Agents act.** **Evaluations prove.** **Monitoring watches.** **Guardrails protect.** **Protocols (MCP, A2A) connect.** You need all of them to go from Dummy to Vision.

> 🛠️ *"I am Iron Man."* – but first, run chapter 00.
