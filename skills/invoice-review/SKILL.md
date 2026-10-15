---
name: invoice-review
description: Checklist for reviewing a supplier invoice that was extracted from a document.
---

# Invoice review checklist

Use this checklist on invoice fields extracted by Document Intelligence or Content Understanding.

1. Required fields present: vendor name, invoice number, invoice date, total.
2. Total equals the sum of the line items (tolerance 0.01).
3. Invoice date is not in the future.
4. Check the approval limit with the `check_invoice_approval` tool before recommending approval.
5. End with one of: `APPROVE`, `REJECT: <reason>`, `NEEDS HUMAN REVIEW: <reason>`.

Never approve an invoice with missing required fields.
