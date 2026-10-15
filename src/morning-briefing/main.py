"""morning-briefing: J.A.R.V.I.S.'s morning briefing as a Foundry *hosted agent* (Microsoft Agent Framework, concurrent workflow).

Three specialists look at the workshop IN PARALLEL (suits, workshop systems, pending invoices), each through the
`stark-mcp` tools. Then J.A.R.V.I.S. merges their reports into one briefing for Tony.

The MCP server runs on Foundry's side and authenticates with the project connection `stark-mcp` (chapter 06), so this
container never sees the function key.

Run locally:  python main.py   (port 8088)      Deploy:  azd deploy morning-briefing
Call:         azd ai agent invoke morning-briefing "Good morning, J.A.R.V.I.S. Brief me."
"""
import os

from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework_foundry_hosting import ResponsesHostServer, WorkflowTurn, response_input_messages
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()
NO_STORE = {"store": False}  # the host keeps the history; native workflows cannot checkpoint provider-side storage
MCP_CONNECTION = "stark-mcp"  # project connection that holds the function key (created by scripts/connect_mcp.py)


def build_workflow(request=None):
    """A fresh workflow for every request (the host passes the request): a workflow keeps state, so it must never be shared."""
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],  # injected by the platform
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    def stark(allowed: list[str]):
        # least privilege: each specialist only sees the tools it needs
        return client.get_mcp_tool(name="stark", url=os.environ["STARK_MCP_URL"], project_connection_id=MCP_CONNECTION,
                                   approval_mode="never_require", allowed_tools=allowed)

    suits = client.as_agent(name="suits", default_options=NO_STORE, tools=[stark(["list_suits", "get_suit"])], instructions=(
        "You are the suit officer. Use your tools: list the suits, then check each one. "
        "Report which suits are ready for duty in two sentences."))
    workshop = client.as_agent(name="workshop", default_options=NO_STORE, tools=[stark(["get_workshop_status"])], instructions=(
        "You are the workshop officer. Check the arc reactor, the fabrication bay and the hangar with your tool. "
        "Report in two sentences."))
    finance = client.as_agent(name="finance", default_options=NO_STORE, tools=[stark(["check_invoice_approval"])], instructions=(
        "You are the finance officer. Two invoices wait for Pepper Potts: Pym Particle Supply 3,332.34 USD and "
        "Oscorp Materials 99,792.00 USD. Check both with your tool. Report in two sentences."))
    jarvis = client.as_agent(name="jarvis", default_options=NO_STORE, instructions=(
        "You are J.A.R.V.I.S., dry and witty, addressing Tony Stark as sir. Merge the three reports into a morning "
        "briefing of at most five lines. Mention anything that needs his attention."))

    async def brief(results) -> str:
        """The aggregator: runs once all three specialists are done, and its text is the workflow's only output."""
        reports = "\n".join(f"[{r.executor_id}] {r.agent_response.text}" for r in results)
        return (await jarvis.run(reports)).text

    return ConcurrentBuilder(name="morning_briefing", participants=[suits, workshop, finance]).with_aggregator(brief).build()


async def parse_response(request):
    """Map the Responses request to the workflow's start input: this turn's messages."""
    return WorkflowTurn(input=await response_input_messages(request))


def main() -> None:
    ResponsesHostServer(workflow=build_workflow, parse_response=parse_response).run()


if __name__ == "__main__":
    main()
