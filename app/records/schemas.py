from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class RecordCreate(BaseModel):
    id: str = Field(..., description="Client-generated record UUID")
    contact_name: str = ""
    item_name: str = ""
    reference_tag: Optional[str] = None
    unit: str = "Units"
    target_value: float = 0.0
    current_value: float = 0.0
    type: str = "standard"
    contact_image_url: Optional[str] = None
    grand_total: float = 0.0
    breakdown_items_json: list[dict[str, Any]] = Field(default_factory=list)
    timeline_json: list[dict[str, Any]] = Field(default_factory=list)
    reminder_date: Optional[str] = None
    reminder_time: Optional[str] = None
    reminder_is_recurring: bool = False
    is_archived: bool = False


class RecordResponse(RecordCreate):
    user_id: str
    updated_at: Optional[str] = None


class PaginatedRecords(BaseModel):
    data: list[RecordResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
