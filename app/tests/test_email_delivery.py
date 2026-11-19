import asyncio

from app.authentication.email_auth import send_auth_email
from app.core.config import SmtpConfig


def test_email_is_rendered_and_sent_with_text_and_html(monkeypatch) -> None:
    sent: dict[str, object] = {}
    config = SmtpConfig(
        host="smtp.example.com",
        port=587,
        username="smtp-user",
        password="smtp-password",
        from_address="no-reply@example.com",
        from_name="N.O.D.E.",
        use_ssl=False,
        use_starttls=True,
    )

    def fake_send_message(config, message) -> None:
        sent["config"] = config
        sent["message"] = message

    monkeypatch.setattr(send_auth_email, "smtp_config", lambda: config)
    monkeypatch.setattr(send_auth_email, "send_smtp_message", fake_send_message)

    asyncio.run(
        send_auth_email.send_auth_email(
            recipient="person@example.com",
            subject="Verify your email",
            template_name="email_verification.html",
            request_id="test-request-id",
            template_values={"TOKEN": "<123456>"},
        )
    )

    message = sent["message"]
    assert message["To"] == "person@example.com"
    assert message["Subject"] == "Verify your email"
    assert message.get_content_type() == "multipart/alternative"
    parts = list(message.iter_parts())
    assert len(parts) == 2
    assert "<123456>" in parts[0].get_content()
    assert "&lt;123456&gt;" in parts[1].get_content()
    assert "123456" in parts[1].get_content()
    assert "verify your email address" in parts[0].get_content().lower()


def test_email_delivery_errors_are_reported_without_credentials(monkeypatch) -> None:
    config = SmtpConfig(
        host="smtp.example.com",
        port=587,
        username="smtp-user",
        password="never-log-this",
        from_address="no-reply@example.com",
        from_name="N.O.D.E.",
        use_ssl=False,
        use_starttls=True,
    )

    def fail_send_message(config, message) -> None:
        raise OSError("SMTP connection failed")

    monkeypatch.setattr(send_auth_email, "smtp_config", lambda: config)
    monkeypatch.setattr(send_auth_email, "send_smtp_message", fail_send_message)

    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            send_auth_email.send_auth_email(
                recipient="person@example.com",
                subject="Verify your email",
                template_name="email_verification.html",
                request_id="test-request-id",
                template_values={"TOKEN": "123456"},
            )
        )

    assert error.value.status_code == 502
    assert "never-log-this" not in str(error.value.detail)
