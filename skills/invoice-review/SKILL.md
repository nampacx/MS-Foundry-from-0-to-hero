---
name: invoice-review
description: Checklist for reviewing a supplier invoice that was extracted from a document, with scripts for the arithmetic, vendor, bank account, duplicate and approval-limit checks.
---

# Invoice review checklist

Use this checklist on invoice fields extracted by Document Intelligence or Content Understanding.

## Checklist

1. Required fields present: vendor name, invoice number, invoice date, total.
2. Line items add up to the subtotal, and subtotal plus tax equals the total (tolerance 0.01).
3. Invoice date is not in the future.
4. The vendor is approved in the vendor master, not blocked or unknown.
5. If the invoice or request names a payment IBAN: its checksum is valid and it matches the vendor's IBAN on file.
6. The same vendor and invoice number were not reviewed before.
7. Check the approval limit with the `check_invoice_approval` tool or the `approval_limit.py` script before recommending approval.
8. End with one of: `APPROVE`, `REJECT: <reason>`, `NEEDS HUMAN REVIEW: <reason>`.

Never approve an invoice with missing required fields.

## Run the checks with the scripts (when you can run shell commands)

Do not do these checks in your head. This skill ships scripts for them in its `scripts/` folder, next to this file. They use only the Python standard library.

1. Save the extracted invoice as `invoice.json` in your working directory. Use the shape of `assets/invoice-example.json`: `fields` (`VendorName`, `InvoiceId`, `InvoiceDate`, `SubTotal`, `TotalTax`, `InvoiceTotal`, ...) and `items` (`description`, `quantity`, `unitprice`, `amount`).
2. Run every command that applies from your working directory. Replace `scripts/` with the full path of this skill's `scripts/` folder if it is somewhere else:

| Step | Command |
|---|---|
| 1-3 | `python scripts/check_invoice.py invoice.json` |
| 4 | `python scripts/vendor_check.py "<VendorName>"` |
| 5 | `python scripts/iban_check.py "<IBAN>" --vendor "<VendorName>"` |
| 6 | `python scripts/ledger.py invoice.json` (records the invoice in `ledger.csv`) |
| 7 | `python scripts/approval_limit.py --approver "<approver>" --total <InvoiceTotal>` |

Each script prints one JSON line and exits with `0` (pass) or `1` (fail). Quote the failing script's message in your reason.

## Verdict

- `REJECT`: missing fields, wrong arithmetic, a future date, a blocked vendor, an invalid or changed IBAN, or a duplicate.
- `NEEDS HUMAN REVIEW`: an unknown vendor, a total above the approver's limit, or low extraction confidence on a required field.
- `APPROVE`: every check passed.

Without shell access, do steps 1 to 3 and 7 yourself and say that steps 4 to 6 were not checked.
