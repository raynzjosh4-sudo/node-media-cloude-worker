from pydantic import Field

from app.authentication.email_auth.models.email_request import EmailRequest


class OtpVerifyRequest(EmailRequest):
    token: str = Field(min_length=6, max_length=8)
