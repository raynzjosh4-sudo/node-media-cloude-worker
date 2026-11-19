from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.authentication.email_auth.dependencies.auth import get_current_user
from app.db.models import User, VerificationToken
from app.db.session import get_db

router = APIRouter()


@router.delete("/account")
async def delete_account(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    # Remove associated tokens
    db.query(VerificationToken).filter(VerificationToken.email == current_user.email).delete()
    db.delete(current_user)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Your account has been successfully deleted."},
    )
