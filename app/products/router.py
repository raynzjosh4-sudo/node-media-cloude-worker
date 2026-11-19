"""
Products router aggregating catalog, categories, management, and image upload endpoints.
"""
from fastapi import APIRouter
from app.products.endpoints.categories import router as categories_router
from app.products.endpoints.catalog import router as catalog_router
from app.products.endpoints.manage import router as manage_router
from app.products.endpoints.images import router as images_router

router = APIRouter(prefix="/api/v1/products", tags=["products"])

# Include sub-routers in careful priority order so static routes precede {product_id}
router.include_router(categories_router)
router.include_router(manage_router)
router.include_router(images_router)
router.include_router(catalog_router)
