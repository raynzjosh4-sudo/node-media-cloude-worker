"""
Orders router aggregating draft sync, supplier incoming, and wholesale ordering endpoints.
"""
from fastapi import APIRouter
from app.orders.endpoints.drafts import router as drafts_router
from app.orders.endpoints.supplier import router as supplier_router
from app.orders.endpoints.wholesale import router as wholesale_router

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

# Include drafts and supplier incoming first so specific path segments precede /{order_id}
router.include_router(drafts_router)
router.include_router(supplier_router)
router.include_router(wholesale_router)
