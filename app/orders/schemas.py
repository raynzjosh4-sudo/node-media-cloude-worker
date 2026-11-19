"""
Pydantic schemas for the Orders API.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING = "pending"
    DRAFT = "draft"


class OrderCreateRequest(BaseModel):
    order_id: str
    supplier_id: str
    business_name: str
    business_phone: str
    business_city: str
    business_address: str
    latitude: float = 0.0
    longitude: float = 0.0
    total_amount: float
    entries_json: List[Any] = Field(default_factory=list)
    pdf_id: Optional[str] = None
    pdf_url: Optional[str] = None


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus


class OrderListItem(BaseModel):
    order_id: str
    supplier_id: Optional[str] = None
    business_name: Optional[str] = None
    total_amount: Optional[float] = 0.0
    status: Optional[str] = "new"
    created_at: Optional[str] = None

    model_config = {"extra": "allow"}


class OrderResponse(BaseModel):
    id: Optional[str] = None
    order_id: str
    user_id: Optional[str] = None
    supplier_id: Optional[str] = None
    business_name: Optional[str] = None
    business_phone: Optional[str] = None
    business_city: Optional[str] = None
    business_address: Optional[str] = None
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    entries_json: Optional[List[Any]] = Field(default_factory=list)
    pdf_id: Optional[str] = None
    pdf_url: Optional[str] = None
    status: Optional[str] = "new"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"extra": "allow"}


class PaginatedOrders(BaseModel):
    data: List[OrderListItem]
    total: int
    page: int
    limit: int
    has_more: bool
