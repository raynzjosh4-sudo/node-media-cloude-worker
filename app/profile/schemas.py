from typing import Any, Optional

from pydantic import BaseModel


# --------------- response models ---------------


class UserProfile(BaseModel):
    id: str
    full_name: str
    email: str
    role: str  # "buyer", "supplier", "admin"
    profile_pic_url: Optional[str] = None


class BusinessProfile(BaseModel):
    user_id: str
    legal_name: str
    phone_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    city: Optional[str] = None
    physical_address: Optional[str] = None
    logo_url: Optional[str] = None


class ProfileResponse(BaseModel):
    user: UserProfile
    business: Optional[BusinessProfile] = None


# --------------- request bodies ---------------


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    profile_pic_url: Optional[str] = None


class UpdateBusinessRequest(BaseModel):
    legal_name: str
    phone_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    city: Optional[str] = None
    physical_address: Optional[str] = None


class TradingTermsRequest(BaseModel):
    id: str
    content: str
    moq: Optional[str] = None
    warranty: Optional[str] = None
    paymentTerms: Optional[str] = None
    deliveryTerms: Optional[str] = None


class TradingTermsResponse(BaseModel):
    trading_terms: Any
