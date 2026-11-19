from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.authentication.email_auth.dependencies.auth import get_current_user
from app.db.models import User

router = APIRouter()


@router.get("/me")
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"user": current_user.to_dict()},
    )

