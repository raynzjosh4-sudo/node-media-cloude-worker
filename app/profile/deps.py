from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token

security = HTTPBearer()


async def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    return {
        "user_id": str(user_id),
        "email": payload.get("email", ""),
    }


async def get_current_user_id(
    payload: dict[str, Any] = Depends(get_current_token_payload),
) -> str:
    return payload["user_id"]
