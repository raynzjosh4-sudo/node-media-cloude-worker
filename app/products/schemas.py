"""
Pydantic schemas matching Flutter's ProductModel.fromJson() exactly.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class Location(BaseModel):
    latitude: float = 0.0
    longitude: float = 0.0
    addressName: str = ""


class Supplier(BaseModel):
    id: str = ""
    name: str = ""
    imageUrl: str = ""
    category: str = ""
    location: Location = Location()


class PriceTier(BaseModel):
    minQuantity: int
    price: float
    label: Optional[str] = None


class ProductColor(BaseModel):
    name: str
    hexCode: str


class ProductSize(BaseModel):
    name: str
    abbreviation: str


class ProductMaterial(BaseModel):
    name: str
    imageUrl: Optional[str] = None


class ProductSupport(BaseModel):
    whatsapp: str = "+256 000 000 000"
    phone: str = "+256 000 000 000"
    email: str = "support@node.app"


class TradingTerms(BaseModel):
    id: str = "tt_default"
    content: str = "Standard trading terms apply for all wholesale transactions."
    moq: Optional[str] = None
    warranty: Optional[str] = None
    paymentTerms: Optional[str] = None
    deliveryTerms: Optional[str] = None


class ProductResponse(BaseModel):
    id: str
    sku: str = ""
    name: str = ""
    brand: str = ""
    price_tiers: List[PriceTier] = []
    srp: float = 0.0
    hs_code: Optional[str] = ""
    weight_kg: float = 0.0
    volume_cbm: float = 0.0
    origin_country: Optional[str] = ""
    unbs_number: Optional[str] = ""
    denier: Optional[str] = ""
    material: Optional[str] = ""
    supplier: Supplier = Supplier()
    category_id: str = ""
    current_stock: int = 0
    lead_time_days: int = 0
    warehouse_loc: Optional[str] = ""
    seo_title: Optional[str] = ""
    seo_description: Optional[str] = ""
    search_keywords: List[str] = []
    slug: Optional[str] = ""
    image_url: Optional[str] = ""
    media_urls: List[str] = []
    aspect_ratio: float = 1.0
    available_colors: List[ProductColor] = []
    available_sizes: List[ProductSize] = []
    available_materials: List[ProductMaterial] = []
    variant_label: Optional[str] = "Size"
    support: ProductSupport = ProductSupport()
    trading_terms: TradingTerms = TradingTerms()


class ProductListItem(BaseModel):
    """Lightweight model for list view — matches Flutter inventory list query."""
    id: str
    name: str
    sku: str
    brand: str
    srp: float
    image_url: str
    created_at: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None


class PaginatedProducts(BaseModel):
    data: List[ProductListItem]
    total: int
    page: int
    limit: int
    has_more: bool


class CategoryCreatePayload(BaseModel):
    name: str
    parent_id: Optional[str] = None
    level: int = 0
    image_url: Optional[str] = None
    image_base64: Optional[str] = None


class ProductCreateRequest(BaseModel):
    sku: str
    name: str
    brand: str
    srp: float
    category_id: Optional[str] = None
    new_category: Optional[CategoryCreatePayload] = None
    supplier_id: str
    image_url: Optional[str] = ""
    image_base64: Optional[str] = None
    slug: Optional[str] = None
    media_urls: List[str] = []
    aspect_ratio: float = 1.0
    price_tiers: List[PriceTier] = []
    hs_code: Optional[str] = ""
    weight_kg: Optional[float] = 0.0
    volume_cbm: Optional[float] = 0.0
    origin_country: Optional[str] = ""
    unbs_number: Optional[str] = ""
    denier: Optional[str] = ""
    material: Optional[str] = ""
    current_stock: int = 0
    lead_time_days: int = 0
    warehouse_loc: Optional[str] = ""
    seo_title: Optional[str] = ""
    seo_description: Optional[str] = ""
    search_keywords: List[str] = []
    available_colors: List[ProductColor] = []
    available_sizes: List[ProductSize] = []
    available_materials: List[ProductMaterial] = []
    variant_label: str = "Size"
    support_info: Optional[ProductSupport] = None
    trading_terms: Optional[TradingTerms] = None


class ProductUpdateRequest(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    slug: Optional[str] = None
    srp: Optional[float] = None
    category_id: Optional[str] = None
    new_category: Optional[CategoryCreatePayload] = None
    supplier_id: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    media_urls: Optional[List[str]] = None
    aspect_ratio: Optional[float] = None
    price_tiers: Optional[List[PriceTier]] = None
    hs_code: Optional[str] = None
    weight_kg: Optional[float] = None
    volume_cbm: Optional[float] = None
    origin_country: Optional[str] = None
    unbs_number: Optional[str] = None
    denier: Optional[str] = None
    material: Optional[str] = None
    current_stock: Optional[int] = None
    lead_time_days: Optional[int] = None
    warehouse_loc: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    search_keywords: Optional[List[str]] = None
    available_colors: Optional[List[ProductColor]] = None
    available_sizes: Optional[List[ProductSize]] = None
    available_materials: Optional[List[ProductMaterial]] = None
    variant_label: Optional[str] = None
    support_info: Optional[ProductSupport] = None
    trading_terms: Optional[TradingTerms] = None
