# 🔌 MCP, skills and A2A on Foundry agents

> 💡 **TL;DR:** **MCP** gives an agent *tools* from a remote server. **Skills** give an agent *procedures* from a versioned `SKILL.md`. **A2A** lets an agent call *another agent* (chapter 16). Secrets live in **project connections**, never in the agent definition.

| 🔌 | 🎯 Gives the agent | 📦 Lives in | 🧪 Status |
|---|---|---|---|
| MCP | tools (functions with schemas) | remote MCP server + optional project connection | GA tool; toolboxes preview |
| Skills | instructions / know-how | Foundry Skills API (versioned) | 🧪 preview |
| Toolbox | one MCP endpoint for tools **and** skills | Foundry toolbox (versioned) | 🧪 preview |
| A2A | another agent as a tool | project connection to the remote agent | A2A v1.0 GA; SDK surface newer |

Hands-on: [06 MCP](../notebooks/06_mcp_tools.ipynb) · [07 skills](../notebooks/07_agent_skills.ipynb) · [16 A2A](../notebooks/16_vision_a2a_capstone.ipynb).

---

## 🗺️ The big picture

```mermaid
flowchart LR
  A[🤖 Agent] -->|mcp tool<br/>server_url| S1[🌐 Microsoft Learn MCP<br/>public]
  A -->|mcp tool + project_connection_id| S2[⚡ stark-mcp<br/>Azure Function]
  A -->|mcp tool → toolbox URL| TB[🧰 Toolbox]
  TB -->|tools| S2
  TB -->|skills as MCP resources| SK[📜 stark-escalation<br/>SKILL.md v1, v2]
  CN[(🔑 project connection<br/>stark-mcp · function key)] -.-> S2
  H[🏗️ Hosted agent] -->|direct injection<br/>skills/*/SKILL.md| SK
```

---

## 1️⃣ MCP in an agent

`MCPTool(server_label, server_url, allowed_tools, require_approval, project_connection_id)`. The model sees the server's tool list (filtered by `allowed_tools`) and decides when to call. See [agents.md](agents.md) for the approval loop.

| 🛡️ Practice | Why |
|---|---|
| `allowed_tools` allow-list | smaller attack surface, fewer wrong tool picks |
| `require_approval="always"` for writes | a human sees tool and arguments first |
| connection for credentials | the agent definition (and its traces) carry no secrets |
| treat results as untrusted | indirect prompt injection (chapter 14) |

## 2️⃣ Our MCP server

[src/stark-mcp/function_app.py](../src/stark-mcp/function_app.py) is an Azure Function (Flex Consumption, Python) using the Functions MCP extension. Endpoint: `https://<app>.azurewebsites.net/runtime/webhooks/mcp`, authenticated with the `mcp_extension` system key. The postdeploy hook [connect_mcp.py](../scripts/connect_mcp.py) stores that key in the project connection `stark-mcp`.

> ⚠️ **Demo-grade:** public endpoint with a shared system key. Production: private networking or Entra-based auth, per-user identity.

## 3️⃣ Skills

A skill is a folder with `SKILL.md` (front matter `name`, `description`, then Markdown). In Foundry it is **versioned**: every upload is an immutable version, and `default_version` decides what unpinned consumers get. Three ways to deliver it:

| 🚚 Mode | How |
|---|---|
| Direct injection | download into the agent project; agent code adds it to instructions ([main.py](../src/jarvis-hosted/main.py) `load_skills`) |
| Toolbox | attach with `ToolboxSkillReference`; MCP clients read `resources/list` and `resources/read` |
| Copilot harness | `skills:` on a prompt agent with `harness.type: github_copilot_preview` |

## 4️⃣ A2A

The **Agent2Agent** protocol lets agents discover and call each other. Foundry supports **v1.0 (GA)** and v0.3 (preview). Limits: **text only**, **JSON-RPC** transport, **no streaming**, and the target must use the **Responses protocol** (prompt agents do).

| 🧱 Step | 🔧 How (chapter 16) |
|---|---|
| Expose | `project.agents.update_details(agent_endpoint=... a2a, agent_card=...)` |
| Discover | `GET .../agents/<name>/endpoint/protocols/a2a/agentCard/v1.0` with an Entra token |
| Call from any client | `a2a-sdk` (`A2ACardResolver`, `create_client`) |
| Call from a Foundry agent | project connection (`RemoteA2A`) + `A2ATool(a2a_version=V1_0, project_connection_id=...)` |
| Authorize | role **Foundry Agent Consumer** for the caller's identity on the target project or agent |

```mermaid
sequenceDiagram
    participant U as 🧑 User
    participant O as 🤖 jarvis-orchestrator
    participant F as 🤖 friday-finance
    participant M as ⚡ stark-mcp
    U->>O: invoice question
    O->>F: A2A message (Entra token, v1.0)
    F->>M: check_invoice_approval (MCP)
    M-->>F: within_limit
    F-->>O: review + decision
    O-->>U: answer
```

> ⚠️ Unrequested version selection defaults to preview v0.3: always use the v1.0 card or the `A2A-Version: 1.0` header. Role assignments need a minute to propagate. Not verified against a live subscription.
