"""Is an invoice total within the approver's limit? (assets/approval-limits.csv)

Usage:  python scripts/approval_limit.py --approver "Pepper Potts" --total 3332.34
Output: {"ok": ..., "approver": ..., "limit_usd": ..., "total_usd": ...}, exit code 0 when within the limit.
Unknown approvers get the `default` limit, as in chapter 13's check_approval_limit and the stark-mcp tool.
"""
from __future__ import annotations

import argparse

from _common import done, norm, read_csv


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--approver", default="default", help="who approves, e.g. 'Pepper Potts'")
    parser.add_argument("--total", type=float, required=True, help="invoice total in USD")
    args = parser.parse_args()
    limits = {norm(r["approver"]): float(r["limit_usd"]) for r in read_csv("approval-limits.csv")}
    limit = limits.get(norm(args.approver), limits["default"])
    done(args.total <= limit, approver=args.approver, limit_usd=limit, total_usd=args.total)


if __name__ == "__main__":
    main()
