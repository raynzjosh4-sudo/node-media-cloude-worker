from pydantic import BaseModel, EmailStr, Field


class EmailPasswordRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)
