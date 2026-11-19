"""
Supabase client operations for products catalog and mutations.
"""
import json
from typing import Optional
import httpx
from app.core.config import supabase_url, supabase_anon_key, supabase_admin_config

SUPABASE_URL = supabase_url()
SUPABASE_KEY = supabase_anon_key()
_, SUPABASE_ADMIN_KEY = supabase_admin_config()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

WRITE_HEADERS = {
    "apikey": SUPABASE_ADMIN_KEY,
    "Authorization": f"Bearer {SUPABASE_ADMIN_KEY}",
    "Content-Type": "application/json",
}


def _url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


async def fetch_products(
    *,
    supplier_id: Optional[str] = None,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    ascending: bool = False,
) -> dict:
    """Fetch paginated lightweight product list."""
    offset = (page - 1) * limit

    params: dict = {
        "select": "id,name,sku,brand,srp,image_url,created_at,supplier_id",
        "order": f"{sort_by}.{'asc' if ascending else 'desc'}",
        "limit": limit,
        "offset": offset,
    }

    if supplier_id:
        params["supplier_id"] = f"eq.{supplier_id}"

    if category_id:
        params["category_id"] = f"eq.{category_id}"

    if search:
        params["or"] = f"(name.ilike.*{search}*,sku.ilike.*{search}*)"

    headers = {**HEADERS, "Prefer": "count=exact"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(_url("products_table"), params=params, headers=headers)
        resp.raise_for_status()

    products: list = resp.json()
    total_count = int(resp.headers.get("content-range", "0/0").split("/")[-1] or 0)

    if not products:
        return {"products": [], "total": total_count}

    # Fetch supplier names
    supplier_ids = list({p["supplier_id"] for p in products if p.get("supplier_id")})
    supplier_names: dict[str, str] = {}

    if supplier_ids:
        async with httpx.AsyncClient() as client:
            sr = await client.get(
                _url("users_table"),
                params={"select": "id,full_name", "id": f"in.({','.join(supplier_ids)})"},
                headers=HEADERS,
            )
            if sr.status_code == 200:
                for row in sr.json():
                    if row.get("id") and row.get("full_name"):
                        supplier_names[row["id"]] = row["full_name"]

    for p in products:
        p["supplier_name"] = supplier_names.get(p.get("supplier_id", ""), None)

    return {"products": products, "total": total_count}


async def fetch_product_by_id(product_id: str) -> Optional[dict]:
    """Fetch full product detail by UUID."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _url("products_table"),
            params={"id": f"eq.{product_id}", "limit": 1},
            headers=HEADERS,
        )
        resp.raise_for_status()
        rows = resp.json()

    if not rows:
        return None

    product = rows[0]
    supplier_id = product.get("supplier_id")
    if supplier_id:
        async with httpx.AsyncClient() as client:
            sr = await client.get(
                _url("users_table"),
                params={
                    "select": "id,full_name,email,business:business_table(*)",
                    "id": f"eq.{supplier_id}",
                    "limit": 1,
                },
                headers=HEADERS,
            )
            if sr.status_code == 200 and sr.json():
                user_data = sr.json()[0]
                biz_list = user_data.get("business") or []
                biz = biz_list[0] if isinstance(biz_list, list) and biz_list else (biz_list if isinstance(biz_list, dict) else {})
                product["supplier"] = {
                    "id": user_data.get("id"),
                    "name": biz.get("legal_name") or user_data.get("full_name") or "N.O.D.E Supplier",
                    "imageUrl": biz.get("logo_url") or "",
                    "category": biz.get("industry_group") or "General",
                    "business": biz,
                }
    return product


async def fetch_product_by_slug(slug: str) -> Optional[dict]:
    """Fetch full product detail by slug."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _url("products_table"),
            params={"slug": f"eq.{slug}", "limit": 1},
            headers=HEADERS,
        )
        resp.raise_for_status()
        rows = resp.json()

    if not rows:
        return None

    product = rows[0]
    supplier_id = product.get("supplier_id")
    if supplier_id:
        async with httpx.AsyncClient() as client:
            sr = await client.get(
                _url("users_table"),
                params={
                    "select": "id,full_name,email,business:business_table(*)",
                    "id": f"eq.{supplier_id}",
                    "limit": 1,
                },
                headers=HEADERS,
            )
            if sr.status_code == 200 and sr.json():
                user_data = sr.json()[0]
                biz_list = user_data.get("business") or []
                biz = biz_list[0] if isinstance(biz_list, list) and biz_list else (biz_list if isinstance(biz_list, dict) else {})
                product["supplier"] = {
                    "id": user_data.get("id"),
                    "name": biz.get("legal_name") or user_data.get("full_name") or "N.O.D.E Supplier",
                    "imageUrl": biz.get("logo_url") or "",
                    "category": biz.get("industry_group") or "General",
                    "business": biz,
                }
    return product


