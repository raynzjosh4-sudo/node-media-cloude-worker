"""
Supplier incoming orders queue endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.orders.deps import get_current_user_id
from app.orders.schemas import (
    OrderListItem,
    PaginatedOrders,
)
from app.orders.supabase_client import fetch_supplier_incoming

router = APIRouter()


@router.get(
    "/supplier/incoming",
    response_model=PaginatedOrders,
    summary="Get orders where current user is the supplier",
)
async def get_supplier_incoming_orders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user_id: str = Depends(get_current_user_id),
):
    """Get paginated incoming orders for the current user acting as supplier."""
    result = await fetch_supplier_incoming(
        supplier_id=current_user_id,
        page=page,
        limit=limit,
        status_filter=status_filter,
    )

    items = [
        OrderListItem(
            order_id=row.get("order_id", ""),
            supplier_id=row.get("supplier_id"),
            business_name=row.get("business_name"),
            total_amount=float(row.get("total_amount") or 0.0),
            status=row.get("status", "new"),
            created_at=row.get("created_at"),
        )
        for row in result["orders"]
    ]
    total = result["total"]

    return PaginatedOrders(
        data=items,
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )
