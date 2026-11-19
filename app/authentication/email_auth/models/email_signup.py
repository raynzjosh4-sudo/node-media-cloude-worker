from pydantic import BaseModel, EmailStr, Field


class EmailSignupRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=6, max_length=128)
