"""Look a vendor up in Stark Industries' vendor master (assets/vendors.csv).

Usage:  python scripts/vendor_check.py "Pym Particle Supply Co."
Output: {"ok": ..., "vendor": ..., "status": "approved" | "blocked" | "unknown", "note": ...}, exit code 0 only for approved.
"""
from __future__ import annotations

import argparse

from _common import done, find_vendor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("vendor", help="vendor name as written on the invoice")
    name = parser.parse_args().vendor
    vendor = find_vendor(name)
    if vendor is None:
        done(False, vendor=name, status="unknown", note="not in the vendor master, onboard the vendor first")
    done(vendor["status"] == "approved", vendor=vendor["vendor"], status=vendor["status"], note=vendor["note"])


if __name__ == "__main__":
    main()
