"""
Supabase REST client for orders.
Operates on the `supplier_orders` table via httpx.
"""
from datetime import datetime, timezone
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

TABLE = "supplier_orders"


def _url(table: str = TABLE) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


# ── Create / Upsert ──────────────────────────────────────────────

async def upsert_order(data: dict[str, Any]) -> dict:
    """
    Upsert an order row into supplier_orders on `order_id`.
    Returns the upserted row as a dict.
    """
    headers = {
        **HEADERS,
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _url(TABLE),
            json=data,
            headers=headers,
            params={"on_conflict": "order_id"},
        )
        resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else data


# ── Read (list & single) ─────────────────────────────────────────

async def fetch_orders_for_user(
    user_id: str,
    *,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """
    Paginated orders where user_id = current_user, ordered by created_at desc.
    Returns {"orders": list[dict], "total": int}.
    """
    offset = (page - 1) * limit
    headers = {**HEADERS, "Prefer": "count=exact"}
    params: dict[str, Any] = {
        "user_id": f"eq.{user_id}",
        "order": "created_at.desc",
        "limit": limit,
        "offset": offset,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(TABLE), params=params, headers=headers)
        resp.raise_for_status()
    rows = resp.json()
    total = int(resp.headers.get("content-range", "0/0").split("/")[-1] or 0)
    return {"orders": rows, "total": total}


async def fetch_order_by_id(order_id: str, user_id: str) -> Optional[dict]:
    """
    Fetch a single order where order_id = param AND (user_id = current_user OR supplier_id = current_user).
    Returns None if not found or unauthorized.
    """
    params = {
        "order_id": f"eq.{order_id}",
        "or": f"(user_id.eq.{user_id},supplier_id.eq.{user_id})",
        "limit": 1,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(TABLE), params=params, headers=HEADERS)
        resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None


# ── Supplier incoming ────────────────────────────────────────────

async def fetch_supplier_incoming(
    supplier_id: str,
    *,
    page: int = 1,
    limit: int = 20,
    status_filter: Optional[str] = None,
) -> dict:
    """
    Orders where supplier_id = current_user (incoming orders for supplier).
    Returns {"orders": list[dict], "total": int}.
    """
    offset = (page - 1) * limit
    headers = {**HEADERS, "Prefer": "count=exact"}
    params: dict[str, Any] = {
        "supplier_id": f"eq.{supplier_id}",
        "order": "created_at.desc",
        "limit": limit,
        "offset": offset,
    }
    if status_filter:
        params["status"] = f"eq.{status_filter}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(TABLE), params=params, headers=headers)
        resp.raise_for_status()
    rows = resp.json()
    total = int(resp.headers.get("content-range", "0/0").split("/")[-1] or 0)
    return {"orders": rows, "total": total}


# ── Update status ────────────────────────────────────────────────

async def update_order_status(
    order_id: str,
    user_id: str,
    new_status: str,
) -> Optional[dict]:
    """
    Update order status where order_id = param AND (user_id = me OR supplier_id = me).
    Returns the updated row dict or None.
    """
    headers = {**HEADERS, "Prefer": "return=representation"}
    params = {
        "order_id": f"eq.{order_id}",
        "or": f"(user_id.eq.{user_id},supplier_id.eq.{user_id})",
    }
    body = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.patch(_url(TABLE), json=body, params=params, headers=headers)
        resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None


# ── Delete / Cancel ──────────────────────────────────────────────

async def delete_order(order_id: str, user_id: str) -> bool:
    """
    Delete an order where order_id = param AND user_id = current_user.
    Returns True if deleted, False if no matching record.
    """
    headers = {**HEADERS, "Prefer": "return=representation"}
    params = {
        "order_id": f"eq.{order_id}",
        "user_id": f"eq.{user_id}",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.delete(_url(TABLE), params=params, headers=headers)
        resp.raise_for_status()
    rows = resp.json()
    return len(rows) > 0


# ── Drafts ───────────────────────────────────────────────────────

async def fetch_drafts_for_user(user_id: str) -> list[dict]:
    """
    Fetch all draft orders for a user where user_id = me AND status = 'draft'.
    """
    params = {
        "user_id": f"eq.{user_id}",
        "status": "eq.draft",
        "order": "created_at.desc",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_url(TABLE), params=params, headers=HEADERS)
        resp.raise_for_status()
    return resp.json()


async def delete_draft_for_user(draft_id: str, user_id: str) -> bool:
    """
    Delete draft where user_id = me, status = 'draft', and (order_id = draft_id OR id = draft_id).
    Returns True if deleted, False otherwise.
    """
    headers = {**HEADERS, "Prefer": "return=representation"}
    params = {
        "user_id": f"eq.{user_id}",
        "status": "eq.draft",
        "or": f"(order_id.eq.{draft_id},id.eq.{draft_id})",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.delete(_url(TABLE), params=params, headers=headers)
        resp.raise_for_status()
    rows = resp.json()
    return len(rows) > 0
