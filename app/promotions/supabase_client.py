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


def _url(table: str = "promotions_table") -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


async def fetch_active_promotions() -> list[dict[str, Any]]:
    params = {
        "is_active": "eq.true",
        "order": "priority.desc",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(), params=params, headers=HEADERS)
        resp.raise_for_status()
        return resp.json()


async def fetch_promotion_by_id(promo_id: str) -> Optional[dict[str, Any]]:
    params = {
        "id": f"eq.{promo_id}",
        "limit": 1,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(), params=params, headers=HEADERS)
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else None
