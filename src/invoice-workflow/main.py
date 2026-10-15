"""invoice-workflow: the chapter 15 invoice pipeline as a Foundry *hosted agent* (Microsoft Agent Framework).

Three agents run in order: extractor -> reviewer -> reporter. The workflow is hosted *natively* with
`ResponsesHostServer(workflow=..., parse_response=...)`. Hosting `workflow.as_agent()` is deprecated, because a
WorkflowAgent keeps state in memory and must not serve different users or conversations.

Run locally:  python main.py   (port 8088, reads the repo .env)      Deploy:  azd deploy invoice-workflow
Call:         azd ai agent invoke invoice-workflow "Process the invoice at data/docs/invoice-pym-4471.pdf"
"""
import json
import os
import re
from pathlib import Path
from typing import Annotated

from agent_framework import AgentExecutor, AgentExecutorResponse, WorkflowBuilder, WorkflowContext, executor, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer, WorkflowTurn, response_input_messages
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field
from typing_extensions import Never

load_dotenv()
HERE = Path(__file__).parent
NO_STORE = {"store": False}  # the host keeps the history; native workflows cannot checkpoint provider-side storage
LIMITS = {"default": 5000, "pepper potts": 250000, "tony stark": 1000000}


def env(name: str, local_fallback: str) -> str:
    """Hosted: the platform (or azure.yaml `env:`) sets `name`. Local run: fall back to the STARK_* key in the repo's .env."""
    return os.environ.get(name) or os.environ[local_fallback]


def field_value(field):
    """The typed value of a Document Intelligence field, or its raw content."""
    if field is None:
        return None
    for key in ("valueString", "valueDate", "valueNumber", "valueInteger"):
        if field.get(key) is not None:
            return str(field.get(key)) if key == "valueDate" else field.get(key)
    currency = field.get("valueCurrency")
    return currency.get("amount") if currency else field.get("content")


@tool(approval_mode="never_require")
def extract_invoice_fields(path: Annotated[str, Field(description="Invoice file, e.g. data/docs/invoice-pym-4471.pdf")]) -> str:
    """Read an invoice with Document Intelligence and return fields, line items and confidences as JSON."""
    target = (HERE / path).resolve()
    if HERE not in target.parents or not target.is_file():  # only files shipped with this agent
        shipped = sorted(str(p.relative_to(HERE)) for p in (HERE / "data").rglob("*") if p.is_file()) if (HERE / "data").is_dir() else []
        return json.dumps({"error": f"unknown invoice file '{path}'", "shipped_files": shipped})
    try:
        client = DocumentIntelligenceClient(endpoint=env("DOCUMENT_INTELLIGENCE_ENDPOINT", "STARK_ACCOUNT_ENDPOINT"), credential=DefaultAzureCredential())
        result = client.begin_analyze_document("prebuilt-invoice", AnalyzeDocumentRequest(bytes_source=target.read_bytes())).result()
    except Exception as exc:  # noqa: BLE001 - tell the model (and the logs) what went wrong instead of a bare failure
        return json.dumps({"error": f"{type(exc).__name__}: {str(exc)[:300]}"})
    if not result.documents:
        return json.dumps({"error": "no invoice found in the document"})
    f = result.documents[0].fields or {}
    items = []
    for item in (f.get("Items") or {}).get("valueArray") or []:
        obj = item.get("valueObject") or {}
        items.append({k.lower(): field_value(obj.get(k)) for k in ("Description", "Quantity", "UnitPrice", "Amount")})
    keys = ["VendorName", "InvoiceId", "InvoiceDate", "DueDate", "PurchaseOrder", "SubTotal", "TotalTax", "InvoiceTotal", "CustomerName"]
    return json.dumps({
        "fields": {k: field_value(f.get(k)) for k in keys},
        "confidence": {k: round(f[k].get("confidence") or 0, 2) for k in keys if f.get(k)},
        "items": items,
    }, default=str)


@tool(approval_mode="never_require")
def check_approval_limit(amount: Annotated[float, Field(description="Invoice total in USD")],
                         approver: Annotated[str, Field(description="e.g. 'pepper potts'")]) -> str:
    """Check whether an amount is within the approver's limit."""
    limit = LIMITS.get(approver.strip().lower(), LIMITS["default"])
    return f"limit={limit} USD, within_limit={amount <= limit}"


def skill_instructions() -> str:
    """Direct skill injection (chapter 07): the invoice-review checklist, without its front matter."""
    text = (HERE / "skills" / "invoice-review" / "SKILL.md").read_text(encoding="utf-8")
    return re.sub(r"^---.*?---\s*", "", text, flags=re.S)


@executor(id="final-message")
async def final_message(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    """The workflow's only output: plain text. (Raw streamed model updates cannot be a native workflow output.)"""
    await ctx.yield_output(response.agent_response.text)


def build_workflow(request=None):
    """A fresh workflow for every request (the host passes the request): a workflow keeps state, so it must never be shared."""
    client = FoundryChatClient(
        project_endpoint=env("FOUNDRY_PROJECT_ENDPOINT", "STARK_PROJECT_ENDPOINT"),
        model=env("MODEL_DEPLOYMENT_NAME", "STARK_CHAT_MODEL"),
        credential=DefaultAzureCredential(),
    )
    extractor = client.as_agent(name="extractor", tools=[extract_invoice_fields], default_options=NO_STORE, instructions=(
        "Extract the invoice. Call extract_invoice_fields with the path from the user, then list vendor, number, "
        "date, total and any low-confidence (<0.8) field."))
    reviewer = client.as_agent(name="reviewer", tools=[check_approval_limit], default_options=NO_STORE, instructions=(
        "You review the extracted invoice. Follow this checklist exactly:\n" + skill_instructions() +
        "\nUse check_approval_limit with approver 'pepper potts'."))
    reporter = client.as_agent(name="reporter", default_options=NO_STORE, instructions=(
        "Write a three-bullet message for Pepper Potts: what was reviewed, the decision, what she must do next."))
    steps = [AgentExecutor(a) for a in (extractor, reviewer, reporter)]
    return (
        WorkflowBuilder(name="invoice_workflow", start_executor=steps[0], output_from=[final_message])
        .add_edge(steps[0], steps[1])
        .add_edge(steps[1], steps[2])
        .add_edge(steps[2], final_message)
        .build()
    )


async def parse_response(request):
    """Map the Responses request to the workflow's start input: this turn's messages."""
    return WorkflowTurn(input=await response_input_messages(request))


def main() -> None:
    ResponsesHostServer(workflow=build_workflow, parse_response=parse_response).run()


if __name__ == "__main__":
    main()
