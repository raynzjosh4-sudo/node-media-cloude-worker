"""
Background task worker for order status notifications, emails, and spec sheet attachments.
"""
from app.profile.supabase_client import fetch_business, fetch_user
from app.services.email_service import (
    build_order_status_email_html,
    create_in_app_notification,
    send_order_email,
)
from app.services.pdf_generator import _format_ugx, generate_order_pdf


async def _dispatch_order_status_notifications(
    order: dict,
    new_status: str,
    action_by_user_id: str,
):
    """
    Background worker:
    1. Fetches buyer & supplier details.
    2. Builds the official N.O.D.E. order spec sheet PDF.
    3. Sends status update email + PDF attachment to the buyer.
    4. Sends confirmation email + PDF attachment to the supplier.
    5. Writes in-app notifications to notifications_table for both parties.
    """
    order_id = str(order.get("order_id") or order.get("id"))
    buyer_id = order.get("user_id")
    supplier_id = order.get("supplier_id")
    total_amount = float(order.get("total_amount") or 0.0)
    total_ugx = _format_ugx(total_amount)

    buyer_user = (await fetch_user(buyer_id)) if buyer_id else {}
    buyer_biz = (await fetch_business(buyer_id)) if buyer_id else {}
    supplier_user = (await fetch_user(supplier_id)) if supplier_id else {}
    supplier_biz = (await fetch_business(supplier_id)) if supplier_id else {}

    # 1. Generate Order PDF
    try:
        pdf_bytes = generate_order_pdf(
            order=order,
            buyer_user=buyer_user,
            buyer_business=buyer_biz,
            supplier_user=supplier_user,
            supplier_business=supplier_biz,
        )
    except Exception as e:
        print(f"Error generating PDF in background: {e}")
        pdf_bytes = None

    # Status formatting
    status_upper = new_status.upper()
    color_map = {
        "NEW": "#00BFFF",
        "PROCESSING": "#3B82F6",
        "CONFIRMED": "#22C55E",
        "COMPLETED": "#22C55E",
        "CANCELLED": "#EF4444",
    }
    status_color = color_map.get(status_upper, "#00BFFF")

    buyer_name = (buyer_user or {}).get("full_name") or "Valued Merchant"
    buyer_email = (buyer_user or {}).get("email")
    supplier_name = (supplier_biz or {}).get("legal_name") or (supplier_user or {}).get("full_name") or "Supplier"
    supplier_email = (supplier_user or {}).get("email")

    pdf_filename = f"NODE_Order_{order_id}.pdf"

    # 2. Buyer Email & In-App Notification
    if buyer_email:
        buyer_html = build_order_status_email_html(
            recipient_name=buyer_name,
            order_id=order_id,
            status_title=f"Order Status: {status_upper}",
            status_color=status_color,
            message=f"Your wholesale order #[{order_id}] has been updated to '{status_upper}' by {supplier_name}. Please inspect the attached PDF spec sheet and verify delivery upon arrival.",
            order_total_ugx=total_ugx,
            is_supplier=False,
        )
        await send_order_email(
            recipient=buyer_email,
            subject=f"N.O.D.E. Order #{order_id} Status: {status_upper}",
            html_content=buyer_html,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
        )

    if buyer_id:
        await create_in_app_notification(
            user_id=buyer_id,
            title=f"Order #{order_id} is now {status_upper}",
            body=f"Supplier {supplier_name} has updated your order status to {status_upper}.",
            category="order",
            metadata={"order_id": order_id, "status": new_status},
        )

    # 3. Supplier Email & In-App Notification
    if supplier_email:
        supplier_html = build_order_status_email_html(
            recipient_name=supplier_name,
            order_id=order_id,
            status_title=f"Order #{order_id} Marked As {status_upper}",
            status_color=status_color,
            message=f"You updated order #[{order_id}] to '{status_upper}'. The buyer has been notified and issued their digital clearance sheet.",
            order_total_ugx=total_ugx,
            is_supplier=True,
        )
        await send_order_email(
            recipient=supplier_email,
            subject=f"Confirmation: Order #{order_id} marked as {status_upper}",
            html_content=supplier_html,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
        )

    if supplier_id and supplier_id != action_by_user_id:
        await create_in_app_notification(
            user_id=supplier_id,
            title=f"Order #{order_id} Status Changed",
            body=f"Order #[{order_id}] status transitioned to {status_upper}.",
            category="order",
            metadata={"order_id": order_id, "status": new_status},
        )
