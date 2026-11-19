"""
Product entry line-item flowables: header banner, specs row, color-size matrix, and subtotal.
"""
from typing import Any
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

from app.services.pdf.styles import (
    BORDER_COLOR,
    BORDER_DARK,
    DARK_BG,
    LIGHT_BG,
    PRIMARY_COLOR,
    _format_ugx,
)


def build_entry_flowables(
    entry: dict[str, Any],
    supplier_business: dict[str, Any],
    default_business_name: str,
    page_width: float,
) -> tuple[list, float, int]:
    """Build product header banner, specs row, color-size matrix, and subtotal."""
    product = entry.get("savedProduct", {}).get("product") or entry.get("product") or {}
    prod_name = (product.get("name") or entry.get("name") or "Wholesale Item").upper()
    prod_brand = (product.get("brand") or "N.O.D.E.").upper()
    prod_sku = product.get("sku") or "SKU-N/A"
    total_units = int(entry.get("totalUnits") or entry.get("quantity") or 1)

    price_tiers = product.get("price_tiers") or []
    unit_price = float(product.get("srp") or 0.0)
    for t in sorted(price_tiers, key=lambda x: x.get("minQuantity", 0), reverse=True):
        if total_units >= t.get("minQuantity", 0):
            unit_price = float(t.get("price", unit_price))
            break

    entry_total = unit_price * total_units
    flowables = []

    # 1. Product Dark Header Banner
    p_title_para = Paragraph(
        f"<font size='12' color='#FFFFFF'><b>{prod_name}</b></font><br/>"
        f"<font size='7' color='#00BFFF'><b>{prod_brand}</b></font> "
        f"<font size='7' color='#71717A'>| REFERENCE SKU: {prod_sku}</font>",
        ParagraphStyle("PTitle", leading=12),
    )
    p_units_badge = Paragraph(
        f"<para align='center'><font size='8' color='#FFFFFF'><b>{total_units} UNITS</b></font></para>",
        ParagraphStyle("PUnits"),
    )
    p_header_table = Table([[p_title_para, p_units_badge]], colWidths=[page_width - 95, 95])
    p_header_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), DARK_BG),
            ("BACKGROUND", (1, 0), (1, 0), PRIMARY_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ])
    )
    flowables.append(p_header_table)

    # 2. Product Specs Row
    supplier_name = (
        supplier_business.get("legal_name")
        or product.get("supplier", {}).get("name")
        or default_business_name
        or "Verified Supplier"
    ).upper()
    current_stock = product.get("current_stock", "In Stock")
    lead_time = product.get("lead_time_days", 3)
    trading_terms = (
        product.get("trading_terms", {}).get("content")
        or "Standard wholesale trading terms apply. Goods inspected upon delivery."
    )

    specs_left = Paragraph(
        f"<font size='6' color='#71717A'><b>SUPPLIER</b></font><br/>"
        f"<font size='8' color='#FFFFFF'><b>{supplier_name}</b></font><br/>"
        f"<font size='6.5' color='#A1A1AA'>{supplier_business.get('physical_address') or 'Certified Fulfillment Depot'}</font>",
        ParagraphStyle("SpecsLeft", leading=8.5),
    )
    stock_badge = Paragraph(
        f"<font size='6' color='#71717A'><b>AVAILABILITY</b></font><br/>"
        f"<font size='7.5' color='#22C55E'><b>{current_stock} UNITS</b></font>",
        ParagraphStyle("Stk", leading=8),
    )
    lead_badge = Paragraph(
        f"<font size='6' color='#71717A'><b>LEAD TIME</b></font><br/>"
        f"<font size='7.5' color='#00BFFF'><b>{lead_time} DAYS</b></font>",
        ParagraphStyle("Lead", leading=8),
    )
    terms_block = Paragraph(
        f"<font size='6' color='#71717A'><b>TRADING TERMS</b></font><br/>"
        f"<font size='6.5' color='#A1A1AA'>{trading_terms}</font>",
        ParagraphStyle("Terms", leading=8),
    )

    specs_table = Table(
        [[specs_left, stock_badge, lead_badge, terms_block]],
        colWidths=[page_width * 0.35, page_width * 0.18, page_width * 0.15, page_width * 0.32],
    )
    specs_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("LINEBEFORE", (1, 0), (-1, -1), 0.5, BORDER_DARK),
        ])
    )
    flowables.append(specs_table)

    # 3. Matrix Data Table
    groups = entry.get("confirmedGroups") or []
    all_sizes_set = set()
    for g in groups:
        for sz in (g.get("sizeQtys") or {}).keys():
            all_sizes_set.add(sz)
    size_list = sorted(list(all_sizes_set)) if all_sizes_set else ["STD"]

    matrix_header = [Paragraph("<font size='7' color='#FFFFFF'><b>COLOR</b></font>", ParagraphStyle("HdrC"))]
    for sz in size_list:
        matrix_header.append(Paragraph(f"<para align='center'><font size='7' color='#FFFFFF'><b>{sz.upper()}</b></font></para>", ParagraphStyle("HdrSz")))
    matrix_header.append(Paragraph("<para align='center'><font size='7' color='#FFFFFF'><b>TOTAL</b></font></para>", ParagraphStyle("HdrT")))

    matrix_rows = [matrix_header]
    if groups:
        for g in groups:
            c_label = g.get("color", {}).get("label") or "Standard"
            sq = g.get("sizeQtys") or {}
            row_total = sum(int(v or 0) for v in sq.values())
            row_cells = [Paragraph(f"<font size='7.5' color='#1A1A2E'><b>{c_label}</b></font>", ParagraphStyle("ColorLbl"))]
            for sz in size_list:
                qty = sq.get(sz, 0)
                qty_str = str(qty) if qty > 0 else "-"
                q_color = "#1A1A2E" if qty > 0 else "#A1A1AA"
                row_cells.append(Paragraph(f"<para align='center'><font size='7.5' color='{q_color}'>{qty_str}</font></para>", ParagraphStyle("QC")))
            row_cells.append(Paragraph(f"<para align='center'><font size='7.5' color='#1A1A2E'><b>{row_total}</b></font></para>", ParagraphStyle("RT")))
            matrix_rows.append(row_cells)
    else:
        row_cells = [Paragraph("<font size='7.5' color='#1A1A2E'><b>Default Specification</b></font>", ParagraphStyle("DefLbl"))]
        for sz in size_list:
            row_cells.append(Paragraph(f"<para align='center'><font size='7.5' color='#1A1A2E'>{total_units}</font></para>", ParagraphStyle("DefQ")))
        row_cells.append(Paragraph(f"<para align='center'><font size='7.5' color='#1A1A2E'><b>{total_units}</b></font></para>", ParagraphStyle("DefTot")))
        matrix_rows.append(row_cells)

    num_cols = len(matrix_header)
    col_w_color = page_width * 0.40
    rem_w = page_width - col_w_color
    other_w = rem_w / (num_cols - 1)
    matrix_col_widths = [col_w_color] + [other_w] * (num_cols - 1)

    matrix_table = Table(matrix_rows, colWidths=matrix_col_widths)
    matrix_style = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for r_i in range(1, len(matrix_rows)):
        if r_i % 2 == 0:
            matrix_style.append(("BACKGROUND", (0, r_i), (-1, r_i), LIGHT_BG))
    matrix_table.setStyle(TableStyle(matrix_style))
    flowables.append(matrix_table)

    # 4. Pricing Subtotal Row
    price_summary_para = Paragraph(
        f"<para align='right'>"
        f"<font size='6.5' color='#71717A'><b>UNIT PRICE (TIERED):</b></font> "
        f"<font size='7.5' color='#1A1A2E'><b>{_format_ugx(unit_price)}</b></font>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<font size='7.5' color='#1A1A2E'><b>TOTAL ITEM VALUE:</b></font> "
        f"<font size='10' color='#00BFFF'><b>{_format_ugx(entry_total)}</b></font>"
        f"</para>",
        ParagraphStyle("SubtotPara", leading=11),
    )
    price_subtable = Table([[price_summary_para]], colWidths=[page_width])
    price_subtable.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    flowables.append(price_subtable)

    return flowables, entry_total, total_units
