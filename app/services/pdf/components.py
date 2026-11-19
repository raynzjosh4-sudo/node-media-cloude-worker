"""
Visual building blocks and flowable tables for N.O.D.E. Order Spec Sheet PDF.
"""
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    Table,
    TableStyle,
)
from app.services.pdf.styles import (
    BORDER_COLOR,
    CARD_FILL,
    DARK_BG,
    LIGHT_BG,
    NODE_ICON_PATH,
    PRIMARY_COLOR,
    _format_ugx,
    _make_qr_image,
)


def build_header(date_str: str, page_width: float) -> Table:
    """Build the dark executive top banner with logo and official spec sheet badge."""
    header_logo_cells = []
    if NODE_ICON_PATH.exists():
        logo_img = Image(str(NODE_ICON_PATH), width=28, height=28)
        header_logo_cells.append(logo_img)
    else:
        header_logo_cells.append(Paragraph("<font color='#00BFFF'>●</font>", ParagraphStyle("Bullet", fontSize=18)))

    brand_para = Paragraph(
        "<font size='18' color='#FFFFFF'><b>N.O.D.E.</b></font><br/>"
        "<font size='6.5' color='#71717A'><b>NATIONAL ORDER &amp; DISTRIBUTION EXCHANGE</b></font>",
        ParagraphStyle("BrandHead", leading=11),
    )

    badge_meta_para = Paragraph(
        f"<para align='right'>"
        f"<font size='7' color='#00BFFF'><b>[ OFFICIAL SPEC SHEET ]</b></font><br/>"
        f"<font size='7' color='#71717A'><b>ISSUED: {date_str.upper()}</b></font>"
        f"</para>",
        ParagraphStyle("MetaHead", leading=10),
    )

    header_table = Table(
        [[header_logo_cells[0], brand_para, badge_meta_para]],
        colWidths=[34, page_width - 174, 140],
    )
    header_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ])
    )
    return header_table


def build_merchant_bar(buyer_user: dict, buyer_business: dict, page_width: float) -> Table:
    """Build merchant details card (recipient, destination depot, contact)."""
    buyer_name = (buyer_user.get("full_name") or "MERCHANT BUYER").upper()
    biz_legal = buyer_business.get("legal_name") or buyer_user.get("email") or "Wholesale Account"
    city = (buyer_business.get("city") or "KAMPALA").upper()
    address = buyer_business.get("physical_address") or "Headquarters / Central Depot"
    phone = buyer_business.get("phone_number") or buyer_user.get("phone_number") or "+256 700 000 000"

    merch_col1 = Paragraph(
        f"<font size='6' color='#71717A'><b>ISSUED TO MERCHANT</b></font><br/>"
        f"<font size='8.5' color='#1A1A2E'><b>{buyer_name}</b></font><br/>"
        f"<font size='6.5' color='#71717A'>{biz_legal}</font>",
        ParagraphStyle("Merch1", leading=9),
    )
    merch_col2 = Paragraph(
        f"<font size='6' color='#71717A'><b>LOGISTICS ORIGIN / DESTINATION</b></font><br/>"
        f"<font size='8.5' color='#1A1A2E'><b>{city}</b></font><br/>"
        f"<font size='6.5' color='#71717A'>{address}</font>",
        ParagraphStyle("Merch2", leading=9),
    )
    merch_col3 = Paragraph(
        f"<para align='right'>"
        f"<font size='6' color='#71717A'><b>CONTACT REGISTRY</b></font><br/>"
        f"<font size='8.5' color='#1A1A2E'><b>{phone}</b></font><br/>"
        f"<font size='6.5' color='#00BFFF'><b>NODE PARTNER NETWORK</b></font>"
        f"</para>",
        ParagraphStyle("Merch3", leading=9),
    )

    merchant_table = Table(
        [[merch_col1, merch_col2, merch_col3]],
        colWidths=[page_width * 0.36, page_width * 0.38, page_width * 0.26],
    )
    merchant_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ])
    )
    return merchant_table


def build_consolidation_table(total_units: int, grand_total: float, page_width: float) -> Table:
    """Build order total consolidation and value bar."""
    consol_left = Paragraph(
        f"<font size='6.5' color='#71717A'><b>ORDER CONSOLIDATION SUMMARY</b></font><br/>"
        f"<font size='8' color='#18181B'><b>Total Consolidated Units: {total_units}</b></font>",
        ParagraphStyle("ConsolLeft", leading=9),
    )
    consol_right = Paragraph(
        f"<para align='right'>"
        f"<font size='7' color='#18181B'><b>GRAND TOTAL VALUE</b></font><br/>"
        f"<font size='14' color='#00BFFF'><b>{_format_ugx(grand_total)}</b></font>"
        f"</para>",
        ParagraphStyle("ConsolRight", leading=13),
    )
    consol_table = Table([[consol_left, consol_right]], colWidths=[page_width * 0.5, page_width * 0.5])
    consol_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_FILL),
            ("LINEABOVE", (0, 0), (-1, -1), 2, PRIMARY_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ])
    )
    return consol_table


def build_verification_qr_table(order_id: str, page_width: float) -> Table:
    """Build digital clearance token with QR code for delivery receipt verification."""
    qr_img = _make_qr_image(order_id, size=65)
    qr_desc_para = Paragraph(
        f"<font size='8' color='#00BFFF'><b>DELIVERY VERIFICATION CLEARANCE</b></font><br/>"
        f"<font size='6.5' color='#FFFFFF'>This document acts as the official ownership token for the wholesale items listed. "
        f"The recipient merchant must scan the QR code using the N.O.D.E. app upon receipt to verify and complete custody transfer.</font><br/><br/>"
        f"<font size='6.5' color='#A1A1AA'><b>TOKEN ID: {order_id}</b></font>",
        ParagraphStyle("QRDesc", leading=8.5),
    )
    qr_table = Table([[qr_img, qr_desc_para]], colWidths=[75, page_width - 75])
    qr_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ])
    )
    return qr_table


def build_footer() -> list:
    """Build document running divider line and platform attribution footer."""
    footer_text = Paragraph(
        f"<font size='6.5' color='#71717A'>Generated by N.O.D.E. Wholesale Platform in association with NEXUS &bull; Official Digital B2B Clearance Record</font>",
        ParagraphStyle("FootText"),
    )
    return [
        HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=4),
        footer_text,
    ]
