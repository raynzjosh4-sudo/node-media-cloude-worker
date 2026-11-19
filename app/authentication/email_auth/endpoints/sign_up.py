from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.authentication.email_auth.models.email_signup import EmailSignupRequest
from app.authentication.email_auth.send_auth_email import send_email
from app.core.security import generate_numeric_otp, hash_password
from app.db.models import User, VerificationToken
from app.db.session import get_db

router = APIRouter()


@router.post("/email/sign-up")
async def sign_up(
    payload: EmailSignupRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    email = str(payload.email).strip().lower()

    # Check existing user
    user = db.query(User).filter(User.email == email).first()
    if user and user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    if user and not user.is_verified:
        # Update password for pending unverified user
        user.hashed_password = hash_password(payload.password)
    else:
        # Create fresh unverified user
        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
            is_verified=False,
            is_active=True,
        )
        db.add(user)

    # Invalidate previous signup tokens
    db.query(VerificationToken).filter(
        VerificationToken.email == email,
        VerificationToken.token_type == "signup",
        VerificationToken.is_used == False,  # noqa: E712
    ).update({"is_used": True})

    # Generate 6-digit OTP
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
        content={"message": "If the address can be registered, a verification email has been sent."},
    )
