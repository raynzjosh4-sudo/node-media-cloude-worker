import logging
from uuid import uuid4
import httpx
from fastapi import HTTPException, status

from app.authentication.email_auth.render_email_template import render_email_template
from app.core.config import is_production, resend_api_key, resend_from_email

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def send_email(
    to: str,
    template: str,
    code: str,
    *,
    subject: str | None = None,
    request_id: str | None = None,
    **extra_values: str,
) -> None:
    """
    Unified one-line helper to send an email template with a code.

    Usage:
        await send_email(email, "email_verification", otp)
        await send_email(email, "password_reset", reset_link)
    """
    # Auto-append .html if omitted (e.g. "email_verification" -> "email_verification.html")
    template_name = template if template.endswith(".html") else f"{template}.html"

    # Default subjects based on template type
    if not subject:
        if "verification" in template_name or "otp" in template_name:
            subject = "Your N.O.D.E. verification code"
        elif "password" in template_name or "reset" in template_name:
            subject = "Reset your N.O.D.E. password"
        else:
            subject = "N.O.D.E. Notification"

    req_id = request_id or uuid4().hex
    values = {
        "TOKEN": str(code),
        "CODE": str(code),
        "ACTION_LINK": str(code),
        **extra_values,
    }

    await send_auth_email(
        recipient=to,
        subject=subject,
        template_name=template_name,
        request_id=req_id,
        template_values=values,
    )


async def send_auth_email(
    *,
    recipient: str,
    subject: str,
    template_name: str,
    request_id: str,
    template_values: dict[str, str],
) -> None:
    api_key = resend_api_key()
    from_email = resend_from_email()

    # Format 'from' name if needed
    if "<" not in from_email:
        sender = f"N.O.D.E. <{from_email}>"
    else:
        sender = from_email

    html_content = render_email_template(template_name, **template_values)
    text_content = render_email_template(
        template_name.replace(".html", ".txt"),
        escape_values=False,
        **template_values,
    )

    # If no Resend API key is configured yet
    if not api_key:
        if not is_production():
            logger.info(
                "[DEV MODE] RESEND_API_KEY not set. OTP code logged: %s",
                template_values,
                extra={"request_id": request_id},
            )
            print("\n=======================================================")
            print(f"📧 [DEV EMAIL SIMULATION - RESEND KEY NOT SET]")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Verification Code: {template_values.get('TOKEN', template_values)}")
            print("=======================================================\n")
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured on the server.",
        )

    # Call Resend REST API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": sender,
        "to": [recipient],
        "subject": subject,
        "html": html_content,
        "text": text_content,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                RESEND_API_URL,
                headers=headers,
                json=payload,
            )

        if response.status_code in (200, 201):
            logger.info("Resend email sent successfully to %s", recipient, extra={"request_id": request_id})
            return

        error_data = response.json() if "application/json" in response.headers.get("content-type", "") else response.text
        logger.error(
            "Resend API error (HTTP %s): %s",
            response.status_code,
            error_data,
            extra={"request_id": request_id},
        )

        if not is_production():
            print("\n=======================================================")
            print(f"⚠️ [RESEND API RETURNED HTTP {response.status_code}]")
            print(f"Error details: {error_data}")
            print(f"To: {recipient}")
            print(f"Verification Code: {template_values.get('TOKEN', template_values)}")
            print("=======================================================\n")
            return

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send verification email via Resend. Please check your Resend domain/API key.",
        )

    except httpx.RequestError as exc:
        logger.error("Network error connecting to Resend: %s", exc, extra={"request_id": request_id})
        if not is_production():
            print("\n=======================================================")
            print(f"⚠️ [RESEND NETWORK ERROR: {exc}]")
            print(f"Verification Code: {template_values.get('TOKEN', template_values)}")
            print("=======================================================\n")
            return
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not connect to email delivery service.",
        ) from exc
