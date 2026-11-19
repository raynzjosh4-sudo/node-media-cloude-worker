import httpx
from datetime import datetime, timezone
from typing import Any, Optional
from app.core.config import supabase_url, supabase_anon_key

SUPABASE_URL = supabase_url()
SUPABASE_KEY = supabase_anon_key()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _url(table: str = "records") -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


async def fetch_user_records(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    is_archived: Optional[bool] = None,
) -> tuple[list[dict[str, Any]], int]:
    params: dict[str, Any] = {
        "user_id": f"eq.{user_id}",
        "order": "updated_at.desc",
        "limit": limit,
        "offset": offset,
    }
    if is_archived is not None:
        params["is_archived"] = f"eq.{str(is_archived).lower()}"

    headers = {**HEADERS, "Prefer": "count=exact"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(), params=params, headers=headers)
        resp.raise_for_status()
        records = resp.json()

        total = 0
        content_range = resp.headers.get("content-range")
        if content_range and "/" in content_range:
            total_part = content_range.split("/")[-1]
            if total_part.isdigit():
                total = int(total_part)
            else:
                total = len(records)
        else:
            total = len(records)

        return records, total


async def fetch_record_by_id(record_id: str, user_id: str) -> Optional[dict[str, Any]]:
    params = {
        "id": f"eq.{record_id}",
        "user_id": f"eq.{user_id}",
        "limit": 1,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(), params=params, headers=HEADERS)
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else None


async def upsert_record(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = {
        **payload,
        "user_id": user_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    headers = {
        **HEADERS,
        "Prefer": "return=representation,resolution=merge-duplicates",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(_url(), json=row, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else row


async def delete_record(record_id: str, user_id: str) -> bool:
    params = {
        "id": f"eq.{record_id}",
        "user_id": f"eq.{user_id}",
    }
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.delete(_url(), params=params, headers=headers)
        resp.raise_for_status()
        return len(resp.json()) > 0
