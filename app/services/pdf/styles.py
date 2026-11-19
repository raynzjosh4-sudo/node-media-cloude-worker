"""
Design tokens, color palette, and asset helpers for ReportLab PDF generation.
Faithfully mirrors Flutter's PdfTheme & OrderPdfService.
"""
import io
from pathlib import Path
import qrcode
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Image

PRIMARY_COLOR = HexColor("#00BFFF")       # Brand sky blue
DARK_BG = HexColor("#0D0D1A")             # Executive Navy/Black
BODY_TEXT = HexColor("#1A1A2E")           # Dark Charcoal
HEADER_TEXT = white                       # White
SUBTLE_COLOR = HexColor("#71717A")        # Zinc/Grey
BORDER_COLOR = HexColor("#E4E4E7")        # Subtle borders
BORDER_DARK = HexColor("#3F3F46")         # Dark border for cards
LIGHT_BG = HexColor("#FAFAFA")            # Very light grey for cards
CARD_FILL = HexColor("#F4F4F5")
ACCENT_GREEN = HexColor("#22C55E")
ACCENT_RED = HexColor("#EF4444")

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
NODE_ICON_PATH = STATIC_DIR / "nodeicon.png"
NEXUS_ICON_PATH = STATIC_DIR / "nexus.png"


def _format_ugx(val: float) -> str:
    """Format float into Ugandan Shillings currency string."""
    try:
        return f"UGX {int(round(float(val))):,}"
    except (ValueError, TypeError):
        return f"UGX {val}"


def _make_qr_image(data: str, size: float = 70.0) -> Image:
    """Generate scannable QR code in-memory for digital delivery clearance."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image(buf, width=size, height=size)
