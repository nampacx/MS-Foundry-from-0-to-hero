"""Shared by the invoice-review scripts: the skill's asset files and the one output contract.

Every script prints one JSON object and exits with 0 (check passed) or 1 (check failed).
Standard library only: the scripts run wherever there is a Python 3.9+ (the harness sandbox, your laptop).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def norm(text: str) -> str:
    """Compare names without case, punctuation or extra spaces: 'Pym Particle Supply Co.' == 'pym particle supply co'."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).casefold()).strip()


def read_csv(name: str) -> list[dict]:
    with open(ASSETS / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_vendor(name: str) -> dict | None:
    return next((v for v in read_csv("vendors.csv") if norm(v["vendor"]) == norm(name)), None)


def done(ok: bool, **result) -> None:
    print(json.dumps({"ok": ok, **result}, ensure_ascii=False))
    sys.exit(0 if ok else 1)
