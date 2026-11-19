from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.authentication.email_auth.models.email_request import EmailRequest
from app.authentication.email_auth.send_auth_email import send_email
from app.core.security import generate_numeric_otp
from app.db.models import User, VerificationToken
from app.db.session import get_db

router = APIRouter()


@router.post("/email/otp/resend")
async def resend_signup_otp(
    payload: EmailRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    email = str(payload.email).strip().lower()

    user = db.query(User).filter(User.email == email).first()
    if user and not user.is_verified:
        # Invalidate old signup tokens
        db.query(VerificationToken).filter(
            VerificationToken.email == email,
            VerificationToken.token_type == "signup",
            VerificationToken.is_used == False,  # noqa: E712
        ).update({"is_used": True})

        # Generate new OTP
        otp = generate_numeric_otp(6)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        token_record = VerificationToken(
            email=email,
            token=otp,
            token_type="signup",
            expires_at=expires_at,
            is_used=False,
        )
        db.add(token_record)
        db.commit()

        # Send verification email
        await send_email(email, "email_verification", otp)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": "If the address has a pending account, a verification email has been sent."},
    )
