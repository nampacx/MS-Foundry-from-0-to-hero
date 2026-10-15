"""stark-mcp: Tony Stark's workshop as an MCP server (Azure Function, Python v2, Functions MCP extension).

Foundry agents call these tools over MCP (chapter 06). The data is static on purpose so the demo needs no backends.
The tool descriptions are what the model reads to decide when to call a tool, so they are written for the model.
"""
import json
import logging

import azure.functions as func

app = func.FunctionApp()

SUITS = {
    "mark 3": {"name": "Mark III", "year": 2008, "status": "museum", "power_level": 61, "special": "gold-titanium alloy, flight"},
    "mark 7": {"name": "Mark VII", "year": 2012, "status": "destroyed", "power_level": 78, "special": "automated deployment"},
    "mark 42": {"name": "Mark XLII", "year": 2013, "status": "destroyed", "power_level": 83, "special": "prehensile modular armor"},
    "mark 85": {"name": "Mark LXXXV", "year": 2023, "status": "retired", "power_level": 97, "special": "nanotech, Infinity Gauntlet slot"},
}

WORKSHOP = {
    "arc reactor": {"status": "online", "output_gw": 3.0, "last_service": "2026-09-30"},
    "fabrication bay": {"status": "busy", "queue": ["Mark 86 gauntlet", "drone swarm test"], "eta_hours": 6},
    "hangar": {"status": "idle", "suits_stored": 12},
}

INVOICE_LIMITS = {"default": 5000, "tony stark": 1000000, "pepper potts": 250000}

_NAME_PROP = json.dumps([{"propertyName": "name", "propertyType": "string", "description": "Name, e.g. 'mark 42'."}])
_APPROVAL_PROPS = json.dumps([
    {"propertyName": "amount", "propertyType": "number", "description": "Invoice total in USD."},
    {"propertyName": "approver", "propertyType": "string", "description": "Who approves, e.g. 'pepper potts'."},
])


def _args(context: str) -> dict:
    return json.loads(context).get("arguments", {})


def _lookup(table: dict, context: str) -> str:
    key = str(_args(context).get("name", "")).strip().lower()
    logging.info("MCP lookup name=%s", key)
    item = table.get(key)
    return json.dumps(item) if item else json.dumps({"error": f"'{key}' not found", "known": sorted(table)})


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="list_suits",
    description="List all Iron Man suits with their year and status.",
    tool_properties="[]",
)
def list_suits(context: str) -> str:
    return json.dumps([{"id": k, **v} for k, v in SUITS.items()])


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="get_suit",
    description="Get details (year, status, power level, special feature) of one suit by name, e.g. 'mark 42'.",
    tool_properties=_NAME_PROP,
)
def get_suit(context: str) -> str:
    return _lookup(SUITS, context)


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="get_workshop_status",
    description="Get the status of a workshop system: 'arc reactor', 'fabrication bay' or 'hangar'.",
    tool_properties=_NAME_PROP,
)
def get_workshop_status(context: str) -> str:
    return _lookup(WORKSHOP, context)


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="check_invoice_approval",
    description="Check whether an invoice amount in USD is within the approval limit of an approver (used by the invoice workflow).",
    tool_properties=_APPROVAL_PROPS,
)
def check_invoice_approval(context: str) -> str:
    args = _args(context)
    approver = str(args.get("approver", "default")).strip().lower()
    limit = INVOICE_LIMITS.get(approver, INVOICE_LIMITS["default"])
    amount = float(args.get("amount", 0))
    return json.dumps({"approver": approver, "limit_usd": limit, "amount_usd": amount, "within_limit": amount <= limit})
