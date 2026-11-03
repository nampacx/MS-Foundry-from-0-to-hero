"""Check an extracted invoice: required fields, arithmetic and dates.

Usage:  python scripts/check_invoice.py invoice.json
Input:  the shape of chapter 13's extract_invoice (see assets/invoice-example.json).
Output: {"ok": ..., "problems": [...], "warnings": [...], "computed": {...}}, exit code 0 or 1.
"""
from __future__ import annotations

import argparse
import json
from datetime import date

from _common import done

REQUIRED = ["VendorName", "InvoiceId", "InvoiceDate", "InvoiceTotal"]
TOLERANCE = 0.01
MIN_CONFIDENCE = 0.8


def amount(item: dict) -> float:
    """A line amount; falls back to quantity x unit price when the amount was not extracted."""
    if item.get("amount") is not None:
        return float(item["amount"])
    return float(item.get("quantity") or 1) * float(item.get("unitprice") or 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("invoice", help="path to the invoice JSON")
    invoice = json.load(open(parser.parse_args().invoice, encoding="utf-8"))
    fields, items = invoice.get("fields", {}), invoice.get("items", [])
    problems, warnings = [], []

    missing = [k for k in REQUIRED if fields.get(k) in (None, "")]
    if missing:
        problems.append(f"missing required fields: {', '.join(missing)}")

    lines = round(sum(amount(i) for i in items), 2)
    tax = float(fields.get("TotalTax") or 0)
    subtotal = float(fields["SubTotal"]) if fields.get("SubTotal") is not None else lines
    total = fields.get("InvoiceTotal")
    if items and abs(lines - subtotal) > TOLERANCE:
        problems.append(f"line items add up to {lines:,.2f}, but the subtotal says {subtotal:,.2f}")
    if total is not None and abs(subtotal + tax - float(total)) > TOLERANCE:
        problems.append(f"subtotal {subtotal:,.2f} + tax {tax:,.2f} = {subtotal + tax:,.2f}, but the total says {float(total):,.2f}")

    if fields.get("InvoiceDate"):
        try:
            if date.fromisoformat(str(fields["InvoiceDate"])[:10]) > date.today():
                problems.append(f"invoice date {fields['InvoiceDate']} is in the future")
        except ValueError:
            problems.append(f"invoice date {fields['InvoiceDate']!r} is not an ISO date (YYYY-MM-DD)")

    low = {k: c for k, c in invoice.get("confidence", {}).items() if c < MIN_CONFIDENCE}
    if low:
        warnings.append(f"low extraction confidence, double-check: {low}")

    done(not problems, problems=problems, warnings=warnings,
         computed={"lines": lines, "subtotal": subtotal, "tax": tax, "total": round(subtotal + tax, 2)})


if __name__ == "__main__":
    main()
