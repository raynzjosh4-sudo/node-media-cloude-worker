from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.authentication.email_auth.models.password_reset import PasswordResetRequest
from app.authentication.email_auth.send_auth_email import send_email
from app.core.security import generate_numeric_otp, hash_password
from app.db.models import User, VerificationToken
from app.db.session import get_db
from app.profile import supabase_client as sb

router = APIRouter()


@router.post("/email/password-reset")
async def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    email = str(payload.email).strip().lower()

    user = db.query(User).filter(User.email == email).first()
    # If user does not exist in SQLite yet, check if they exist in Supabase users_table
    if not user:
        sb_user = await sb.fetch_user(user_id="", email=email)
        if sb_user and sb_user.get("email"):
            user = User(
                id=sb_user.get("id") or uuid4().hex,
                email=email,
                hashed_password=hash_password("TemporaryPassword123!"),
                is_verified=True,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    if user:
        # Invalidate old recovery tokens
        db.query(VerificationToken).filter(
            VerificationToken.email == email,
            VerificationToken.token_type == "recovery",
            VerificationToken.is_used == False,  # noqa: E712
        ).update({"is_used": True})

        # Generate 6-digit numeric recovery PIN
        otp_pin = generate_numeric_otp(6)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        token_record = VerificationToken(
            email=email,
            token=otp_pin,
            token_type="recovery",
            expires_at=expires_at,
            is_used=False,
        )
        db.add(token_record)
        db.commit()

        # Send password reset email with 6-digit security PIN
        await send_email(email, "password_reset", otp_pin)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": "If an account exists for that address, a 6-digit password reset PIN has been sent."},
    )
