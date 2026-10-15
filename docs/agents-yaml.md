# 📄 Agents as files: YAML, azd and CI

> 💡 **TL;DR:** Keep agent definitions in git. This repo supports two routes: [agents/*.yaml](../agents/jarvis.yaml) deployed by [deploy_agents.py](../scripts/deploy_agents.py) (prompt agents, plain SDK), and azd `azure.yaml` services (`azure.ai.agent`, `azure.ai.toolbox`, `azure.ai.skill`, `azure.ai.connection`). Re-deploying creates a **new version**.

| 📄 Route | 🧰 Command | 🤖 Agent kinds | ✅ Verified here |
|---|---|---|---|
| `agents/*.yaml` | `python scripts/deploy_agents.py` | prompt | YAML parsing, `${VAR}` resolution (dry run) |
| `azure.yaml` services | `azd deploy` | prompt, hosted, voice | ❌ not run against Azure |

Hands-on: [notebooks/08_agents_from_yaml.ipynb](../notebooks/08_agents_from_yaml.ipynb).

---

## 🗺️ The big picture

```mermaid
flowchart LR
  Y[📄 agents/*.yaml] -->|deploy_agents.py<br/>resolve env vars| SDK[azure-ai-projects<br/>create_version]
  Z[📄 azure.yaml<br/>azure.ai.agent · toolbox · skill] -->|azd deploy| EXT[azd Foundry extensions]
  SDK --> P[(📁 Foundry project)]
  EXT --> P
  P --> V[🏷️ agent name + version N]
```

---

## 1️⃣ Our YAML

| Field | Meaning |
|---|---|
| `name` | agent name; reuse = new version |
| `kind` | `prompt` (only kind this script deploys) |
| `model` | deployment name, e.g. `${STARK_CHAT_MODEL}` |
| `instructions` / `instructions_file` | inline text or a file next to the YAML |
| `tools[]` | `code_interpreter`, `web_search`, `file_search`, `mcp`, `a2a`, `function` |

`${VAR}` comes from `.env`; an unset variable stops the script (so a missing MCP URL never ships silently). `--dry-run` prints the resolved definitions for a pull-request check.

## 2️⃣ azd `azure.yaml`

Each Foundry resource is a **service** with a `host`: `azure.ai.project`, `azure.ai.agent`, `azure.ai.connection`, `azure.ai.toolbox`, `azure.ai.skill`. `uses:` orders them. Connections are applied by `azd provision`; agents, toolboxes and skills by `azd deploy`. Secrets stay in the azd environment (`${VAR}`), never in the file.

The old `agent.yaml` / `agent.manifest.yaml` files are deprecated. See the [azure.yaml reference](https://learn.microsoft.com/azure/foundry/agents/concepts/azure-yaml-reference).

## 3️⃣ In CI

A minimal pipeline: `deploy_agents.py --dry-run` on pull requests, `deploy_agents.py` on merge, then run an evaluation (chapter 10) against the new version before routing traffic to it.

---

## 🪜 Walkthrough: deploy an agent from a file

Code in [chapter 08](../notebooks/08_agents_from_yaml.ipynb).

**Step 1. Open [agents/jarvis.yaml](../agents/jarvis.yaml)** and read the fields from section 1.

**Step 2. Dry run.** `python scripts/deploy_agents.py --dry-run` prints the resolved definitions. An unset `${VAR}` stops here, before anything ships.

**Step 3. Deploy.** `python scripts/deploy_agents.py` creates a new **version** for each file.

**Step 4. Check the portal.** **Build → Agents** shows the new version.

**Step 5. Evaluate** the new version ([datasets-evals.md](datasets-evals.md)) before you route traffic to it.

---

## 🙈 Common mistakes

| 🚨 Mistake | 💥 What happens | ✅ Do this |
|---|---|---|
| a `${VAR}` that is not in `.env` | the script stops | add it, or use `--dry-run` to find it |
| `kind: hosted` in `agents/*.yaml` | the script deploys prompt agents only | use the `azure.yaml` route |
| using the old `agent.yaml` / manifest | deprecated | follow the `azure.yaml` reference |
| secrets in the YAML | they land in git | use `${VAR}` and the azd environment |
| expecting a re-deploy to overwrite | it adds a version | clean up old versions |
