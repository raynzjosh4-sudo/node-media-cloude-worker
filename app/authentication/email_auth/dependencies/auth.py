from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.authentication.email_auth.dependencies.bearer_token import bearer_token
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Validate Bearer JWT token and fetch active user from the database."""
    token = bearer_token(authorization)
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == str(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return user

