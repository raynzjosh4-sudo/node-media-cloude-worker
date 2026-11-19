from typing import Optional
from pydantic import BaseModel, Field


class PromotionResponse(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = ""
    action_text: Optional[str] = ""
    image_urls: list[str] = Field(default_factory=list)
    priority: int = 0
    is_active: bool = True
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None
