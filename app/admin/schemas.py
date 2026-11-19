from typing import Any, Optional
from pydantic import BaseModel, Field


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., description="Category display name")
    parent_id: Optional[str] = Field(None, description="Parent category ID for subcategories")
    image_url: Optional[str] = Field(None, description="Public image URL")
    level: int = Field(default=0, ge=0, description="Hierarchy depth (0 for root)")


class SupplierActionResponse(BaseModel):
    user_id: str
    role: str
    message: str


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., description="Target role: customer, supplier, admin")


class PotentialSupplierItem(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    role: str
    profile_pic: Optional[str] = None
    legal_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    industry_group: Optional[str] = None
    logo_url: Optional[str] = None
