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


def _url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


async def fetch_notifications(
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    category: Optional[str] = None,
) -> tuple[list[dict[str, Any]], int]:
    params: dict[str, Any] = {
        "user_id": f"eq.{user_id}",
        "order": "created_at.desc",
        "limit": limit,
        "offset": offset,
    }
    if category and category.lower() != "all":
        params["category"] = f"eq.{category.lower()}"

    headers = {**HEADERS, "Prefer": "count=exact"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url("notifications_table"), params=params, headers=headers)
        resp.raise_for_status()
        items = resp.json()

        total = 0
        content_range = resp.headers.get("content-range")
        if content_range and "/" in content_range:
            total_part = content_range.split("/")[-1]
            if total_part.isdigit():
                total = int(total_part)
            else:
                total = len(items)
        else:
            total = len(items)

        return items, total


async def mark_notification_read(notification_id: str, user_id: str) -> bool:
    params = {
        "id": f"eq.{notification_id}",
        "user_id": f"eq.{user_id}",
    }
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            _url("notifications_table"),
            params=params,
            json={"is_unread": False},
            headers=headers,
        )
        resp.raise_for_status()
        return len(resp.json()) > 0


async def mark_all_notifications_read(user_id: str) -> int:
    params = {
        "user_id": f"eq.{user_id}",
        "is_unread": "eq.true",
    }
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            _url("notifications_table"),
            params=params,
            json={"is_unread": False},
            headers=headers,
        )
        resp.raise_for_status()
        return len(resp.json())


async def delete_notification(notification_id: str, user_id: str) -> bool:
    params = {
        "id": f"eq.{notification_id}",
        "user_id": f"eq.{user_id}",
    }
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.delete(_url("notifications_table"), params=params, headers=headers)
        resp.raise_for_status()
        return len(resp.json()) > 0


async def register_device_token(user_id: str, token: str, device_type: str = "android") -> dict[str, Any]:
    payload = {
        "user_id": user_id,
        "token": token,
        "device_type": device_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    headers = {
        **HEADERS,
        "Prefer": "return=representation,resolution=merge-duplicates",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(_url("device_tokens"), json=payload, headers=headers)
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else payload


async def unregister_device_token(user_id: str, token: Optional[str] = None) -> bool:
    params: dict[str, Any] = {"user_id": f"eq.{user_id}"}
    if token:
        params["token"] = f"eq.{token}"
    headers = {**HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.delete(_url("device_tokens"), params=params, headers=headers)
        resp.raise_for_status()
        return len(resp.json()) > 0