async def fetch_suppliers() -> list:
    """Fetch all verified supplier users with their profile pics and business details."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _url("users_table"),
            params={
                "role": "eq.supplier",
                "select": "id,full_name,email,profile_pic_url,business:business_table(*)",
            },
            headers=HEADERS,
        )
        resp.raise_for_status()
        rows = resp.json()
        for u in rows:
            biz_list = u.get("business") or []
            biz = biz_list[0] if isinstance(biz_list, list) and biz_list else (biz_list if isinstance(biz_list, dict) else {})
            u["imageUrl"] = biz.get("logo_url") or u.get("profile_pic_url") or ""
        return rows


async def insert_product(product_data: dict) -> dict:
    """Insert a new product into products_table."""
    headers = {**WRITE_HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(_url("products_table"), json=product_data, headers=headers)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            raise RuntimeError("Supabase did not return the inserted product row.")
        return rows[0]


async def update_product(product_id: str, updates: dict) -> dict:
    """Update fields on an existing product in products_table."""
    headers = {**WRITE_HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            _url("products_table"),
            params={"id": f"eq.{product_id}"},
            json=updates,
            headers=headers,
        )
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            raise RuntimeError(
                f"Supabase did not return an updated row for product '{product_id}'."
            )
        return rows[0]


async def delete_product(product_id: str) -> bool:
    """Delete a product from products_table."""
    headers = {**WRITE_HEADERS, "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            _url("products_table"),
            params={"id": f"eq.{product_id}"},
            headers=headers,
        )
        resp.raise_for_status()
        return len(resp.json()) > 0


async def fetch_popular_products(
    *,
    category_id: Optional[str] = None,
    limit: int = 15,
    offset: int = 0,
) -> list[dict]:
    """Fetch popular / trending products for explore section."""
    params: dict = {
        "select": "*",
        "order": "created_at.desc",
        "limit": limit,
        "offset": offset,
    }
    if category_id:
        params["category_id"] = f"eq.{category_id}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(_url("products_table"), params=params, headers=HEADERS)
        resp.raise_for_status()
        rows: list = resp.json()

    if not rows:
        return []

    supplier_ids = list({r["supplier_id"] for r in rows if r.get("supplier_id")})
    if supplier_ids:
        async with httpx.AsyncClient() as client:
            sr = await client.get(
                _url("users_table"),
                params={
                    "select": "id,full_name,profile_pic_url,business:business_table(*)",
                    "id": f"in.({','.join(supplier_ids)})",
                },
                headers=HEADERS,
            )
            if sr.status_code == 200:
                user_map = {u["id"]: u for u in sr.json()}
                for r in rows:
                    sid = r.get("supplier_id")
                    if sid in user_map:
                        u = user_map[sid]
                        biz = u.get("business") or {}
                        if isinstance(biz, list):
                            biz = biz[0] if biz else {}
                        r["supplier"] = {
                            "id": sid,
                            "name": biz.get("legal_name") or u.get("full_name") or "N.O.D.E Supplier",
                            "imageUrl": biz.get("logo_url") or u.get("profile_pic_url") or "",
                            "business": biz,
                        }
    return rows
