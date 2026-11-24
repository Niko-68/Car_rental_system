import datetime as dt
import os
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from models import Invoice, Reservation

TAX_RATE = Decimal(os.getenv("TAX_RATE", "0"))  # e.g. 0.20 for 20% VAT


def _money(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"))


def compute_amounts(res: Reservation, extra_fees: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    base = _money(res.total_price)
    extra = _money(extra_fees)
    tax = _money((base + extra) * TAX_RATE)
    return base, tax, base + extra + tax


def upsert_invoice(db: Session, res: Reservation, extra_fees: Decimal | None = None) -> Invoice:
    """Create the reservation invoice, or update its extra fees."""
    inv = res.invoice
    if inv is None:
        extra = extra_fees or Decimal("0")
        base, tax, total = compute_amounts(res, extra)
        inv = Invoice(
            reservation_id=res.id,
            invoice_number=f"INV-{dt.date.today():%Y}-{res.id:06d}",
            issue_date=dt.date.today(),
            base_amount=base, extra_fees=extra, tax_amount=tax, total_amount=total,
        )
        db.add(inv)
    elif extra_fees is not None:
        base, tax, total = compute_amounts(res, extra_fees)
        inv.extra_fees, inv.tax_amount, inv.total_amount = extra_fees, tax, total
    db.flush()
    return inv


def build_invoice_pdf(res: Reservation) -> bytes:
    inv, car, user = res.invoice, res.listing.car, res.customer.user
    days = max((res.end_date - res.start_date).days, 1)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    st = getSampleStyleSheet()
    story = [
        Paragraph(f"Invoice {inv.invoice_number}", st["Title"]),
        Paragraph(f"Issue date: {inv.issue_date} &nbsp;|&nbsp; Reservation #{res.id}", st["Normal"]),
        Spacer(1, 0.6 * cm),
        Paragraph("Customer", st["Heading3"]),
        Paragraph(f"{user.name} {user.last_name}<br/>{user.email}", st["Normal"]),
        Spacer(1, 0.4 * cm),
        Paragraph("Vehicle", st["Heading3"]),
        Paragraph(f"{car.brand} {car.model} ({car.year}) - {car.seats} seats<br/>"
                  f"Plate: {car.plate}", st["Normal"]),
        Spacer(1, 0.6 * cm),
    ]
    rows = [
        ["Description", "Qty", "Unit price", "Amount"],
        [f"Rental {res.start_date} to {res.end_date}", f"{days} day(s)",
         f"{float(res.listing.price):.2f}", f"{float(inv.base_amount):.2f}"],
    ]
    if inv.extra_fees:
        rows.append(["Extra fees (damage / late return)", "", "", f"{float(inv.extra_fees):.2f}"])
    if inv.tax_amount:
        rows.append(["Tax", "", "", f"{float(inv.tax_amount):.2f}"])
    rows.append(["", "", "TOTAL", f"{float(inv.total_amount):.2f}"])

    table = Table(rows, colWidths=[8 * cm, 3 * cm, 3 * cm, 3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(table)
    paid = [p for p in res.payments if p.status == "paid"]
    if paid:
        story += [Spacer(1, 0.6 * cm), Paragraph("Payments", st["Heading3"])]
        for p in paid:
            story.append(Paragraph(f"{p.date} - {p.method} - {float(p.amount):.2f} {p.currency}", st["Normal"]))
    doc.build(story)
    return buf.getvalue()
