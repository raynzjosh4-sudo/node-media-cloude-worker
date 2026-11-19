from typing import Optional
from pydantic import BaseModel, Field


class PasswordUpdateRequest(BaseModel):
    password: str = Field(min_length=6, max_length=128)
    token: Optional[str] = None
    email: Optional[str] = None
