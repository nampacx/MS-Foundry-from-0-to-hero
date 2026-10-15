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
OpenTelemetry tracing into Application Insights, custom spans, finding a conversation in the portal, and KQL for tokens and latency. See [docs/observability.md](docs/observability.md).

## 🧥 Act II · The Suit – J.A.R.V.I.S. *(planned)*
| # | Chapter | What it covers |
|---|---|---|
| 04 | `jarvis_prompt_agent` | agents from code: `create_version`, versions, `agent_reference` |
| 05 | `tools_function_and_builtin` | function calling, code interpreter, file search, web search |
| 06 | `mcp_tools` | MCP servers as tools: approvals, `allowed_tools`, our own MCP Function |
| 07 | `agent_skills` 🧪 | `SKILL.md` skills, uploaded and versioned in Foundry |
| 08 | `agents_from_yaml` | declarative agent YAML, `azd ai agent` |
| 09 | `hosted_agent` | your own agent container, deployed with azd |

## 🧪 Act III · The Lab – F.R.I.D.A.Y. *(planned)*
| # | Chapter | What it covers |
|---|---|---|
| 10 | `datasets_and_evals` | versioned datasets, built-in evaluators, cloud evaluation runs |
| 11 | `conversation_and_trace_evals` | conversation-level evals, evaluating live traces, continuous evaluation |

## 🔬 Act IV · The Senses *(planned)*
| # | Chapter | What it covers |
|---|---|---|
| 12 | `senses_ocr_read` | OCR / Read on images and PDFs |
| 13 | `senses_document_intelligence` | Document Intelligence and Content Understanding, as an agent tool |

## ⚠️ Act V · The Warning – Ultron *(planned)*
| # | Chapter | What it covers |
|---|---|---|
| 14 | `ultron_guardrails_redteam` 🧪 | guardrails, prompt injection through tools, red teaming |

## 🌐 Act VI · The Avengers – Vision *(planned)*
| # | Chapter | What it covers |
|---|---|---|
| 15 | `workflows` | sample workflows: sequential pipeline, handoff, group chat |
| 16 | `vision_a2a_capstone` 🧪 | agents calling agents over A2A, final orchestrator, teardown |

## 🧰 Helper
[`notebooks/stark_helpers.py`](notebooks/stark_helpers.py) holds the shared code: `project()`, `openai_client()`, `model()`, and `kql_wait()` (KQL with retry).

## 🏁 The moral
Models answer, **agents act**, **evaluations prove**, **monitoring watches**, **guardrails protect** and **protocols (MCP, A2A)** connect. You need all of them to go from Dummy to Vision.
