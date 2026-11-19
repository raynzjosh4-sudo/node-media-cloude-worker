"""
Supabase REST client for products and categories.
Re-exports modular implementations from app.products.supabase.*.
"""
from app.products.supabase.categories import (
    fetch_categories,
    insert_category,
    update_category,
)
from app.products.supabase.products import (
    fetch_products,
    fetch_product_by_id,
    fetch_product_by_slug,
    fetch_suppliers,
    insert_product,
    update_product,
    delete_product,
    fetch_popular_products,
)

__all__ = [
    "fetch_categories",
    "insert_category",
    "update_category",
    "fetch_products",
    "fetch_product_by_id",
    "fetch_product_by_slug",
    "fetch_suppliers",
    "insert_product",
    "update_product",
    "delete_product",
    "fetch_popular_products",
]
