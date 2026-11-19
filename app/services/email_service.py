"""
Unified email delivery service for N.O.D.E. Wholesale Platform.
Supports HTML emails and file attachments (e.g. Order PDF) via Resend API.
Templates are stored cleanly in app/templates/.
"""
import base64
import logging
from pathlib import Path
from typing import Any, Optional
import httpx

from app.core.config import is_production, resend_api_key, resend_from_email
from app.notifications.supabase_client import register_device_token, _url, HEADERS

logger = logging.getLogger(__name__)
RESEND_API_URL = "https://api.resend.com/emails"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_order_template(
    template_name: str,
    context: dict[str, str],
) -> str:
    """Load HTML template from app/templates and substitute {{KEY}} tags."""
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Email template not found: {template_path}")
    
    content = template_path.read_text(encoding="utf-8")
    for key, val in context.items():
        content = content.replace(f"{{{{{key}}}}}", str(val))
    return content


async def send_order_email(
    *,
    recipient: str,
    subject: str,
    html_content: str,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: str = "Order_Document.pdf",
) -> bool:
    """
    Send an order notification email, optionally with an attached PDF file.
    """
    api_key = resend_api_key()
    from_email = resend_from_email()
    sender = f"N.O.D.E. Wholesale <{from_email}>" if "<" not in from_email else from_email

    payload: dict[str, Any] = {
        "from": sender,
        "to": [recipient],
        "subject": subject,
        "html": html_content,
    }

    if pdf_bytes:
        encoded_content = base64.b64encode(pdf_bytes).decode("utf-8")
        payload["attachments"] = [
            {
                "filename": pdf_filename,
                "content": encoded_content,
            }
        ]

    if not api_key:
        print("\n=======================================================")
        print(f"📧 [DEV EMAIL SIMULATION - RESEND KEY NOT SET]")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Has PDF Attachment: {'Yes (' + str(len(pdf_bytes)) + ' bytes)' if pdf_bytes else 'No'}")
        print("=======================================================\n")
        return True

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(RESEND_API_URL, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                logger.info(f"Order email sent successfully to {recipient}")
                return True
            else:
                logger.error(f"Resend error ({resp.status_code}): {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to deliver order email to {recipient}: {e}")
        return False


async def create_in_app_notification(
    user_id: str,
    title: str,
    body: str,
    category: str = "order",
    metadata: Optional[dict[str, Any]] = None,
) -> bool:
    """
    Write a real-time notification into Supabase notifications_table.
    """
    payload = {
        "user_id": user_id,
        "title": title,
        "body": body,
        "category": category,
        "is_unread": True,
        "metadata": metadata or {},
    }
    headers = {**HEADERS, "Prefer": "return=representation"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(_url("notifications_table"), json=payload, headers=headers)
            return resp.status_code in (200, 201)
    except Exception as e:
        logger.error(f"Failed to insert in-app notification: {e}")
        return False


def build_order_status_email_html(
    *,
    recipient_name: str,
    order_id: str,
    status_title: str,
    status_color: str,
    message: str,
    order_total_ugx: str,
    is_supplier: bool = False,
) -> str:
    """
    Render order status update email from app/templates/order_status_update.html.
    """
    role_sub = "Supplier Copy" if is_supplier else "Merchant Copy"
    context = {
        "RECIPIENT_NAME": recipient_name,
        "ORDER_ID": order_id,
        "STATUS_TITLE": status_title,
        "STATUS_COLOR": status_color,
        "MESSAGE": message,
        "ORDER_TOTAL_UGX": order_total_ugx,
        "ROLE_SUB": role_sub,
    }
    return render_order_template("order_status_update.html", context)


def build_supplier_status_email_html(
    *,
    recipient_name: str,
    user_id: str,
    is_approved: bool,
) -> str:
    """
    Render supplier approval or revocation email from app/templates/supplier_status_update.html.
    """
    if is_approved:
        header_badge = "OFFICIAL SUPPLIER APPROVAL"
        status_title = "Congratulations! Your Supplier Account is Active"
        accent_color = "#22C55E"
        message = "Your business profile has been thoroughly reviewed and confirmed by platform administration. You now possess full supplier privileges."
        next_steps = "You can now publish products, configure tiered wholesale pricing, manage catalog listings, and fulfill incoming merchant orders directly."
    else:
        header_badge = "SUPPLIER PRIVILEGES REVOCATION"
        status_title = "Supplier Privileges Have Been Revoked"
        accent_color = "#EF4444"
        message = "Your supplier status has been revoked by administration. Your account has returned to standard customer/buyer tier."
        next_steps = "You will no longer be able to post new products or update existing inventory listings. Existing pending orders must still be completed."

    context = {
        "RECIPIENT_NAME": recipient_name,
        "USER_ID": user_id,
        "HEADER_BADGE": header_badge,
        "STATUS_TITLE": status_title,
        "ACCENT_COLOR": accent_color,
        "MESSAGE": message,
        "NEXT_STEPS_TEXT": next_steps,
    }
    return render_order_template("supplier_status_update.html", context)

