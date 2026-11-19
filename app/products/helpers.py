"""
Data mapping and helper functions for product serialization and category resolution.
"""
from typing import Optional
from app.products.schemas import (
    CategoryCreatePayload,
    Location,
    PriceTier,
    ProductColor,
    ProductMaterial,
    ProductResponse,
    ProductSize,
    ProductSupport,
    Supplier,
    TradingTerms,
)
from app.products.supabase_client import insert_category
from app.services.cloud_media_service import decode_base64_image, upload_to_cloudflare


def _build_supplier(raw: dict) -> Supplier:
    """Reconstruct Supplier from raw DB row (mirrors Supplier.fromJson logic)."""
    business = raw.get("business") or {}
    if isinstance(business, list):
        business = business[0] if business else {}

    loc_raw = raw.get("location") or {}
    if isinstance(loc_raw, dict):
        location = Location(
            latitude=loc_raw.get("latitude", 0.0),
            longitude=loc_raw.get("longitude", 0.0),
            addressName=loc_raw.get("addressName", ""),
        )
    else:
        location = Location(
            latitude=float(business.get("latitude") or raw.get("latitude") or 0),
            longitude=float(business.get("longitude") or raw.get("longitude") or 0),
            addressName=business.get("physical_address") or raw.get("physical_address") or "Headquarters",
        )

    return Supplier(
        id=raw.get("id") or raw.get("user_id") or raw.get("supplier_id") or "",
        name=(
            raw.get("name")
            or business.get("legal_name")
            or raw.get("full_name")
            or raw.get("supplier_name")
            or "N.O.D.E Supplier"
        ),
        imageUrl=(
            raw.get("imageUrl")
            or business.get("logo_url")
            or raw.get("profile_pic_url")
            or ""
        ),
        category=raw.get("category") or business.get("industry_group") or "General",
        location=location,
    )


def _build_product_response(row: dict) -> ProductResponse:
    """
    Map a raw Supabase products_table row → ProductResponse.
    Matches ProductModel.fromJson() field-by-field.
    """
    supplier_raw = row.get("supplier") or {}
    if not supplier_raw and row.get("supplier_id"):
        supplier_raw = {
            "id": row["supplier_id"],
            "supplier_name": row.get("supplier_name"),
        }
    supplier = _build_supplier(supplier_raw) if supplier_raw else Supplier(
        id=row.get("supplier_id", ""),
        name=row.get("supplier_name", "N.O.D.E Supplier"),
    )

    tiers_raw = row.get("price_tiers") or []
    price_tiers = [
        PriceTier(
            minQuantity=t.get("minQuantity", 0),
            price=float(t.get("price", 0)),
            label=t.get("label"),
        )
        for t in tiers_raw
    ]

    colors = [
        ProductColor(name=c.get("name", ""), hexCode=c.get("hexCode", ""))
        for c in (row.get("available_colors") or [])
    ]

    sizes = [
        ProductSize(name=s.get("name", ""), abbreviation=s.get("abbreviation", ""))
        for s in (row.get("available_sizes") or [])
    ]

    materials = [
        ProductMaterial(name=m.get("name", ""), imageUrl=m.get("imageUrl"))
        for m in (row.get("available_materials") or [])
    ]

    support_raw = row.get("support_info") or row.get("support") or {}
    support = ProductSupport(
        whatsapp=support_raw.get("whatsapp", "+256 000 000 000"),
        phone=support_raw.get("phone", "+256 000 000 000"),
        email=support_raw.get("email", "support@node.app"),
    ) if support_raw else ProductSupport()

    tt_raw = row.get("trading_terms") or {}
    trading_terms = TradingTerms(
        id=tt_raw.get("id", "tt_default"),
        content=tt_raw.get("content", "Standard trading terms apply for all wholesale transactions."),
        moq=tt_raw.get("moq"),
        warranty=tt_raw.get("warranty"),
        paymentTerms=tt_raw.get("paymentTerms"),
        deliveryTerms=tt_raw.get("deliveryTerms"),
    ) if tt_raw else TradingTerms()

    media_urls = list(dict.fromkeys(row.get("media_urls") or []))

    return ProductResponse(
        id=row.get("id") or "",
        sku=row.get("sku") or "",
        name=row.get("name") or "",
        brand=row.get("brand") or "",
        price_tiers=price_tiers,
        srp=float(row.get("srp") or 0),
        hs_code=row.get("hs_code") or "",
        weight_kg=float(row.get("weight_kg") or 0),
        volume_cbm=float(row.get("volume_cbm") or 0),
        origin_country=row.get("origin_country") or "",
        unbs_number=row.get("unbs_number") or "",
        denier=row.get("denier") or "",
        material=row.get("material") or "",
        supplier=supplier,
        category_id=row.get("category_id") or "",
        current_stock=int(row.get("current_stock") or 0),
        lead_time_days=int(row.get("lead_time_days") or 0),
        warehouse_loc=row.get("warehouse_loc") or "",
        seo_title=row.get("seo_title") or "",
        seo_description=row.get("seo_description") or "",
        search_keywords=list(row.get("search_keywords") or []),
        slug=row.get("slug") or "",
        image_url=row.get("image_url") or "",
        media_urls=media_urls,
        aspect_ratio=float(row.get("aspect_ratio") or 1.0),
        available_colors=colors,
        available_sizes=sizes,
        available_materials=materials,
        variant_label=row.get("variant_label") or "Size",
        support=support,
        trading_terms=trading_terms,
    )


def replace_primary_media_url(
    media_urls: list[str],
    old_primary_url: Optional[str],
    new_primary_url: str,
) -> list[str]:
    """Put the new primary image first and remove its previous primary URL."""
    other_urls = [
        url
        for url in media_urls
        if url and url not in (old_primary_url, new_primary_url)
    ]
    return [new_primary_url, *other_urls]


async def _resolve_category_id(
    category_id: Optional[str],
    new_category: Optional[CategoryCreatePayload],
) -> str:
    """
    Resolves category ID: if new_category is provided, creates category/subcategory
    (with Cloudflare R2 image upload) and returns its generated category ID.
    """
    if new_category:
        cat_image_url = new_category.image_url or ""
        if new_category.image_base64:
            file_bytes, filename, content_type = decode_base64_image(new_category.image_base64)
            cat_image_url = await upload_to_cloudflare(
                file_bytes=file_bytes,
                filename=filename,
                content_type=content_type,
                folder="categories",
            )
        created_cat = await insert_category(
            name=new_category.name,
            parent_id=new_category.parent_id,
            image_url=cat_image_url,
            level=new_category.level,
        )
        return created_cat.get("id", category_id or "cat_1")
    return category_id or "cat_1"
