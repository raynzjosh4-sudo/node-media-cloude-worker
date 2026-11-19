"""
Category & Subcategory management endpoints for products.
"""
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from app.core.deps import require_supplier_or_admin
from app.products.schemas import CategoryCreatePayload
from app.products.supabase_client import (
    fetch_categories,
    insert_category,
    update_category,
)
from app.services.cloud_media_service import decode_base64_image, upload_to_cloudflare

router = APIRouter()


def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


@router.get("/categories", summary="List all categories")
async def list_categories():
    return await fetch_categories()


@router.post("/categories", status_code=status.HTTP_201_CREATED, summary="Create a category or subcategory with Cloudflare image")
async def create_product_category(
    request: Request,
    payload: CategoryCreatePayload,
    current_user: dict = Depends(require_supplier_or_admin),
):
    """
    Create a new category or subcategory via JSON.
    If image_base64 is provided, uploads it to Cloudflare R2 (folder='categories').
    - For root categories: level=0, parent_id=None
    - For subcategories: level=1 (or higher), parent_id set to parent's category ID.
    """
    image_url = payload.image_url or ""
    if payload.image_base64:
        file_bytes, filename, content_type = decode_base64_image(payload.image_base64)
        image_url = await upload_to_cloudflare(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            folder="categories",
            token=_extract_token(request),
        )

    return await insert_category(
        name=payload.name,
        parent_id=payload.parent_id,
        image_url=image_url,
        level=payload.level,
    )


@router.post("/categories/with-image", status_code=status.HTTP_201_CREATED, summary="Create category/subcategory with direct image file upload")
async def create_category_with_image(
    request: Request,
    name: str = Form(..., description="Category name"),
    parent_id: Optional[str] = Form(None, description="Parent category ID (omit for root level)"),
    level: int = Form(0, description="Hierarchy level: 0 for root, 1 for subcategory"),
    file: Optional[UploadFile] = File(None, description="Category cover image file"),
    current_user: dict = Depends(require_supplier_or_admin),
):
    """
    Create a new category or subcategory with a direct multipart image file upload.
    Uploads the file directly to Cloudflare R2 (folder='categories') and stores the public CDN URL.
    """
    image_url = ""
    if file:
        file_bytes = await file.read()
        if file_bytes:
            image_url = await upload_to_cloudflare(
                file_bytes=file_bytes,
                filename=file.filename or f"cat_{name}.jpg",
                content_type=file.content_type or "image/jpeg",
                folder="categories",
                token=_extract_token(request),
            )

    return await insert_category(
        name=name.strip(),
        parent_id=parent_id.strip() if parent_id else None,
        image_url=image_url,
        level=level,
    )


@router.post("/categories/{category_id}/image", summary="Upload/Update category cover image")
@router.put("/categories/{category_id}/image", summary="Upload/Update category cover image")
async def upload_category_image(
    category_id: str,
    request: Request,
    file: UploadFile = File(..., description="Image file to set as category cover"),
    current_user: dict = Depends(require_supplier_or_admin),
):
    """
    Upload or replace the cover image for an existing category or subcategory.
    Uploads directly to Cloudflare R2 and updates image_url in categories_table.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    uploaded_url = await upload_to_cloudflare(
        file_bytes=file_bytes,
        filename=file.filename or f"{category_id}.jpg",
        content_type=file.content_type or "image/jpeg",
        folder="categories",
        token=_extract_token(request),
    )

    updated = await update_category(category_id, {"image_url": uploaded_url})
    return {
        "id": category_id,
        "image_url": uploaded_url,
        "category": updated,
    }
