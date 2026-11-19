from fastapi import APIRouter, HTTPException, status
from app.promotions.schemas import PromotionResponse
from app.promotions.supabase_client import (
    fetch_active_promotions,
    fetch_promotion_by_id,
)

router = APIRouter(prefix="/api/v1/promotions", tags=["promotions"])


@router.get("", response_model=list[PromotionResponse], summary="List active promotion campaigns")
async def list_promotions():
    return await fetch_active_promotions()


@router.get("/{promo_id}", response_model=PromotionResponse, summary="Get single promotion by ID")
async def get_promotion(promo_id: str):
    row = await fetch_promotion_by_id(promo_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promotion '{promo_id}' not found",
        )
    return PromotionResponse(**row)
