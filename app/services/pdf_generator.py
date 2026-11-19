"""
N.O.D.E. Order Spec Sheet & Invoice PDF Generator.
Re-exports modular implementation from app.services.pdf.*.
"""
from app.services.pdf.generator import generate_order_pdf
from app.services.pdf.styles import _format_ugx

__all__ = [
    "generate_order_pdf",
    "_format_ugx",
]
