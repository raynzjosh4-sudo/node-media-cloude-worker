from typing import Any, Optional
from pydantic import BaseModel, Field


class SavedItemCreate(BaseModel):
    product_id: str = Field(..., description="UUID of the product")
    quantity: int = Field(default=1, ge=1)
    selected_color: Optional[str] = None
    selected_size: Optional[str] = None
    product_snapshot: Optional[dict[str, Any]] = None


class SavedItemResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    quantity: int = 1
    selected_color: Optional[str] = None
    selected_size: Optional[str] = None
    product_snapshot: Optional[dict[str, Any]] = None
    created_at: Optional[str] = None


class SavedItemCheckResponse(BaseModel):
    is_saved: bool
    saved_item_id: Optional[str] = None
