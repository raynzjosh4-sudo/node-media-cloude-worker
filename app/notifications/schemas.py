from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class NotificationCategory(str, Enum):
    ALL = "all"
    ORDERS = "orders"
    INVENTORY = "inventory"
    LOGISTICS = "logistics"
    SECURITY = "security"
    FINANCE = "finance"
    SYSTEM = "system"
    REMINDERS = "reminders"
    MESSAGES = "messages"


class NotificationItemResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    category: str
    is_unread: bool = True
    metadata: Optional[dict[str, Any]] = None
    created_at: str


class PaginatedNotifications(BaseModel):
    data: list[NotificationItemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class DeviceTokenRegister(BaseModel):
    token: str = Field(..., description="FCM device push token")
    device_type: str = Field(default="android", description="android | ios | web")
