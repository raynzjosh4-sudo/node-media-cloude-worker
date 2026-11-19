"""
Wholesale orders placement, status updates, and PDF download endpoints.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.orders.deps import get_current_user_id
from app.orders.notifications import _dispatch_order_status_notifications
from app.orders.schemas import (
    OrderCreateRequest,
    OrderListItem,
    OrderResponse,
    OrderStatus,
    OrderStatusUpdateRequest,
    PaginatedOrders,
)
from app.orders.supabase_client import (
    delete_order,
    fetch_order_by_id,
    fetch_orders_for_user,
    update_order_status,
    upsert_order,
)
from app.profile.supabase_client import fetch_business, fetch_user
from app.services.pdf_generator import generate_order_pdf

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, summary="Send order to supplier")
async def create_order(
    body: OrderCreateRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
):
    """Create or upsert a wholesale order sent to a supplier."""
    now = datetime.now(timezone.utc).isoformat()
    order_data = body.model_dump()
    order_data["user_id"] = current_user_id
    order_data["status"] = OrderStatus.NEW.value
    order_data["created_at"] = now
    order_data["updated_at"] = now

    result = await upsert_order(order_data)

    background_tasks.add_task(
        _dispatch_order_status_notifications,
        order=result,
        new_status="new",
        action_by_user_id=current_user_id,
    )

    return OrderResponse(**result)


@router.get("/", response_model=PaginatedOrders, summary="Get my sent orders")
async def list_my_orders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user_id: str = Depends(get_current_user_id),
):
    """Get paginated wholesale orders placed by current user."""
    result = await fetch_orders_for_user(
        user_id=current_user_id,
        page=page,
        limit=limit,
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


@router.get("/{order_id}/pdf", summary="Download official Order Spec Sheet & Invoice PDF")
async def get_order_pdf(
    order_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Generates and streams the official N.O.D.E. Order Spec Sheet PDF for direct web/app viewing.
    Accessible by the buyer who placed it, the supplier who received it, or an admin.
    """
    order = await fetch_order_by_id(order_id=order_id, user_id=current_user_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found or unauthorized",
        )

    buyer_id = order.get("user_id")
    supplier_id = order.get("supplier_id")

    buyer_user = (await fetch_user(buyer_id)) if buyer_id else {}
    buyer_biz = (await fetch_business(buyer_id)) if buyer_id else {}
    supplier_user = (await fetch_user(supplier_id)) if supplier_id else {}
    supplier_biz = (await fetch_business(supplier_id)) if supplier_id else {}

    pdf_bytes = generate_order_pdf(
        order=order,
        buyer_user=buyer_user,
        buyer_business=buyer_biz,
        supplier_user=supplier_user,
        supplier_business=supplier_biz,
    )

    filename = f"NODE_Order_{order_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{filename}\"",
        },
    )


@router.get("/{order_id}", response_model=OrderResponse, summary="Get single order")
async def get_order(
    order_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    """Get single order details by order_id."""
    order = await fetch_order_by_id(order_id=order_id, user_id=current_user_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )
    return OrderResponse(**order)


@router.patch("/{order_id}/status", response_model=OrderResponse, summary="Update order status")
async def update_status(
    order_id: str,
    body: OrderStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
):
    """Update order status (caller must be buyer/order owner or supplier)."""
    updated = await update_order_status(
        order_id=order_id,
        user_id=current_user_id,
        new_status=body.status.value,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found or you are not authorized to update its status",
        )

    background_tasks.add_task(
        _dispatch_order_status_notifications,
        order=updated,
        new_status=body.status.value,
        action_by_user_id=current_user_id,
    )

    return OrderResponse(**updated)


@router.delete("/{order_id}", summary="Delete/cancel order")
async def remove_order(
    order_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    """Delete or cancel an order (must be owner of the order)."""
    deleted = await delete_order(order_id=order_id, user_id=current_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )
    return {"success": True, "message": "Order deleted successfully"}
