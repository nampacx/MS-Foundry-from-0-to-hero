"""Generate the sample documents for the Foundry Tools chapters (12, 13, 15): invoice PDFs, a receipt and a whiteboard photo.

Usage: python scripts/make_sample_docs.py     (needs: pip install pillow reportlab; outputs are committed in data/docs/)
All names, numbers and addresses are fictional.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "data" / "docs"
OUT.mkdir(parents=True, exist_ok=True)


def invoice(path: Path, number: str, date: str, vendor: str, lines: list[tuple[str, int, float]]) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm)
    subtotal = sum(q * p for _, q, p in lines)
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + tax, 2)
    rows = [["Description", "Qty", "Unit price", "Amount"]] + [[d, str(q), f"${p:,.2f}", f"${q * p:,.2f}"] for d, q, p in lines]
    rows += [["", "", "Subtotal", f"${subtotal:,.2f}"], ["", "", "Tax (8%)", f"${tax:,.2f}"], ["", "", "Total due", f"${total:,.2f}"]]
    table = Table(rows, colWidths=[90 * mm, 20 * mm, 30 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b71c1c")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, len(lines)), 0.5, colors.grey), ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story = [
        Paragraph(f"<b>{vendor}</b>", styles["Title"]),
        Paragraph("12 Quantum Lane, Queens, NY 11101", styles["Normal"]),
        Spacer(1, 8 * mm),
        Paragraph(f"<b>INVOICE</b> No. {number}", styles["Heading2"]),
        Paragraph(f"Invoice date: {date}<br/>Due date: 2026-11-30<br/>Purchase order: PO-7781", styles["Normal"]),
        Spacer(1, 6 * mm),
        Paragraph("Bill to:<br/><b>Stark Industries</b><br/>200 Park Avenue, New York, NY 10166", styles["Normal"]),
        Spacer(1, 8 * mm),
        table,
        Spacer(1, 10 * mm),
        Paragraph("Payment terms: net 30. Please quote the invoice number on your transfer.", styles["Italic"]),
    ]
    doc.build(story)
    print("wrote", path.name, f"(total {total:,.2f})")


def text_image(path: Path, title: str, body: list[str], size=(900, 620), bg="white", fg="black", slight_rotation=0) -> None:
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    big, small = ImageFont.load_default(size=34), ImageFont.load_default(size=26)
    d.text((40, 30), title, fill=fg, font=big)
    y = 100
    for line in body:
        d.text((40, y), line, fill=fg, font=small)
        y += 48
    if slight_rotation:
        img = img.rotate(slight_rotation, expand=True, fillcolor=bg)
    img.save(path)
    print("wrote", path.name)


if __name__ == "__main__":
    invoice(OUT / "invoice-pym-4471.pdf", "4471", "2026-10-02", "Pym Particle Supply Co.",
            [("Pym particles, 10 g vial", 4, 450.00), ("Shrink/grow regulator", 1, 1200.00), ("Shipping and handling", 1, 85.50)])
    invoice(OUT / "invoice-oscorp-9930.pdf", "9930", "2026-10-09", "Oscorp Materials",
            [("Vibranium alloy sheet 1 m2", 6, 15000.00), ("Express freight", 1, 2400.00)])
    text_image(OUT / "receipt-dummy-cafe.png", "DUM-E'S CAFE", [
        "Malibu, CA   2026-10-11 08:14", "-" * 34, "2x Espresso            $7.00", "1x Smoothie (no spill)  $6.50",
        "Tax                    $1.08", "-" * 34, "TOTAL                 $14.58", "Thank you, sir!"], size=(620, 560))
    text_image(OUT / "whiteboard-workshop.png", "WORKSHOP TODO", [
        "1. Service arc reactor (Pepper present!)", "2. Mark 86 gauntlet: fit test Friday", "3. Teach Dummy NOT to spill",
        "4. Order Pym particles (PO-7781)", "Owner: T. Stark   Due: 2026-10-30"], size=(980, 420), bg="#f4f1de", slight_rotation=2)
