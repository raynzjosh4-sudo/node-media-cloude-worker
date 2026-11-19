from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.authentication.email_auth.models.pending_account_delete import (
    PendingAccountDeleteRequest,
)
from app.db.models import User, VerificationToken
from app.db.session import get_db

router = APIRouter()


@router.delete("/email/pending-account")
async def delete_pending_account(
    payload: PendingAccountDeleteRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    target_id = str(payload.user_id).strip()
    user = db.query(User).filter(User.id == target_id, User.is_verified == False).first()  # noqa: E712
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending unconfirmed user not found.",
        )

    # Clean up tokens
    db.query(VerificationToken).filter(VerificationToken.email == user.email).delete()
    db.delete(user)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Pending unverified account successfully deleted."},
    )
