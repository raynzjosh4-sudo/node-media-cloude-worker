import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import SmtpConfig

_SMTP_TIMEOUT = 15.0


def send_smtp_message(config: SmtpConfig, message: EmailMessage) -> None:
    context = ssl.create_default_context()
    if config.use_ssl:
        with smtplib.SMTP_SSL(
            config.host,
            config.port,
            timeout=_SMTP_TIMEOUT,
            context=context,
        ) as server:
            if config.username:
                server.login(config.username, config.password)
            server.send_message(message)
        return

    with smtplib.SMTP(config.host, config.port, timeout=_SMTP_TIMEOUT) as server:
        server.ehlo()
        if config.use_starttls:
            server.starttls(context=context)
            server.ehlo()
        if config.username:
            server.login(config.username, config.password)
        server.send_message(message)
