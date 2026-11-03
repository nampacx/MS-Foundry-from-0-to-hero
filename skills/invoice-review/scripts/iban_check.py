"""Validate a payment IBAN (ISO 13616 mod-97 checksum) and compare it with the vendor's account on file.

Usage:  python scripts/iban_check.py "DE89 3704 0044 0532 0130 00" --vendor "Pym Particle Supply Co."
Output: {"ok": ..., "iban": ..., "checksum_valid": ..., "matches_vendor_master": ...}, exit code 0 or 1.
A valid IBAN that differs from the one on file is the classic "we changed our bank details" fraud.
"""
from __future__ import annotations

import argparse
import re

from _common import done, find_vendor


def checksum_valid(iban: str) -> bool:
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", iban):
        return False
    rearranged = iban[4:] + iban[:4]
    return int("".join(str(int(c, 36)) for c in rearranged)) % 97 == 1   # A=10 ... Z=35


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("iban", help="IBAN, spaces allowed")
    parser.add_argument("--vendor", help="vendor name: also compare with the IBAN in assets/vendors.csv")
    args = parser.parse_args()
    iban = re.sub(r"\s+", "", args.iban).upper()
    result = {"iban": iban, "checksum_valid": checksum_valid(iban)}
    ok = result["checksum_valid"]
    if args.vendor:
        vendor = find_vendor(args.vendor)
        on_file = (vendor or {}).get("iban") or None
        result["matches_vendor_master"] = on_file == iban if on_file else None
        if on_file is None:
            result["note"] = "no IBAN on file for this vendor"
        elif on_file != iban:
            result["note"] = f"vendor master has {on_file[:4]}...{on_file[-4:]}: bank details changed, verify by phone"
        ok = ok and result["matches_vendor_master"] is True
    done(ok, **result)


if __name__ == "__main__":
    main()
