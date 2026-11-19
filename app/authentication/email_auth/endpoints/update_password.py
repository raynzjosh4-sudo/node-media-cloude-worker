from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.authentication.email_auth.dependencies.bearer_token import bearer_token
from app.authentication.email_auth.models.password_update import PasswordUpdateRequest
from app.core.security import decode_access_token, hash_password
from app.db.models import User, VerificationToken
from app.db.session import get_db
from app.profile import supabase_client as sb

router = APIRouter()


@router.put("/email/password")
async def update_password(
    payload: PasswordUpdateRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
    reset_token: Annotated[str | None, Query(alias="token")] = None,
) -> JSONResponse:
    user: User | None = None
    effective_token = (payload.token or reset_token or "").strip()

    if effective_token:
        # User updating password via 6-digit recovery PIN
        now = datetime.now(timezone.utc)
        token_record = (
            db.query(VerificationToken)
            .filter(
                VerificationToken.token == effective_token,
                VerificationToken.token_type == "recovery",
                VerificationToken.is_used == False,  # noqa: E712
            )
            .order_by(VerificationToken.id.desc())
            .first()
        )
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or already used password reset PIN.",
            )

        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset PIN has expired. Please request a new PIN.",
            )

        user = db.query(User).filter(User.email == token_record.email).first()
        if not user:
            sb_user = await sb.fetch_user(user_id="", email=token_record.email)
            user = User(
                id=sb_user.get("id") or uuid4().hex,
                email=token_record.email,
                hashed_password=hash_password(payload.password),
                is_verified=True,
                is_active=True,
            )
            db.add(user)
        else:
            user.hashed_password = hash_password(payload.password)
            user.is_verified = True
            user.is_active = True

        token_record.is_used = True

    elif authorization:
        # Authenticated user updating their own password
        raw_token = bearer_token(authorization)
        token_data = decode_access_token(raw_token)
        user_id = token_data.get("sub")
        email = token_data.get("email")

        user = db.query(User).filter(User.id == str(user_id)).first()
        if not user and email:
            user = db.query(User).filter(User.email == str(email).lower()).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found.",
            )
        user.hashed_password = hash_password(payload.password)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid recovery PIN or Authorization header is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Password has been successfully updated. You can now log in with your new password."},
    )
