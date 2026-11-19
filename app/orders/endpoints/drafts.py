"""
Draft orders synchronization endpoints for N.O.D.E. (Flutter SQLite/Drift sync).
"""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.orders.deps import get_current_user_id
from app.orders.schemas import (
    OrderCreateRequest,
    OrderResponse,
    OrderStatus,
)
from app.orders.supabase_client import (
    delete_draft_for_user,
    fetch_drafts_for_user,
    upsert_order,
)

router = APIRouter()


@router.get("/drafts", response_model=List[OrderResponse], summary="Get drafts for user")
async def get_drafts(
    current_user_id: str = Depends(get_current_user_id),
):
    """Fetch all saved order drafts for the current user."""
    drafts = await fetch_drafts_for_user(current_user_id)
    return [OrderResponse(**d) for d in drafts]


@router.post("/drafts", response_model=OrderResponse, summary="Save or upsert draft")
async def save_draft(
    body: OrderCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    """Save or upsert a local draft synced from Flutter SQLite/Drift."""
    now = datetime.now(timezone.utc).isoformat()
    order_data = body.model_dump()
    order_data["user_id"] = current_user_id
    order_data["status"] = OrderStatus.DRAFT.value
    order_data["created_at"] = now
    order_data["updated_at"] = now

    result = await upsert_order(order_data)
    return OrderResponse(**result)


@router.delete("/drafts/{id}", summary="Delete draft")
async def delete_draft(
    id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    """Delete a draft order by ID or order_id."""
    deleted = await delete_draft_for_user(draft_id=id, user_id=current_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft '{id}' not found",
        )
    return {"success": True, "message": "Draft deleted successfully"}
