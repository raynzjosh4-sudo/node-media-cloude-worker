"""
PDF Document assembler for official N.O.D.E. Order Spec Sheets.
"""
import io
from datetime import datetime, timezone
from typing import Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Spacer

from app.services.pdf.components import (
    build_consolidation_table,
    build_footer,
    build_header,
    build_merchant_bar,
    build_verification_qr_table,
)
from app.services.pdf.matrix import build_entry_flowables


def generate_order_pdf(
    order: dict[str, Any],
    buyer_user: Optional[dict[str, Any]] = None,
    buyer_business: Optional[dict[str, Any]] = None,
    supplier_user: Optional[dict[str, Any]] = None,
    supplier_business: Optional[dict[str, Any]] = None,
) -> bytes:
    """
    Generate an official N.O.D.E. Order Spec Sheet / Invoice PDF.
    Returns the binary content as bytes.
    """
    order_id = str(order.get("order_id") or order.get("id") or "ORD-UNKNOWN")
    created_at_str = order.get("created_at") or datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        date_str = dt.strftime("%B %d, %Y")
    except Exception:
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    buyer_user = buyer_user or {}
    buyer_business = buyer_business or {}
    supplier_business = supplier_business or {}

    buffer = io.BytesIO()

    # Page setup - A4 with 30pt horizontal margin
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=25,
        bottomMargin=35,
    )

    page_width = A4[0] - 60  # total usable content width (~535pt)
    story = []

    # 1. Header (Dark Executive Bleed)
    story.append(build_header(date_str, page_width))

    # 2. Merchant Identity Bar
    story.append(build_merchant_bar(buyer_user, buyer_business, page_width))
    story.append(Spacer(1, 14))

    # 3. Entries / Line Items Breakdown
    entries = order.get("entries_json") or []
    if isinstance(entries, dict):
        entries = [entries]

    grand_total_calc = 0.0
    total_units_calc = 0
    default_business_name = str(order.get("business_name") or "")

    for entry in entries:
        flowables, entry_total, units = build_entry_flowables(
            entry=entry,
            supplier_business=supplier_business,
            default_business_name=default_business_name,
            page_width=page_width,
        )
        story.extend(flowables)
        grand_total_calc += entry_total
        total_units_calc += units

    # 4. Order Consolidation Summary / Grand Total
    grand_total_display = float(order.get("total_amount") or grand_total_calc)
    story.append(build_consolidation_table(total_units_calc, grand_total_display, page_width))
    story.append(Spacer(1, 14))

    # 5. Delivery Verification Clearance (QR Code Block)
    story.append(build_verification_qr_table(order_id, page_width))
    story.append(Spacer(1, 12))

    # 6. Footer
    story.extend(build_footer())

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
