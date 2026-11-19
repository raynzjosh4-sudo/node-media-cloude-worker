import httpx
from typing import Any, Optional
from app.core.config import supabase_url, supabase_anon_key

SUPABASE_URL = supabase_url()
SUPABASE_KEY = supabase_anon_key()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _url(table: str = "saved_items") -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


async def get_user_saved_items(user_id: str) -> list[dict[str, Any]]:
    params = {
        "user_id": f"eq.{user_id}",
        "order": "created_at.desc",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(), params=params, headers=HEADERS)
        resp.raise_for_status()
        return resp.json()


async def upsert_saved_item(
    user_id: str,
    product_id: str,
    quantity: int = 1,
    selected_color: Optional[str] = None,
    selected_size: Optional[str] = None,
    product_snapshot: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    payload = {
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity,
        "selected_color": selected_color,
        "selected_size": selected_size,
        "product_snapshot": product_snapshot or {},
    }
    headers = {
        **HEADERS,
        "Prefer": "return=representation,resolution=merge-duplicates",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(_url(), json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else payload


async def delete_saved_item(saved_item_id: str, user_id: str) -> bool:
    params = {
        "id": f"eq.{saved_item_id}",
        "user_id": f"eq.{user_id}",
    }
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.delete(_url(), params=params, headers=headers)
        resp.raise_for_status()
        return len(resp.json()) > 0


async def check_item_saved(user_id: str, product_id: str) -> tuple[bool, Optional[str]]:
    params = {
        "user_id": f"eq.{user_id}",
        "product_id": f"eq.{product_id}",
        "select": "id",
        "limit": 1,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(), params=params, headers=HEADERS)
        resp.raise_for_status()
        rows = resp.json()
        if rows:
            return True, rows[0]["id"]
        return False, None
