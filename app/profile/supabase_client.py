"""
Supabase REST client for profile & business data with unified ID resolution.
"""
import json
import logging
from typing import Any, Optional

import httpx

from app.core.config import supabase_url, supabase_anon_key

logger = logging.getLogger(__name__)

SUPABASE_URL = supabase_url()
SUPABASE_KEY = supabase_anon_key()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

VALID_BUSINESS_COLUMNS = {
    "legal_name",
    "phone_number",
    "physical_address",
    "city",
    "region",
    "latitude",
    "longitude",
    "industry_group",
    "logo_url",
}


def _url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


# ---- users_table helpers ----


async def ensure_user_exists(
    user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
) -> dict:
    """
    Ensure a user row exists in Supabase users_table.
    Resolves by user_id first, then by email (handles ID mismatch between auth providers).
    Auto-creates customer record if not found.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Lookup by ID
        resp = await client.get(
            _url("users_table"),
            params={"id": f"eq.{user_id}", "limit": "1"},
            headers=HEADERS,
        )
        if resp.status_code == 200:
            rows = resp.json()
            if rows:
                return rows[0]

        # 2. Lookup by email fallback
        if email:
            resp_email = await client.get(
                _url("users_table"),
                params={"email": f"eq.{email.strip().lower()}", "limit": "1"},
                headers=HEADERS,
            )
            if resp_email.status_code == 200:
                rows_email = resp_email.json()
                if rows_email:
                    return rows_email[0]

        # 3. Create missing user row in Supabase users_table
        clean_email = (email or f"user_{user_id[:8]}@example.com").strip().lower()
        clean_name = (full_name or clean_email.split("@")[0]).strip()
        payload = {
            "id": user_id,
            "email": clean_email,
            "full_name": clean_name,
            "role": "customer",
        }
        upsert_headers = {
            **HEADERS,
            "Prefer": "resolution=merge-duplicates,return=representation",
        }
        create_resp = await client.post(
            f"{_url('users_table')}?on_conflict=id",
            json=payload,
            headers=upsert_headers,
        )
        if create_resp.status_code in (200, 201):
            rows_created = create_resp.json()
            if rows_created:
                return rows_created[0]

        return payload


async def fetch_user(user_id: str, email: Optional[str] = None) -> Optional[dict]:
    """Fetch user row by id or email with auto-provisioning."""
    try:
        return await ensure_user_exists(user_id, email=email)
    except Exception as exc:
        logger.warning(f"Error fetching/ensuring user in Supabase: {exc}")
        return {
            "id": user_id,
            "email": email or "",
            "full_name": "",
            "role": "customer",
        }


async def upsert_user(user_id: str, data: dict, email: Optional[str] = None) -> dict:
    """Upsert user fields (full_name, profile_pic_url, etc.)."""
    user = await ensure_user_exists(user_id, email=email)
    resolved_id = user["id"]
    payload = {**data, "id": resolved_id}

    upsert_headers = {
        **HEADERS,
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{_url('users_table')}?on_conflict=id",
            json=payload,
            headers=upsert_headers,
        )
        resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else payload


async def update_user_role(user_id: str, new_role: str, email: Optional[str] = None) -> dict:
    """Update role in users_table (e.g. promote to 'supplier')."""
    user = await ensure_user_exists(user_id, email=email)
    resolved_id = user["id"]

    patch_headers = {
        **HEADERS,
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.patch(
            _url("users_table"),
            params={"id": f"eq.{resolved_id}"},
            json={"role": new_role},
            headers=patch_headers,
        )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else {**user, "role": new_role}


# ---- business_table helpers ----


async def fetch_business(user_id: str, email: Optional[str] = None) -> Optional[dict]:
    """Fetch business profile for a user using resolved Supabase user_id."""
    user = await ensure_user_exists(user_id, email=email)
    resolved_id = user["id"]

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            _url("business_table"),
            params={"user_id": f"eq.{resolved_id}", "limit": "1"},
            headers=HEADERS,
        )
        if resp.status_code == 200:
            rows = resp.json()
            return rows[0] if rows else None
        return None


async def upsert_business(user_id: str, data: dict, email: Optional[str] = None) -> dict:
    """
    Upsert business profile for a user with verified foreign key constraint
    and safe column sanitization.
    """
    user = await ensure_user_exists(user_id, email=email)
    resolved_id = user["id"]

    # Filter to only existing business_table columns to prevent 400 Bad Request
    clean_data = {k: v for k, v in data.items() if k in VALID_BUSINESS_COLUMNS}
    payload = {**clean_data, "user_id": resolved_id}

    upsert_headers = {
        **HEADERS,
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{_url('business_table')}?on_conflict=user_id",
            json=payload,
            headers=upsert_headers,
        )
        if resp.is_error:
            logger.error(f"Supabase upsert_business error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else payload


# ---- trading terms (JSONB column on users_table) ----


async def update_trading_terms(user_id: str, terms: Any, email: Optional[str] = None) -> dict:
    """Store trading terms as JSONB in users_table.trading_terms column."""
    user = await ensure_user_exists(user_id, email=email)
    resolved_id = user["id"]
    trading_json = terms if isinstance(terms, str) else json.dumps(terms)
    patch_headers = {
        **HEADERS,
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.patch(
            _url("users_table"),
            params={"id": f"eq.{resolved_id}"},
            json={"trading_terms": json.loads(trading_json)},
            headers=patch_headers,
        )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else {}
