from pydantic import BaseModel, EmailStr, Field


class EmailRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
