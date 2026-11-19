"""
Supabase client operations for product categories.
"""
from typing import Optional
import uuid
import httpx
from app.core.config import supabase_url, supabase_anon_key

SUPABASE_URL = supabase_url()
SUPABASE_KEY = supabase_anon_key()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


async def fetch_categories() -> list:
    """Fetch all categories ordered by name (matches Flutter fetchCategories)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _url("categories_table"),
            params={"order": "name.asc"},
            headers=HEADERS,
        )
        resp.raise_for_status()
        return resp.json()


async def insert_category(
    name: str,
    parent_id: Optional[str] = None,
    image_url: Optional[str] = None,
    level: int = 0,
) -> dict:
    """Insert a new category/subcategory row in categories_table matching Flutter."""
    category_id = f"cat_{uuid.uuid4().hex[:8]}"
    payload = {
        "id": category_id,
        "name": name,
        "parent_id": parent_id,
        "image_url": image_url,
        "level": level,
        "item_count": 0,
    }
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(_url("categories_table"), json=payload, headers=headers)
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else payload


async def update_category(category_id: str, updates: dict) -> dict:
    """Update fields (like image_url, name) on a category in categories_table."""
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            _url("categories_table"),
            params={"id": f"eq.{category_id}"},
            json=updates,
            headers=headers,
        )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else updates
