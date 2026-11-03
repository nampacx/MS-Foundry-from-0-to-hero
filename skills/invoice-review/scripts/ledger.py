"""Duplicate check: has this vendor's invoice number been reviewed before? Records it if not.

Usage:  python scripts/ledger.py invoice.json            (ledger.csv in the current directory, the workspace)
Output: {"ok": ..., "invoice": ..., "duplicate": ..., "first_seen": ...}, exit code 1 for a duplicate.
On the Copilot harness the workspace lives as long as the conversation, so a new conversation starts with an empty ledger.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from _common import done, norm

LEDGER = Path("ledger.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("invoice", help="path to the invoice JSON")
    fields = json.load(open(parser.parse_args().invoice, encoding="utf-8")).get("fields", {})
    key = f"{norm(fields.get('VendorName', ''))}|{str(fields.get('InvoiceId', '')).strip()}"
    rows = list(csv.DictReader(LEDGER.open(encoding="utf-8"))) if LEDGER.exists() else []
    seen = next((r for r in rows if r["key"] == key), None)
    if seen:
        done(False, invoice=key, duplicate=True, first_seen=seen["reviewed_at"])
    new = not LEDGER.exists()
    with LEDGER.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["key", "reviewed_at"])
        if new:
            writer.writeheader()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        writer.writerow({"key": key, "reviewed_at": now})
    done(True, invoice=key, duplicate=False, first_seen=now, ledger_entries=len(rows) + 1)


if __name__ == "__main__":
    main()
