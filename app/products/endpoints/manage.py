"""
Product publishing, updating, and management endpoints for suppliers and admins.
"""
import re
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_supplier_or_admin
from app.products.helpers import (
    _build_product_response,
    _resolve_category_id,
    replace_primary_media_url,
)
from app.products.schemas import (
    CategoryCreatePayload,
    PaginatedProducts,
    ProductCreateRequest,
    ProductListItem,
    ProductResponse,
    ProductUpdateRequest,
)
from app.products.supabase_client import (
    delete_product,
    fetch_product_by_id,
    fetch_products,
    insert_product,
    update_product,
)
from app.services.cloud_media_service import decode_base64_image, upload_to_cloudflare

router = APIRouter()


@router.get("/my-products", response_model=PaginatedProducts, summary="List supplier's own posted products")
async def list_my_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    sort_by: str = Query("created_at"),
    ascending: bool = Query(False),
    current_user: dict = Depends(require_supplier_or_admin),
):
    """Returns only products posted by the currently authenticated supplier."""
    result = await fetch_products(
        supplier_id=current_user["id"],
        search=search,
        page=page,
        limit=limit,
        sort_by=sort_by,
        ascending=ascending,
    )
    items = [ProductListItem(**p) for p in result["products"]]
    total = result["total"]
    return PaginatedProducts(
        data=items,
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="Post/Publish a new product")
async def create_new_product(
    payload: ProductCreateRequest,
    current_user: dict = Depends(require_supplier_or_admin),
):
    """Post a new product to the global catalog."""
    caller_role = (current_user.get("role") or "").lower()
    supplier_id = payload.supplier_id if caller_role == "admin" and payload.supplier_id else current_user["id"]

    slug = payload.slug
    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "-", payload.name.lower()).strip("-")
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    product_id = str(uuid.uuid4())

    # Handle image upload to Cloudflare if base64 data provided
    image_url = payload.image_url or ""
    media_urls = list(payload.media_urls or [])
    if payload.image_base64:
        file_bytes, filename, content_type = decode_base64_image(payload.image_base64)
        uploaded_url = await upload_to_cloudflare(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            folder="products",
        )
        image_url = uploaded_url
        if uploaded_url not in media_urls:
            media_urls.insert(0, uploaded_url)
    elif image_url and not media_urls:
        media_urls = [image_url]

    category_id = await _resolve_category_id(payload.category_id, payload.new_category)

    product_data = {
        "id": product_id,
        "sku": payload.sku,
        "name": payload.name,
        "brand": payload.brand,
        "slug": slug,
        "srp": payload.srp,
        "category_id": category_id,
        "supplier_id": supplier_id,
        "image_url": image_url,
        "media_urls": media_urls,
        "aspect_ratio": payload.aspect_ratio,
        "price_tiers": [t.model_dump() for t in payload.price_tiers],
        "hs_code": payload.hs_code or "",
        "weight_kg": payload.weight_kg or 0.0,
        "volume_cbm": payload.volume_cbm or 0.0,
        "origin_country": payload.origin_country or "",
        "unbs_number": payload.unbs_number or "",
        "denier": payload.denier or "",
        "material": payload.material or "",
        "current_stock": payload.current_stock or 0,
        "lead_time_days": payload.lead_time_days or 0,
        "warehouse_loc": payload.warehouse_loc or "",
        "seo_title": payload.seo_title or payload.name,
        "seo_description": payload.seo_description or "",
        "search_keywords": payload.search_keywords or [],
        "available_colors": [c.model_dump() for c in payload.available_colors],
        "available_sizes": [s.model_dump() for s in payload.available_sizes],
        "available_materials": [m.model_dump() for m in payload.available_materials],
        "variant_label": payload.variant_label or "Size",
        "support_info": payload.support_info.model_dump() if payload.support_info else {},
        "trading_terms": payload.trading_terms.model_dump() if payload.trading_terms else {},
    }

    inserted = await insert_product(product_data)
    row = await fetch_product_by_id(product_id) or inserted
    return _build_product_response(row)


@router.put("/{product_id}", response_model=ProductResponse, summary="Update an existing product")
async def update_existing_product(
    product_id: str,
    payload: ProductUpdateRequest,
    current_user: dict = Depends(require_supplier_or_admin),
):
    """Update a product (only owner supplier or admin)."""
    existing = await fetch_product_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found")

    caller_role = (current_user.get("role") or "").lower()
    if caller_role != "admin" and existing.get("supplier_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are only permitted to edit your own posted products.",
        )

    updates = payload.model_dump(exclude_none=True)

    if "new_category" in updates:
        new_cat_data = updates.pop("new_category")
        if new_cat_data:
            cat_payload = CategoryCreatePayload(**new_cat_data) if isinstance(new_cat_data, dict) else new_cat_data
            updates["category_id"] = await _resolve_category_id(updates.get("category_id"), cat_payload)

    if updates.get("image_base64"):
        file_bytes, filename, content_type = decode_base64_image(updates.pop("image_base64"))
        uploaded_url = await upload_to_cloudflare(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            folder="products",
        )
        updates["image_url"] = uploaded_url
        current_media = list(updates.get("media_urls") or existing.get("media_urls") or [])
        updates["media_urls"] = replace_primary_media_url(
            current_media,
            existing.get("image_url"),
            uploaded_url,
        )
    elif "image_base64" in updates:
        updates.pop("image_base64", None)

    if updates.get("image_url"):
        current_media = list(updates.get("media_urls") or existing.get("media_urls") or [])
        updates["media_urls"] = replace_primary_media_url(
            current_media,
            existing.get("image_url"),
            updates["image_url"],
        )

    if "price_tiers" in updates:
        updates["price_tiers"] = [t.model_dump() if hasattr(t, "model_dump") else t for t in payload.price_tiers or []]
    if "available_colors" in updates:
        updates["available_colors"] = [c.model_dump() if hasattr(c, "model_dump") else c for c in payload.available_colors or []]
    if "available_sizes" in updates:
        updates["available_sizes"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in payload.available_sizes or []]
    if "available_materials" in updates:
        updates["available_materials"] = [m.model_dump() if hasattr(m, "model_dump") else m for m in payload.available_materials or []]
    if "support_info" in updates and payload.support_info:
        updates["support_info"] = payload.support_info.model_dump()
    if "trading_terms" in updates and payload.trading_terms:
        updates["trading_terms"] = payload.trading_terms.model_dump()

    if updates:
        await update_product(product_id, updates)

    refreshed = await fetch_product_by_id(product_id)
    return _build_product_response(refreshed or existing)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a product")
async def delete_existing_product(
    product_id: str,
    current_user: dict = Depends(require_supplier_or_admin),
):
    """Delete a product (only owner supplier or admin)."""
    existing = await fetch_product_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found")

    caller_role = (current_user.get("role") or "").lower()
    if caller_role != "admin" and existing.get("supplier_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are only permitted to delete your own posted products.",
        )

    deleted = await delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to delete product")
    return None
