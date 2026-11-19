"""
Public catalog browsing endpoints (list, details, popular, suppliers).
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.products.helpers import _build_product_response
from app.products.schemas import (
    PaginatedProducts,
    ProductListItem,
    ProductResponse,
)
from app.products.supabase_client import (
    fetch_popular_products,
    fetch_product_by_id,
    fetch_product_by_slug,
    fetch_products,
    fetch_suppliers,
)

router = APIRouter()


@router.get("/", response_model=PaginatedProducts, summary="List products")
async def list_products(
    supplier_id: Optional[str] = Query(None, description="Filter by supplier UUID"),
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", description="Column to sort by"),
    ascending: bool = Query(False),
):
    result = await fetch_products(
        supplier_id=supplier_id,
        category_id=category_id,
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


@router.get("/popular", response_model=list[ProductResponse], summary="Get popular products for home screen explore section")
async def get_popular_products(
    category_id: Optional[str] = Query(None, description="Optional category UUID to filter by"),
    limit: int = Query(15, ge=1, le=50, description="Number of products to return (default 15)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Returns popular and trending products for the home screen explore section.
    Directly feeds Flutter's popularProductsProvider and PopularSection widget.
    """
    rows = await fetch_popular_products(
        category_id=category_id,
        limit=limit,
        offset=offset,
    )
    return [_build_product_response(r) for r in rows]


@router.get("/suppliers", summary="List all suppliers")
async def list_suppliers():
    return await fetch_suppliers()


@router.get("/slug/{slug}", response_model=ProductResponse, summary="Get product by slug")
async def get_product_by_slug(slug: str):
    row = await fetch_product_by_slug(slug)
    if not row:
        raise HTTPException(status_code=404, detail=f"Product with slug '{slug}' not found")
    return _build_product_response(row)


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product by ID")
async def get_product(product_id: str):
    row = await fetch_product_by_id(product_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    return _build_product_response(row)
