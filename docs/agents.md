# 🤖 Prompt agents, hosted agents and their tools

> 💡 **TL;DR:** A Foundry **agent** has a name and numbered **versions**. A **prompt agent** is configuration (model, instructions, tools) that Foundry runs. A **hosted agent** is your own code that Foundry runs in a managed container. Both are called the same way: a Responses API call with an `agent_reference`, usually inside a **conversation**.

| 🧾 | 🧩 Prompt agent | 🏗️ Hosted agent |
|---|---|---|
| You provide | `PromptAgentDefinition` | code + `azure.yaml` service |
| Created with | `agents.create_version` / [deploy_agents.py](../scripts/deploy_agents.py) | `azd deploy` ([main.py](../src/jarvis-hosted/main.py)) |
| Logic | the model + tools | anything your code does |
| Good for | fast start, simple tool use | custom logic, frameworks, own libraries |
| Chapter | [04](../notebooks/04_jarvis_prompt_agent.ipynb) · [05](../notebooks/05_tools_function_and_builtin.ipynb) · [06](../notebooks/06_mcp_tools.ipynb) | [09](../notebooks/09_hosted_agent.ipynb) |

---

## 🗺️ The big picture

```mermaid
sequenceDiagram
    participant C as 🧑‍💻 Your code
    participant F as ☁️ Foundry Agent Service
    participant M as 🧠 Model
    participant T as 🛠️ Tool (function · MCP · A2A · built-in)
    C->>F: responses.create(conversation, input, agent_reference)
    F->>F: load agent version + conversation items
    F->>M: instructions + history + tool definitions
    M-->>F: tool call
    alt executed by Foundry (code interpreter, MCP, search)
        F->>T: call tool
        T-->>F: result
    else function tool (your code)
        F-->>C: function_call item
        C->>F: function_call_output
    end
    F->>M: results
    M-->>F: answer
    F-->>C: response (output_text, tool items, usage)
```

---

## 1️⃣ Versions

`create_version` with an existing name adds a version; old ones stay. A call without a version uses the latest. Treat a version like a release: review the definition, deploy, evaluate (chapter 10), then keep or delete.

## 2️⃣ Who runs a tool?

| 🛠️ Tool | 🏃 Executor | 🔑 You need |
|---|---|---|
| Function | your code (loop on `function_call`) | the function and its JSON schema |
| Code interpreter | Foundry sandbox | nothing |
| File search | Foundry | a vector store |
| Web search | Foundry | nothing (⚠️ data leaves the Azure boundary) |
| MCP | the remote MCP server | URL, optional project connection |
| A2A | the remote agent | project connection |

## 3️⃣ Approvals

MCP tools default to `require_approval="always"`: the response contains `mcp_approval_request` items and the run only continues after your `mcp_approval_response`. [ask_agent()](../notebooks/stark_helpers.py) in the helpers shows the loop. Deny by default; approve only server and tool names you expect.

## 4️⃣ Hosted agents in short

`azd deploy` zips [src/jarvis-hosted](../src/jarvis-hosted/main.py) and Foundry builds it remotely (code mode, no Docker). The container gets its own Entra identity and `FOUNDRY_PROJECT_ENDPOINT` from the platform. The `ResponsesHostServer` speaks the Responses protocol, so conversations, streaming and tracing work like for prompt agents.

> ⚠️ **Demo-grade / unverified:** the hosted-agent `azure.yaml` service in this repo was written from the Microsoft Learn reference and has not been deployed in a live subscription. If `azd` rejects a field, run `azd ai agent init -m <sample azure.yaml> --deploy-mode code` in a scratch folder and compare.
