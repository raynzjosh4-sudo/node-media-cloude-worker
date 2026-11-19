"""
Product and general image upload endpoints with Cloudflare R2 integration.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from app.core.deps import require_supplier_or_admin
from app.products.helpers import _build_product_response, replace_primary_media_url
from app.products.schemas import ProductResponse
from app.products.supabase_client import fetch_product_by_id, update_product
from app.services.cloud_media_service import upload_to_cloudflare

router = APIRouter()


def _extract_token(request: Request) -> str | None:
    """Pull the raw Bearer token string from the Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


@router.post("/{product_id}/image", response_model=ProductResponse, summary="Upload image file to Cloudflare and update product")
@router.put("/{product_id}/image", response_model=ProductResponse, summary="Upload image file to Cloudflare and update product")
async def upload_product_image_file(
    product_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_supplier_or_admin),
):
    """
    Receives an image file from the user (multipart/form-data), uploads it to Cloudflare R2,
    and updates the product's image_url and media_urls in Supabase DB.
    """
    existing = await fetch_product_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found")

    caller_role = (current_user.get("role") or "").lower()
    if caller_role != "admin" and existing.get("supplier_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are only permitted to edit your own posted products.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    # 1. Upload to Cloudflare R2 with the user's session token
    uploaded_url = await upload_to_cloudflare(
        file_bytes=file_bytes,
        filename=file.filename or f"{product_id}.jpg",
        content_type=file.content_type or "image/jpeg",
        folder="products",
        token=_extract_token(request),
    )

    # 2. Update image_url and media_urls in DB
    updates = {
        "image_url": uploaded_url,
        "media_urls": replace_primary_media_url(
            list(existing.get("media_urls") or []),
            existing.get("image_url"),
            uploaded_url,
        ),
    }
    await update_product(product_id, updates)

    refreshed = await fetch_product_by_id(product_id)
    return _build_product_response(refreshed or existing)


@router.post("/upload-image", summary="Upload general image to Cloudflare R2")
async def upload_general_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_supplier_or_admin),
):
    """Standalone upload: uploads an image file to Cloudflare R2 and returns its public CDN URL."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    uploaded_url = await upload_to_cloudflare(
        file_bytes=file_bytes,
        filename=file.filename or "image.jpg",
        content_type=file.content_type or "image/jpeg",
        folder="products",
        token=_extract_token(request),
    )
    return {
        "url": uploaded_url,
        "filename": file.filename,
        "content_type": file.content_type,
    }
