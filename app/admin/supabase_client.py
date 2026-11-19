import uuid
from typing import Any, Optional
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


async def fetch_potential_suppliers() -> list[dict[str, Any]]:
    """
    Fetch users whose role is 'customer' with their business_table profile.
    Mirrors Flutter AdminProductService.fetchPotentialSuppliers().
    """
    params = {
        "role": "eq.customer",
        "select": "id,full_name,email,role,profile_pic_url,business_table(*)",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url("users_table"), params=params, headers=HEADERS)
        resp.raise_for_status()
        rows = resp.json()

    results = []
    for item in rows:
        biz_data = item.get("business_table") or {}
        if isinstance(biz_data, list):
            biz_data = biz_data[0] if biz_data else {}

        results.append({
            "id": str(item.get("id")),
            "name": item.get("full_name") or "",
            "email": item.get("email"),
            "role": item.get("role") or "customer",
            "profile_pic": item.get("profile_pic_url"),
            "legal_name": biz_data.get("legal_name"),
            "phone": biz_data.get("phone_number"),
            "address": biz_data.get("physical_address"),
            "latitude": biz_data.get("latitude"),
            "longitude": biz_data.get("longitude"),
            "industry_group": biz_data.get("industry_group"),
            "logo_url": biz_data.get("logo_url"),
        })
    return results


async def set_user_role(user_id: str, new_role: str) -> dict[str, Any]:
    """Update a user's role in users_table (e.g. promote to 'supplier' or revoke to 'customer')."""
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            _url("users_table"),
            params={"id": f"eq.{user_id}"},
            json={"role": new_role},
            headers=headers,
        )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else {"id": user_id, "role": new_role}


async def insert_category(
    name: str,
    parent_id: Optional[str] = None,
    image_url: Optional[str] = None,
    level: int = 0,
) -> dict[str, Any]:
    """Insert a new category row in categories_table."""
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


async def fetch_users(
    role: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List registered users with optional role filtering."""
    params: dict[str, Any] = {
        "select": "id,full_name,email,role,profile_pic_url,created_at",
        "order": "created_at.desc",
        "limit": limit,
        "offset": offset,
    }
    if role:
        params["role"] = f"eq.{role}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url("users_table"), params=params, headers=HEADERS)
        resp.raise_for_status()
        return resp.json()
