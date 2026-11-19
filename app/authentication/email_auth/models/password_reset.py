from pydantic import BaseModel

from app.authentication.email_auth.models.email_request import EmailRequest


class PasswordResetRequest(EmailRequest):
    redirect_to: str | None = None
